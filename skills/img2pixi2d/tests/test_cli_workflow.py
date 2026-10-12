"""Exercise the README's manual workflow through real CLI subprocesses.

From the repository root, after installing the declared Pillow requirement:
    .venv/bin/python -m unittest discover -s skills/img2pixi2d/tests -p test_cli_workflow.py -v

Fixtures are authored locally; no user artwork, host app or network is needed.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SKILL = Path(__file__).resolve().parents[1]


class ManualWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pixi2d workflow ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / 'host project' / '.img2pixi2d'
        self.source = self.root / 'reference image.png'
        self.pixels = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
        self.addCleanup(self.pixels.close)
        self.pixels.paste((40, 120, 200, 255), (3, 4, 11, 13))
        self.pixels.putpixel((6, 7), (220, 60, 30, 128))
        self.pixels.save(self.source)

    def cli(self, *arguments, code=0):
        result = subprocess.run(
            [sys.executable, '-m', 'forge.cli', *map(str, arguments)],
            cwd=SKILL, capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def admit(self):
        result = self.cli('intake', self.source, '--workspace', self.workspace)
        self.assertEqual(result['status'], 'proceed', result)
        return result

    def test_intake_crop_and_compare_preserve_pixels_and_layer_placement(self):
        source_bytes = self.source.read_bytes()
        admission = self.admit()
        self.assertEqual(
            (self.workspace / admission['reference']['originalSrc']).read_bytes(),
            source_bytes,
        )
        reference = self.workspace / 'reference/working.png'
        reference_bytes = reference.read_bytes()
        with Image.open(reference) as working:
            self.assertEqual(working.mode, 'RGBA')
            self.assertEqual(working.size, self.pixels.size)
            self.assertEqual(working.tobytes(), self.pixels.tobytes())

        asset = self.cli(
            'crop', '--workspace', self.workspace, '--bbox', 0, 0, 16, 16,
            '--out', 'layers/observed-region.png',
        )
        self.assertEqual(asset['trimOffset'], [3, 4])
        layer_path = self.workspace / asset['src']
        metadata = json.loads(layer_path.with_suffix('.meta.json').read_text())
        restored = Image.new('RGBA', self.pixels.size)
        self.addCleanup(restored.close)
        with Image.open(layer_path) as layer:
            self.assertEqual(layer.size, (8, 9))
            # No paste mask: source alpha must be preserved, not multiplied twice.
            restored.paste(layer, tuple(metadata['trimOffset']))
        self.assertEqual(restored.tobytes(), self.pixels.tobytes())

        render = self.workspace / 'evidence/render.png'
        render.parent.mkdir()
        restored.save(render)
        report = self.cli(
            'compare', '--reference', reference, '--render', render,
            '--out', render.parent,
        )
        self.assertEqual(report['metrics']['meanRGBErrorWhite'], 0)
        self.assertEqual(report['metrics']['meanRGBErrorBlack'], 0)
        self.assertEqual(report['metrics']['meanAlphaError'], 0)
        self.assertEqual(report['metrics']['globalLumaSSIM'], 1)
        with Image.open(report['comparison']) as sheet:
            self.assertEqual(sheet.size, (48, 16))
            with sheet.crop((32, 0, 48, 16)) as difference:
                self.assertEqual(difference.tobytes(), bytes(16 * 16 * 3))
        self.assertEqual(reference.read_bytes(), reference_bytes)
        self.assertEqual(self.source.read_bytes(), source_bytes)

    def test_reviewed_matte_preserves_rgb_and_multiplies_source_alpha(self):
        self.admit()
        mask = self.workspace / 'masks/part.png'
        mask.parent.mkdir()
        with Image.new('L', self.pixels.size, 128) as matte:
            matte.save(mask)
        asset = self.cli(
            'crop', '--workspace', self.workspace, '--bbox', 0, 0, 16, 16,
            '--mask', 'masks/part.png', '--out', 'layers/matted.png',
        )
        with Image.open(self.workspace / asset['src']) as layer:
            self.assertEqual(layer.size, (8, 9))
            self.assertEqual(layer.getpixel((0, 0)), (40, 120, 200, 128))
            self.assertEqual(layer.getpixel((3, 3)), (220, 60, 30, 64))

    def test_empty_crop_fails_without_publishing_layer_or_provenance(self):
        self.admit()
        result = self.cli(
            'crop', '--workspace', self.workspace, '--bbox', 0, 0, 2, 2,
            '--out', 'layers/empty.png', code=2,
        )
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['issues'][0]['code'], 'empty-layer')
        self.assertFalse((self.workspace / 'layers/empty.png').exists())
        self.assertFalse((self.workspace / 'layers/empty.meta.json').exists())

    def test_compare_rejects_different_artboards_instead_of_resizing(self):
        self.admit()
        render = self.root / 'wrong-frame.png'
        with Image.new('RGBA', (17, 16), (40, 120, 200, 255)) as image:
            image.save(render)
        evidence = self.workspace / 'evidence'
        result = self.cli(
            'compare', '--reference', self.workspace / 'reference/working.png',
            '--render', render, '--out', evidence, code=2,
        )
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['issues'][0]['code'], 'framing-mismatch')
        self.assertFalse(evidence.exists())

    def test_https_reference_requires_explicit_network_consent(self):
        # .invalid cannot supply a real image; denial must precede fetching it.
        result = self.cli(
            'intake', 'https://reference.invalid/artwork.png',
            '--workspace', self.workspace, code=3,
        )
        self.assertEqual(result['status'], 'request-input')
        self.assertEqual(result['issues'][0]['code'], 'network-consent-required')
        self.assertFalse(self.workspace.exists())

    def test_compare_measures_visible_color_error_in_metrics_and_evidence(self):
        self.admit()
        render = self.root / 'changed-render.png'
        changed = self.pixels.copy()
        self.addCleanup(changed.close)
        changed.putpixel((3, 4), (255, 255, 255, 255))
        changed.save(render)
        report = self.cli(
            'compare', '--reference', self.workspace / 'reference/working.png',
            '--render', render, '--out', self.workspace / 'evidence',
        )
        expected_error = (215 + 135 + 55) / (16 * 16 * 3 * 255)
        self.assertAlmostEqual(report['metrics']['meanRGBErrorWhite'], expected_error)
        self.assertAlmostEqual(report['metrics']['meanRGBErrorBlack'], expected_error)
        self.assertEqual(report['metrics']['meanAlphaError'], 0)
        self.assertLess(report['metrics']['globalLumaSSIM'], 1)
        with Image.open(report['comparison']) as sheet:
            self.assertEqual(sheet.getpixel((32 + 3, 4)), (215, 135, 55))


if __name__ == '__main__':
    unittest.main()
