# Occlusion recognition and bounded completion

A single flattened view cannot reveal exact hidden artwork. Infer support
from evidence, complete it when authorized, and distinguish the result from
observed pixels. PixiJS renders supplied content; it is not a semantic
segmenter or image inpainter. No such backend ships with this skill.

## 1. Recognize missing support before cutting

- Inspect contour interruptions/T-junctions, branch and trunk attachments,
  hull/roof continuation, texture direction and nearer objects. Mark the
  foreground occluder and the interrupted object, not just a missing colour.
- Distinguish an intentional opening, transparency, out-of-frame content and
  occlusion. Record evidence, alternatives and confidence without inventing
  a model score. A fully hidden object's identity is not established by a
  single image; request a layer/reference where appearance matters.
- Record separate regions in common source coordinates: visible ownership,
  inferred full (amodal) support, uncertain boundary, occluder ownership and
  unobserved support. Hidden support may overlap a foreground owner's visible
  pixels; it belongs to a separate layer, not to a destructive shared union.
- Validate contour continuation and attachment against native crops before
  accepting a completed silhouette. Split articulation where motion needs it.

## 2. Establish permission and available authoring tools

- An explicit request to compensate/complete hidden parts authorizes inferred
  hidden-content authoring for that task, not visible-image restyling or an
  automatic 3D migration. Without that request, resolve this fidelity tradeoff
  before generating hidden content. Respect remaining source-only constraints.
- Prefer supplied layers or another view of the same object. Otherwise use
  source-supported cloning/material continuation where it genuinely fits,
  bounded manual authoring, or an actually available masked inpainting tool.
  Record which method was used; do not call any inferred RGB recovered art.
- Discover tool/API/model and mask semantics before use. Do not fabricate a
  segmentation/inpainting service or use `forge crop` as if it generated RGB.
  External image uploads require permission; a completion request alone is
  not consent to send private imagery to a third-party service.
- If the required authoring backend/input is unavailable, finish reachable
  ownership/planning work and request the precise missing tool/layer/view.
  Do not ship holes, generic substitute objects or a fake no-op completion.

## 3. Complete two different surfaces

### Object completion

- Reconstruct the object's occluded geometry/material in its own layer. A
  boat hidden by dock posts needs hull/sail continuation without those posts;
  a trunk behind rock needs trunk continuation, not copied rock or sky.
- Use the inferred support minus trustworthy visible interiors as the allowed
  edit region; include only a reviewed seam/uncertain band where necessary.
  Protect every observed neighbouring owner and the object's known interior.
- Generate/author a candidate separately, then composite ONLY approved hidden
  regions and seam corrections into the final asset. Check decoded pixels in
  protected regions against the original; reject whole-image recolouring.
- Keep inferred alpha/RGB provenance separate from visible-source provenance.
  Keep static occluders above it at the reference pose, so hidden completion
  does not change the observed neutral silhouette.

### Underlying-layer completion

- Removing a moving object reveals another surface. Restore that surface in
  a clean stationary underlay, separately from the moving object's completion.
- Compute what becomes visible across the full requested motion/camera/edit
  envelope. Complete only unknown underlying regions; protect known terrain,
  foliage, dock and other actors. The swept area defines required coverage,
  not permission to repaint every pixel along the entire path.
- Follow the correct surface and depth: continue mountain behind a palm,
  water behind a boat, sky behind an exposed leaf. Do not fill a broad strip
  with one sky colour or stretch an unrelated same-image rectangle.
- Resolve each newly exposed depth layer, not just the far background. When
  a moving front part reveals a rear trunk/branch, that rear object also needs
  an independently correct layer and, if necessary, its own completion.

## 4. Integrate and prove

- Expand texture frames, mesh support, logical bounds, atlas padding, masks
  and filter/culling areas for the completed assets and transformed extremes.
  A stale visible-source bbox can clip correct completed pixels at runtime.
- Preserve source coordinate registration and pivots; never rescale the whole
  admitted image to accommodate added content. Record source/matte/asset
  hashes, completion regions, method/tool/model/version and seed if supplied.
- Inspect the object alone and with each relevant occluder hidden. Inspect
  the underlay with the moving actor hidden. Reject inherited foreground
  pixels, unfinished attachments, holes, ghosts and visible fill seams.
- Run the full native motion gate in `references/review.md`. Ask for explicit
  acceptance of materially ambiguous completed appearances, not blanket
  approval of all cutouts or a high aggregate image score.
