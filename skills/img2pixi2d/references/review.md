# Review — one reference, actual output

## Capture the existing project

1. Build/run the user's existing project; wait for actual assets and fonts.
2. Render the intended state and capture its real Pixi canvas PNG at the reference artboard size.
3. Read the saved PNG back. Browser chrome/inspector UI is not part of the canvas reference.
4. Use the admitted working image as authority, never an image repainted from reconstruction code.

```bash
python3 -m forge.cli compare --reference /project/.img2pixi2d/reference/working.png \
  --render /project/.img2pixi2d/evidence/render.png --out /project/.img2pixi2d/evidence
```

Add `--bbox X Y W H` for a critical native-resolution region. Frame mismatch is an error; neither input is resized. Sheet: reference over white, render over white, absolute RGB difference.

Diagnostics: normalized RGB error over white/black, alpha error and **global-moment** luma SSIM. This is not windowed SSIM, semantic segmentation, an AI score or editability proof. Check black-composite/alpha error for translucent art. Inspect small and color-sensitive details in separate native crops.

## Native visual judgment

Read the actual reference/render/critical crops with host vision. Compare silhouette, proportions, layout, exact text/font/glyph placement, alpha edges, color, pattern and identity details.

Assess global agreement and every declared critical feature against acceptance set **before** rendering. Record concrete matches/defects and, when the planned contract uses numeric native-vision thresholds, actual reviewer-assigned scores with reasons. Never derive vision scores from pixel metrics, copy a default score or silently waive a critical defect.

Exact font/hidden-art requirements still need source evidence. Inferred mattes and explicitly authorized occlusion completion follow their dedicated workflows, with native review and provenance. A high whole-image metric never overrides critical ownership, completion or motion damage.

## Actual runtime evidence

Exercise only applicable requested behavior on this same reconstruction:
- Replace Text and inspect pixels; reject the prior wording baked behind it.
- Hide/move each requested foreground owner; reject duplicates, stolen neighbour pixels and damaged underlying layers.
- Rotate/seek the FULL requested envelope, not just what the reference happens to show; inspect exposed object/underlay surfaces and reset baseline.
- Verify pointer/keyboard/disabled/cancel behavior, focus and real callback counts.
- Dispose/recreate with shared host resources; other consumers still work.
- This skill is 2D-only; for requested 3D runtime verification, follow
  `img2pixi3d`. A primitive 2D scene smoke proves integration, never
  image fidelity or hidden geometry recovery.

Use the existing project. Do not add a test UI, demo, synthetic corpus or benchmark app. Requested performance claims require real target measurements; unavailable hardware remains unmeasured.

## Mandatory ownership and motion gate

Before animation acceptance, use `references/object-separation.md` and
`references/occlusion-completion.md`. Record separate evidence for:

1. **Asset ownership:** RGBA on black/white/checkerboard; opaque interiors,
   thin attachments, genuine openings and absence of neighbouring RGB.
2. **Object support:** visible and inferred amodal layers, then relevant
   occluders hidden; newly exposed hull/trunk/fronds are complete and coherent.
3. **Underlying support:** actor hidden; terrain, water and intermediate
   objects are intact without ghosts, broad sky fills or pasted rectangles.
4. **Isolated motion:** freeze unrelated effects/actors. Seek start/end,
   extrema, all depth/occlusion crossings and user-reported failing states.
   Inspect native frames/crops, not just transforms or successful callbacks.
5. **Continuous coverage:** inspect the full requested cycle/path, with
   sampling refined around crossings/extrema so thin features or brief cuts
   cannot fall between accepted samples. Record times/poses and limitations;
   a neutral image plus one moving frame is insufficient.
6. **Combined states:** inspect requested simultaneous wind/sailing/parallax,
   light presets and camera/scale extremes, plus reset and authored edits.
7. **Protected neighbours:** compare stationary owner regions outside
   declared expected occlusion/effect/edit contributions. Unexpected alpha/RGB
   changes, diagonal cutouts and exposed missing surfaces fail acceptance.

Do not reduce motion amplitude/path, disable an actor or hide a defect under
the opaque original to pass. Change requested behavior only with explicit
user approval. FPS, neutral pixel equality and a state hash do not prove
correct separation or completion.

## Record and resume

Agent authors `.img2pixi2d/reconstruction.json` and a historical `review.json` record. No state SDK/automatic pass controller is provided.

Each review records pass, reviewer, exactly one decision (`continue | refine-spec | refine-code | request-input | stop`), concrete defects, actual global/per-critical assessments, requested runtime observations, evidence paths and approximations.

Bind it to:
- `referenceHash`: actual working PNG bytes.
- `specHash`: canonical JSON of reconstruction data, excluding bookkeeping/history.
- `sourceHash`: canonical JSON map `{project-relative source path: SHA256(file bytes)}`.
- `assetHash`: the same map convention for loaded images/fonts and layer provenance.
- `profileHash`: canonical JSON of the actual frame, resolution and reviewed state/motion settings.
- Each evidence artifact: its actual byte SHA256.

Canonical JSON sorts object keys, uses UTF-8, compact separators and rejects non-finite numbers. File hashes are raw byte SHA256. `forge/common.py` supplies these helpers; hashes prove freshness, not visual quality.

Read records, real source/resources and artifact hashes at every start/resume. Never reconstruct completion from chat memory. Do not hash the review/history into its own spec binding.

## Corrections and invalidation

Correct one causal group: framing → hierarchy/silhouette → text/details → appearance → behavior. Do not combine unrelated edits or lower thresholds after a failed output.

Count completed correction actions: at most 3 per pass, 6 total. Inspect the last allowed correction before refusing another; reviewing it is not an extra correction. Preserve counters/history on resume. Repeated unresolved defects, oscillation or no observed improvement require reassessment/input, not an invented numerical gain threshold.

Changed reference requires a new admitted workspace; retain the old workspace/history. Changed spec/source/resources/profile makes dependent captures/reviews stale. Record invalidation separately from the five decision actions, preserve historical reviews, and capture again. Do not delete the ledger or invent `action: invalidate` as a sixth decision.

User-reported damaged artwork immediately withdraws dependent animation/
ownership acceptance. Preserve old observations as history, record the
reported state/evidence and unresolved defect, and select a current decision.
Do not rerun to dispute the report or relabel major cuts as accepted fringes.

## Delivery

Deliver the subject factory, reconstruction data and permitted resources into the user's project. Report observed checks, critical assessments, evidence paths and accepted approximations.

If the intended test image is absent, fidelity on it is unverified. A labelled local script smoke image is not the user's reconstruction and is never a substitute demo.
