"""Consumer-visible image-tool boundaries, all derived from one supplied image."""
import argparse
import json
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path
from PIL import Image, ImageChops, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from forge.common import ToolError, hash_file
from forge.intake import intake_reference, _socket_deadline
from forge.crop import crop_reference
from forge.compare import compare_images

IMAGE = None


class OneImageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / 'work'
        self.original_bytes = IMAGE.read_bytes()
        self.admission = intake_reference(str(IMAGE), self.workspace)
        self.assertEqual(self.admission['status'], 'proceed', self.admission)
        self.reference = self.workspace / 'reference/working.png'
        with Image.open(self.reference) as image:
            self.pixels = image.convert('RGBA')
        self.bbox = [0, 0, self.pixels.width, self.pixels.height]
        self.assertIsNotNone(self.pixels.getchannel('A').getbbox(), 'Test input must contain a visible subject')

    def test_resume_preserves_artifacts_and_rejects_redirected_cached_reference(self):
        artifacts = [self.reference, self.workspace / self.admission['reference']['originalSrc'], self.workspace / 'intake.json']
        before = [(path.read_bytes(), path.stat().st_mtime_ns) for path in artifacts]
        repeated = intake_reference(str(IMAGE), self.workspace)
        self.assertEqual(repeated['status'], 'proceed', repeated)
        self.assertEqual([(path.read_bytes(), path.stat().st_mtime_ns) for path in artifacts], before)
        forged = json.loads((self.workspace / 'intake.json').read_text())
        forged['reference']['src'] = str(IMAGE)
        (self.workspace / 'intake.json').write_text(json.dumps(forged))
        denied = intake_reference(str(IMAGE), self.workspace)
        self.assertEqual(denied['status'], 'request-input', denied)
        self.assertEqual(self.reference.read_bytes(), before[0][0])

    def test_unpaired_intake_record_is_not_overwritten_by_new_admission(self):
        workspace = self.root / 'unpaired'
        workspace.mkdir()
        record = workspace / 'intake.json'
        record.write_text('{"unrelated":"preserved history"}')
        before = (record.read_bytes(), record.stat().st_mtime_ns)
        result = intake_reference(str(IMAGE), workspace)
        self.assertEqual(result['status'], 'request-input', result)
        self.assertEqual((record.read_bytes(), record.stat().st_mtime_ns), before)
        self.assertFalse((workspace / 'reference').exists())

    def test_trimmed_layer_reconstructs_visible_reference_at_its_logical_offset(self):
        asset = crop_reference(self.workspace, self.bbox, 'layers/subject.png')
        with Image.open(self.workspace / asset['src']) as image:
            layer = image.convert('RGBA')
        restored = Image.new('RGBA', self.pixels.size)
        restored.paste(layer, tuple(asset['trimOffset']))
        self.assertIsNone(ImageChops.difference(self.pixels.getchannel('A'), restored.getchannel('A')).getbbox())
        visible = self.pixels.getchannel('A').point(lambda value: 255 if value else 0)
        difference = ImageChops.difference(self.pixels.convert('RGB'), restored.convert('RGB'))
        self.assertIsNone(Image.composite(difference, Image.new('RGB', self.pixels.size), visible).getbbox())
        self.assertEqual((asset['originalWidth'], asset['originalHeight']), self.pixels.size)
        self.assertEqual(IMAGE.read_bytes(), self.original_bytes)

    def test_full_reference_matte_multiplies_alpha_without_changing_rgb(self):
        Image.new('L', self.pixels.size, 128).save(self.workspace / 'matte.png')
        asset = crop_reference(self.workspace, self.bbox, 'layers/matted.png', mask='matte.png')
        with Image.open(self.workspace / asset['src']) as image:
            layer = image.convert('RGBA')
        ox, oy = asset['trimOffset']
        for x, y in [(layer.width // 2, layer.height // 2), (0, 0), (layer.width - 1, layer.height - 1)]:
            expected = self.pixels.getpixel((x + ox, y + oy))
            actual = layer.getpixel((x, y))
            self.assertEqual(actual, (*expected[:3], expected[3] * 128 // 255))
        Image.new('L', (self.pixels.width + 1, self.pixels.height), 128).save(self.workspace / 'wrong-matte.png')
        with self.assertRaises(ToolError):
            crop_reference(self.workspace, self.bbox, 'layers/rejected.png', mask='wrong-matte.png')
        self.assertFalse((self.workspace / 'layers/rejected.png').exists())

    def test_conflicting_provenance_cannot_publish_an_orphan_png(self):
        target = self.workspace / 'layers/subject.png'
        target.parent.mkdir()
        sidecar = target.with_suffix('.meta.json')
        sidecar.write_text('{"unrelated":"user data"}')
        before = sidecar.read_bytes()
        with self.assertRaises(ToolError):
            crop_reference(self.workspace, self.bbox, 'layers/subject.png')
        self.assertFalse(target.exists())
        self.assertEqual(sidecar.read_bytes(), before)

    def test_existing_layer_and_reference_cannot_be_overwritten(self):
        asset = crop_reference(self.workspace, self.bbox, 'layers/subject.png')
        target = self.workspace / asset['src']
        target.write_bytes(b'Unrelated user work')
        with self.assertRaises(ToolError):
            crop_reference(self.workspace, self.bbox, 'layers/subject.png')
        self.assertEqual(target.read_bytes(), b'Unrelated user work')
        digest = hash_file(self.reference)
        with self.assertRaises(ToolError):
            crop_reference(self.workspace, self.bbox, 'reference/working.png')
        self.assertEqual(hash_file(self.reference), digest)
        self.reference.write_bytes(b'Changed working reference')
        with self.assertRaises(ToolError):
            crop_reference(self.workspace, self.bbox, 'layers/stale.png')
        self.assertFalse((self.workspace / 'layers/stale.png').exists())

    def corrupted(self):
        rgb = ImageOps.invert(self.pixels.convert('RGB')).convert('RGBA')
        rgb.putalpha(self.pixels.getchannel('A'))
        path = self.root / 'color-corruption.png'
        rgb.save(path)
        return path

    def test_wrong_pixels_are_measured_and_repeat_does_not_rewrite_evidence(self):
        corrupted = self.corrupted()
        out = self.root / 'evidence'
        report = compare_images(self.reference, corrupted, out)
        self.assertGreater(report['metrics']['meanRGBErrorWhite'], 0)
        self.assertLess(report['metrics']['globalLumaSSIM'], 1)
        before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in out.iterdir()}
        compare_images(self.reference, corrupted, out)
        self.assertEqual({path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in out.iterdir()}, before)

    def test_frame_and_region_errors_cannot_be_hidden_by_resizing(self):
        small = self.root / 'wrong-frame.png'
        self.pixels.resize((self.pixels.width + 1, self.pixels.height)).save(small)
        out = self.root / 'evidence'
        with self.assertRaises(ToolError): compare_images(self.reference, small, out)
        self.assertFalse(out.exists())
        with self.assertRaises(ToolError): compare_images(self.reference, self.reference, out, bbox=[-1, 0, 20, 20])
        self.assertFalse(out.exists())
        with self.assertRaises(ToolError): compare_images(self.reference, self.reference, out, bbox=[0.5, 0, 1, 1])
        self.assertFalse(out.exists())

    def test_invisible_rgb_cannot_be_reported_as_visible_color_error(self):
        first, second = self.pixels.copy(), ImageOps.invert(self.pixels.convert('RGB')).convert('RGBA')
        first.putalpha(0)
        second.putalpha(0)
        a, b = self.root / 'invisible-a.png', self.root / 'invisible-b.png'
        first.save(a)
        second.save(b)
        metrics = compare_images(a, b, self.root / 'evidence')['metrics']
        self.assertEqual((metrics['meanRGBErrorWhite'], metrics['meanRGBErrorBlack'], metrics['meanAlphaError']), (0, 0, 0))

    def test_network_requires_consent_and_socket_deadline_interrupts_real_io(self):
        denied = intake_reference('https://example.com/reference.png', self.root / 'network')
        self.assertEqual(denied['status'], 'request-input', denied)
        first, second = socket.socketpair()
        first.settimeout(2)
        started = time.monotonic()
        timer = _socket_deadline(first, started + 0.1)
        try:
            try: received = first.recv(1)
            except OSError: received = b''
            self.assertEqual(received, b'')
            self.assertLess(time.monotonic() - started, 1)
        finally:
            timer.cancel()
            timer.join()
            first.close()
            second.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=Path, required=True)
    args, remaining = parser.parse_known_args()
    IMAGE = args.image.expanduser().resolve()
    if not IMAGE.is_file(): parser.error('--image must name one readable input image')
    program = unittest.main(argv=[sys.argv[0], *remaining], exit=False)
    sys.exit(0 if program.result.wasSuccessful() else 1)
