# Intake — one actual reference image

Use the single image the user supplied. There is no demo, sample, synthetic
corpus or substitute reference in this skill. If no readable image exists yet,
ask for it; never auto-pick one.

## Route before observing

- 2D UI, illustration, objects, weapons and rigid character cutouts → stay in
  this `img2pixi2d` skill; rebuild with PixiJS containers, Graphics, Sprite
  and Text.
- Requested 2.5D or 3D scene composition with real meshes, textured sprites or
  supplied models is out of scope here; hand off to the `img2pixi3d` skill.
- Novel-view/model recovery or animation-ready 3D rig reconstruction from
  images needs `img2threejs` or supplied geometry. Do not call billboards
  reconstructed volumes or silently replace original artwork with primitives.
- An atomic graphic may be one Sprite when it has no independent
  edit/move requirement. Requested text, interaction or motion gets a
  separately controllable semantic node; group with Containers as needed.

## Observe the provided image (native vision, scripts only)

Run before any geometry or crop decision:

1. Native host vision identifies subject kind (UI panel, illustration, object,
   weapon, rigid character cutout, mixed). Distinguish a whole-reference
   screenshot from the intended subject artboard.
2. Record native width × height, alpha presence, visible bounds, palette,
   readable text, occlusion order, and the small details that make the
   subject recognizable.
3. Walk macro → meso → micro. Each requested independent edit, motion or
   action becomes a planned separately controllable layer in
   `reconstruction.json`.
4. Mark hidden surfaces, interrupted contours, foreground occluders, unread
   glyphs, missing alpha and required motion. Separate observed pixels from
   inferred support; do not treat a plausible completion as recovered art.

Preserve the supplied bytes exactly; never repaint the admitted reference.
A flat background is not a matte; crop is not segmentation or unmixing.
If no artist matte exists, follow `references/object-separation.md` to
produce/review image-guided inferred ownership and record its uncertainty.
Request missing evidence when critical ownership cannot be resolved.

## Record source provenance

Always note, even when brief:

- Where the image came from (user-provided path or explicitly consented URL).
- The license/permission the user grants for this build; do not silently
  relicense.
- Whether the supplied image is the original or a normalized working copy.
- Whether an exact text/font requirement applies; if so, whether the
  licensed font bytes (or an explicitly accepted system-family approximation)
  exist. Missing font → record `fontAssetId` as `request-input` in
  `reconstruction.json`, do not silently fall back.

Admit the reference once via the helper (the only image tool this skill owns
for admission):

```bash
python3 -m forge.cli intake /absolute/reference.png --workspace /project/.img2pixi2d
```

The helper writes `reference/original.<ext>`, a normalized sRGB
`reference/working.png` and `intake.json` with both SHA256 hashes. Accepted
inputs are single-frame PNG/JPEG/WebP/BMP/TIFF/GIF. SVG, animation, oversized
or undecodable input is rejected/unsupported; do not substitute a sample.

Limits: 20 MiB encoded, 8192 px per edge, 32 MP decoded. HTTPS needs explicit
user consent plus `--allow-network`; every destination and redirect must
resolve to a public, non-multicast IP. Reference bytes are immutable — a
different source needs a fresh workspace.

Use the working PNG as the pixel/frame authority for `crop`, `compare` and
all visual judgment. Do not overwrite the original or working files; do not
resize either; do not rename them.

## Separation vs segmentation (do not blur)

- Alpha-preserving crop is rectangular cropping that keeps the original
  alpha. It does not separate subject from background.
- A supplied matte is registered full-reference or crop-sized alpha/luminance.
  Crop multiplies it into source alpha without resize; it does not author it.
- Review traced or backend-proposed mattes against physical contours,
  attachments, genuine openings and protected neighbours. Material colour
  thresholds are not object ownership. Keep mixed-edge estimates explicit.
- Handle missing object support and underlying surfaces separately using
  `references/occlusion-completion.md`; only authorized completion may add RGB.

## Identity gate (global vs critical)

Native agent vision judges identity. Scripts provide diagnostics only
(global-moment luma SSIM, mean RGB error, alpha error, full-resolution
difference sheet). Metrics are never a vision score and never an acceptance
decision.

- Global metrics: open framing, layout, overall palette.
- Critical identity features: exact text content and font, signature
  silhouette, recognizable logo, painted pattern, identity-bound color, an
  unreadable glyph, a misregistered edge. Each critical feature is checked
  separately and reported in `reconstruction.json` before rendering.
- A single failing critical identity feature blocks completion regardless
  of aggregate similarity.

## When to stop and request input

Stop observing and ask for the missing input when any of the following is true:

- No reference image is available, or the available bytes are corrupt.
- Critical separation remains ambiguous after native inspection and available
  matte refinement; request the exact layer/matte/view needed to resolve it.
- Exact text/glyph is requested but the licensed font bytes are unknown or
  absent and no system-family approximation was accepted.
- Required exact hidden artwork has no supporting layer/view, or inferred
  completion is unauthorized/unavailable. Do not invent tool availability.
- Required motion parameters cannot be established from user requirements.
- Actual novel-view/model reconstruction is 3D: hand off to `img2threejs`.

Finish all reachable work (routing, observations, provenance, identity
features, unknowns list) before stopping. Do not fabricate confidence and
do not produce a demo fallback.

## Next step

Move on to `references/reconstruction.md` once the above is settled: write
`.img2pixi2d/reconstruction.json` with reference hash, observations,
uncertainties, named layers, critical features and acceptance thresholds.