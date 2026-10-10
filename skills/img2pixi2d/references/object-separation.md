# Object separation — ownership before animation

Read before extracting any independently moving object from an opaque image.
A segmentation proposal is evidence to review, not ground-truth artist alpha.
`forge crop` applies a supplied matte; it performs no semantic segmentation.

## 1. Map physical owners

- Inspect native crops, including dark interiors, glass, gold leaf tips, thin
  ropes and antialiased boundaries. Colour similarity is not object identity.
- Name each physical object, attached parts and stationary neighbours. Do not
  assign a mountain, dock post or sky strip to a nearby moving tree/boat.
- Mark observed front/back relations from T-junctions, contour termination,
  overlap and attachments. Record ambiguous relations as inference. Use a
  partial occlusion order; split interleaving parts instead of forcing one z.
- For each object record registered visible-ownership matte, uncertain edge
  band, protected neighbouring regions, occluders and requested motion/edit
  envelope. Link amodal support/completion separately; see
  `references/occlusion-completion.md`.
- Treat shadows, reflections, foam and translucent edges as separate
  contributions where necessary, not solid geometry stolen from neighbours.

## 2. Produce and refine the matte

1. Prefer supplied transparent layers/artist mattes. Otherwise discover an
   actually available segmentation/matting backend and its version, or trace
   image-guided physical contours. Record backend/prompts/positive-negative
   points or traced control points and which boundaries are uncertain.
2. Use object-specific positive points plus negative points on adjacent sky,
   mountain, water, house and dock. Refine each touching/interleaving component.
   Do not accept an entire bounding rectangle or a single scene-wide mask.
3. Inspect RGBA alone on black, white and checkerboard, then at the original
   position. Preserve opaque shadow/glass/material pixels. Preserve genuine
   holes between leaves, ropes and rails. Do not punch holes using RGB gates.
4. Check thin appendages and connected attachments individually. A model can
   miss fronds or capture a neighbour; review and correct its proposal.
   Morphological dilation/erosion must be locally justified, never blanket
   cleanup that steals a neighbour or deletes opaque source detail.
5. Separate opaque observed interiors from mixed boundary pixels. Keep
   interiors source-bound. If edge unmixing/decontamination is necessary,
   confine it to the declared uncertain band and label the estimate. Keeping
   sky-coloured composite RGB under fractional alpha is not a clean cutout.
6. Keep all mattes registered in native source coordinates. Verify size,
   origin, trim offset and attachment pivot before packing. Export an RGBA
   revision and provenance; do not overwrite the admitted reference.

## 3. Build independent owners, not cut-up context

- Keep visible source RGBA, completed object RGBA and clean underlying layer
  distinct. Compose them with the recorded occlusion order; do not erase a
  stationary neighbour to reveal a moving object.
- Remove each actor's visible ownership from the corresponding static
  underlay only. Restore unobserved underlying content using the completion
  workflow, while preserving every other observed owner's pixels.
- Never place the opaque original behind all cutouts to disguise incomplete
  ownership. Never move an opaque sky/water/terrain crop with the foreground.
- Grow logical texture/canvas/atlas bounds to include completed support.
  Preserve native pivot/trim registration; atlas extrusion is sampling
  padding, not missing anatomy or terrain completion.
- Keep authored anchors separate from private motion. Keep a moving object's
  mask in its local space; keep stationary occluders stationary. Audit stale
  source-bbox clips, shared masks, filter areas, culling bounds and UV frames
  when the asset is correct but the renderer cuts it.

## 4. Admit the layer only after destructive tests

- Hide and move each owner alone with other animation/effects frozen. The
  mountain/tree/dock left behind must remain intact, without actor ghosts,
  opaque rectangles, diagonal sky cuts or missing silhouettes.
- Show each layer alone: no borrowed neighbour pixels. Inspect full source
  and completed silhouettes, not only the neutral recomposition.
- Seek full requested motion, including extrema and occluder crossings;
  inspect vacated footprints and newly exposed object surfaces. A boat must
  not carry dock-post pixels or reveal post-shaped holes in its own hull.
- Compare protected neighbour regions before/after isolation. Exclude only
  explicitly expected occlusion/effect contributions. Unexpected changes
  outside the edit/completion masks fail the layer gate.
- Follow `references/review.md` for native evidence and motion acceptance.
  Exact neutral assembly cannot certify any of these separation properties.
