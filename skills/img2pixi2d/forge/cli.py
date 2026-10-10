"""Local img2pixi2d image tools; no application, fake vision scoring, or 3D runtime."""
import argparse
import json
import sys
from pathlib import Path
from PIL import Image
from forge.common import ToolError


def main(argv=None):
    parser = argparse.ArgumentParser(prog='img2pixi2d')
    commands = parser.add_subparsers(dest='command', required=True)
    intake = commands.add_parser('intake', help='Admit an immutable image reference')
    intake.add_argument('source')
    intake.add_argument('--workspace', type=Path, required=True)
    intake.add_argument('--allow-network', action='store_true')
    crop = commands.add_parser('crop', help='Extract a declared crop and supplied matte, preserving alpha')
    crop.add_argument('--workspace', type=Path, required=True)
    crop.add_argument('--bbox', type=int, nargs=4, metavar=('X', 'Y', 'W', 'H'), required=True)
    crop.add_argument('--out', required=True, help='Workspace-relative derived PNG path')
    crop.add_argument('--mask', help='Workspace-relative supplied or reviewed inferred matte; crop does not segment')
    compare = commands.add_parser('compare', help='Compare actual equal-sized PNGs without assigning vision scores')
    compare.add_argument('--reference', type=Path, required=True)
    compare.add_argument('--render', type=Path, required=True)
    compare.add_argument('--out', type=Path, required=True)
    compare.add_argument('--bbox', type=int, nargs=4, metavar=('X', 'Y', 'W', 'H'))
    args = parser.parse_args(argv)
    try:
        if args.command == 'intake':
            from forge.intake import intake_reference
            result = intake_reference(args.source, args.workspace, allow_network=args.allow_network)
        elif args.command == 'crop':
            from forge.crop import crop_reference
            result = crop_reference(args.workspace, args.bbox, args.out, mask=args.mask)
        else:
            from forge.compare import compare_images
            result = compare_images(args.reference, args.render, args.out, bbox=args.bbox)
        status = result['status']
        code = 3 if status == 'request-input' else 2 if status in ('rejected', 'unsupported', 'error') else 0
    except ToolError as error:
        result, code = {'status': 'error', 'issues': [error.as_dict()]}, 2
    except (OSError, ValueError, KeyError, Image.DecompressionBombError) as error:
        result, code = {'status': 'error', 'issues': [{'code': 'invalid-input', 'message': str(error)}]}, 2
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return code


if __name__ == '__main__': sys.exit(main())