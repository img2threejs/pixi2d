# pixi2D — img2pixi2d

An independent OMP plugin for reference-guided, editable **PixiJS 2D scenes**: sprites, graphics, text, native 2D meshes and layered parallax. Includes image intake/crop/compare tools and ownership, occlusion-completion and motion-review guidance. **No 3D beta dependency.**

## Example code

The included [example factory](examples/showcase.ts) is an authored Graphics/Text scene at 960×640, **not** a reconstruction of a user image or evidence of image-to-scene fidelity. The balloon and clouds have independent motion; the scene adds no Application or ticker.

To reproduce it, copy `examples/showcase.ts` to your existing host's `src/plugin-showcase.ts`. After that host's Application is initialized:

```ts
import { createShowcase } from './plugin-showcase';
const showcase = createShowcase(app.stage); // Example design size: 960 x 640.
showcase.setTime(1.5); // Seconds; only the example-owned objects move.
showcase.reset();
// On unmount: showcase.dispose(); remove any host-owned ticker callback first.
```

For animated playback, have your **existing** ticker pass elapsed seconds to `setTime`; do not add a second render loop. This example uses vector primitives; it does not demonstrate source-image segmentation or native mesh deformation.

## Install

Requirements: OMP, Git/GitHub CLI, an existing PixiJS v8 host, and **Python 3.10+** for the image tools. Verified host release: **PixiJS 8.22.0**. Python is not needed to run an integrated scene.

This repository is **private**; your GitHub account needs read access. `package.json`'s `private: true` prevents npm publication, not public GitHub visibility. On macOS/Linux:

```sh
gh auth login --hostname github.com --git-protocol https
gh auth setup-git --hostname github.com
mkdir -p "$HOME/.local/share/img2threejs"
gh repo clone img2threejs/pixi2d "$HOME/.local/share/img2threejs/pixi2d"
PLUGIN="$HOME/.local/share/img2threejs/pixi2d"
omp plugin link "$PLUGIN"
omp plugin list --json
python3 -m venv "$PLUGIN/.venv"
"$PLUGIN/.venv/bin/python" -m pip install -r "$PLUGIN/skills/img2pixi2d/requirements.txt"
```

Already cloned elsewhere? Set `PLUGIN` to that absolute path and run `omp plugin link "$PLUGIN"`. Keep the clone: OMP links it by symlink. Do not run `npm install` in the plugin repository; Pixi dependencies belong to the host. **Start a new OMP session** to discover `img2pixi2d`.

## Recommended workflow

1. Start OMP **inside the existing host project**, attach the original image, and invoke `/skill:img2pixi2d`.
2. Name the objects that must be editable, required controls, target viewport and motion limits. Supply original layers/mattes/fonts when available.
3. Review the ownership and occlusion plan before animation. Preserve source pixels; authorize inferred hidden-region completion explicitly, or limit motion to supported poses.
4. Approve blockout/layout, then details/appearance, then interaction/motion. Reuse one admitted reference and the host preview; diagnose specific failures instead of restarting the scene.
5. Require actual canvas captures, critical-region comparisons, independent hide/move tests, motion extrema, reset and resource-safe teardown. Pixel similarity alone does not establish editability or animation quality.

For best results, give a bounded task and concrete defects. Use 2D meshes for continuous deformation and layered parallax for depth cues; neither requires the 3D plugin. The skill is an agent workflow, **not an automatic generator launched by installation**.

## Copy-ready prompts

Replace the bracketed inputs with real paths and requirements. Attach the referenced image; do not leave placeholders unresolved.

### Reconstruct an editable scene

```text
/skill:img2pixi2d
Use [reference image path] in this existing PixiJS project. Match its silhouette,
colors, text and layout at [viewport dimensions]. Make [object names] independently
editable. Required controls: [controls]. Allowed motion: [limits].
Preserve the original reference and unrelated code. Plan ownership, mattes,
occlusion and pivots before building. Do not invent hidden pixels; request my
approval if completion is needed. Use the existing Application and preview.
Deliver a subject-specific factory, reconstruction data and actual canvas evidence.
Verify critical details, hide/move isolation, full motion, reset and disposal.
```

### Improve an existing reconstruction without regenerating it

```text
/skill:img2pixi2d
Continue the existing scene against [same admitted reference path]. The defect is
[object/region and observed failure]. Preserve the accepted layout and other objects.
Fix only the diagnosed cause. Requested motion is [range]; completion permission
is [none or explicitly authorized regions]. Compare actual before/after captures,
exercise the affected object independently, and verify neutral-pose reset.
```

## Manual image tools

Use the same plugin Python environment. Run from the skill directory; replace the host/image paths:

```sh
PROJECT="/absolute/path/to/your-pixi-project"
IMAGE="/absolute/path/to/reference.png"
cd "$PLUGIN/skills/img2pixi2d"
"$PLUGIN/.venv/bin/python" -m forge.cli --help
"$PLUGIN/.venv/bin/python" -m forge.cli intake "$IMAGE" --workspace "$PROJECT/.img2pixi2d"
# Example only: choose X Y WIDTH HEIGHT inside a visible region of your image.
"$PLUGIN/.venv/bin/python" -m forge.cli crop \
  --workspace "$PROJECT/.img2pixi2d" --bbox 0 0 16 16 --out layers/observed-region.png
```

Intake preserves original bytes and an immutable sRGB RGBA working PNG. A crop must contain visible pixels; replace the example bbox for your image. Add `--mask masks/part.png` for a supplied/reviewed matte, relative to the workspace. Crop **does not segment or inpaint**. Restore trimmed placement using the crop metadata's `trimOffset`.

Capture the **actual host canvas** to the path below, at the working image's artboard dimensions, before comparing:

```sh
"$PLUGIN/.venv/bin/python" -m forge.cli compare \
  --reference "$PROJECT/.img2pixi2d/reference/working.png" \
  --render "$PROJECT/.img2pixi2d/evidence/render.png" --out "$PROJECT/.img2pixi2d/evidence"
```

Do not resize images to manufacture agreement. RGB/alpha/SSIM metrics are diagnostics; inspect critical crops and motion with vision. HTTPS reference admission requires explicit consent and `intake --allow-network`.

## Update, verify and troubleshoot

```sh
git -C "$PLUGIN" pull --ff-only
cd "$PLUGIN/skills/img2pixi2d"
"$PLUGIN/.venv/bin/python" tests/test_tools.py --image "$IMAGE" -v
```

- Reinstall requirements if they change; start a new OMP session after updates.
- **Clone denied:** request organization/repository access; do not put credentials in clone URLs.
- **Skill missing:** check `omp plugin list --json`, the linked clone and the new session.
- **Empty crop:** choose a visible region and the correct matte; alpha-preserving crop is not segmentation.
- `omp plugin uninstall pixi2d` removes registration, not host artwork.

## Scope and further reading

[Skill workflow](skills/img2pixi2d/SKILL.md) · [Reconstruction](skills/img2pixi2d/references/reconstruction.md) · [PixiJS integration](skills/img2pixi2d/references/pixijs.md) · [Object separation](skills/img2pixi2d/references/object-separation.md) · [Occlusion completion](skills/img2pixi2d/references/occlusion-completion.md) · [Review](skills/img2pixi2d/references/review.md).

The host owns Application, renderer, ticker and shared resources; factories own only their nodes/listeners. A flattened image cannot reveal exact hidden artwork. Label inferred mattes/completion honestly. Real Mesh3D/Sprite3D/Model3D belongs to [pixi3d](https://github.com/img2threejs/pixi3d).

Do not upload user artwork, host workspaces, credentials, apps or dependency builds. The included example is authored code, not redistributed reference artwork. Repository access does not grant artwork redistribution rights.
