# Reconstruction — guide to one subject-specific Pixi factory

`<project>/.img2pixi2d/reconstruction.json` is the work plan for THIS
image, not a universal Pixi schema or runtime template. Author the
typed factory in the user's project; no demo, scaffold, scene corpus or
separate test page.

## 1. Observe, then plan (no fabrication)

Read `references/intake.md`, then admit the reference:

```
python3 -m forge.cli intake /abs/reference.png --workspace <project>/.img2pixi2d
```

Tool writes `reference/original.*` (immutable) and `reference/working.png`
(sRGB RGBA). Never mutate either. Working PNG is the pixel authority.

Native vision identifies subject class (UI / illustration / object /
weapon / rigid character), parent scene vs. cutout, hierarchy, exact
readable text, colors, silhouettes, occlusion, identity details. Tag
each entry `observed` vs. `inference` vs. `accepted approximation`.

## 2. Plan the reconstruction JSON

Record before any source file:

- Reference hash/path, artboard `width`/`height`, transparent vs. opaque.
- Named components: id, parent, representation (2D Sprite/Graphics/Text/Mesh/
  Container), bounds, native transform (2D x/y position, rotation in radians,
  scale), resource identity and every requested independent edit/move/action
  as its OWN node. Requested 3D meshes/sprites/models belong to the
  `img2pixi3d` skill; do not model 3D in this skill.
- `identityFeatures[]`: region `[x,y,w,h]`, expected text/color/shape,
  vision threshold, measurable tolerance.
- Requested motion/state/actions and full envelope; honest unknowns.
- Per-owner visible matte, amodal support, occluders, protected regions,
  object/underlay completion masks, permission and observed/inferred provenance.
- Pass / hash log: reference, spec, source, asset-manifest,
  render-profile, review hashes; corrections-per-pass, next decision.

## 3. Coordinates & layering

Top-left origin, +X right, +Y down. Reference pixels = artboard units.
Radians. Apply reference-to-artboard scaling ONCE; do not mix CSS,
canvas and artboard coordinates.

Semantic parts in Containers; native Sprite/Graphics/Text/2D Mesh leaves.
Render order deterministic. Pivots at observed attachment points,
never auto-derived from bounding-box centers or trim offset.

Negative scale reflects paired parts only when reference geometry is
mirrored. Independent `Text` stays `Text`; moving parts cannot stay
baked in a stationary Sprite; static background and movable foreground
may NOT share one flat Sprite. A character cutout is a rigid
articulated hierarchy, not an inferred rig.

## 4. Extract observed layers (crop CLI)

```
python3 -m forge.cli crop --workspace <project>/.img2pixi2d \
  --bbox 120 64 240 180 [--mask masks/observed-part.png] --out layers/part.png
```

`--bbox` is an exact in-bounds reference-space rectangle. Require `--mask`
when a rectangular crop captures context. Use a supplied or native-reviewed
inferred matte from `references/object-separation.md`, not material RGB gates.
Crop cannot generate hidden RGB; author completed assets separately using
`references/occlusion-completion.md` and preserve registered source interiors.

Tool rules: matte resolution crop-sized or full-reference-sized (no
resize); RGB mattes use luminance, RGBA/LA use alpha; matte multiplies
existing alpha. Output PNG, written outside `reference/`. Refuses to
overwrite a different layer at the same path.

`.meta.json` carries `originalWidth`, `originalHeight`, `trimOffset`
`[tx,ty]`, encoded `width`/`height`, hashes. When placing a trimmed
Sprite: add `trimOffset` inside the logical component BEFORE applying
parent transforms or scaling. Never shrink the logical bounds to the
trimmed texture.
Include completed support in logical bounds, UV/atlas frames and local masks;
stale visible-only bounds must not clip hidden completion during motion.

## 5. Factory authoring rules (Pixi v8)

Author a typed, subject-specific factory in the user's existing project.
Use its existing resource loader/interfaces. This skill is 2D-only; for
requested 3D, route to `img2pixi3d`, which owns its own bounded 3D node
construction/lifecycle.

Hard rules:

- Host owns Application, renderer, ticker, resize and shared resources.
  Load actual textures/fonts before constructing the subject. Do not
  create an Application or start a private ticker inside its factory.
- Return stable semantic node references and only requested controls.
  Containers represent real grouping/attachment/transform needs; do
  not wrap every leaf merely to satisfy a generic descriptor schema.
- Keep mask shapes and target nodes in correct coordinate spaces.
  Masking must not retain a second visible copy of the artwork.
- Place a trimmed Sprite at its trim offset inside logical bounds,
  then apply parent transforms. If scaling, multiply both the texture
  and offset by the same reference-to-component scale. Use an explicit
  observed anchor/pivot; trim is not a new attachment point.
- Keep readable, independently editable text native. Load and verify
  the actual font/glyphs; `document.fonts.ready` alone does not identify
  the font. Implement only requested overflow/wrapping behavior.
- Implement only requested motion/actions/state changes. Preserve the
  authored baseline, including after repeated transitions and reset.
- Dispose owned nodes/listeners/geometry idempotently. Never destroy
  host-owned textures/fonts/Containers or another subject's resources.
  Follow the host project's actual disposed-handle contract.

Pixi v8 pitfalls (avoid in the factory):

- `await app.init(opts)` is the renderer-readiness path; bare
  constructor does not init.
- `Graphics` uses current path/shape builders + `.fill()`/`.stroke()`,
  not v7 fill sequencing.
- `Text({text, style})`; measure with the loaded real font.
- `Texture.from(url)` only does cache lookup — fetch via
  `await Assets.load(url)`.
- `#RRGGBBAA` parses as 24-bit RGB in some hosts — keep alpha on a
  separate channel when needed.
- `eventMode='static'|'dynamic'` + explicit hit area + federated
  pointer events; convert global pointer coords with `parent.toLocal`.

Provenance: user artwork stays user-owned (no CC0 claim); font/image
licences stay attached to their derived assets.

## 6. Build order (review each pass against the same image)

1. **Blockout**: framing, artboard, parent-local hierarchy, pivots.
2. **Structure**: visible layers, occlusions, contours, pattern
   placement, identity micro-details.
3. **Appearance & text**: exact font + glyph readiness, color/alpha,
   strokes, effects. Verify font with `document.fonts.ready` before
   capture. Reject baked duplicate text behind a Text node.
4. **Interaction & motion**: requested actions only, independent
   mutations, state transitions, deterministic `reset`.

Keep one source revision per pass; fix the diagnosed defect, no substitute
demo/reference. Complete authorized missing object/underlay regions without
damaging observed owners. Prove the full requested motion envelope and
protected-neighbour invariants in `references/review.md`; otherwise block
acceptance and identify the precise unresolved prerequisite.
