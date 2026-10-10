---
name: img2pixi2d
description: Rebuild images as editable PixiJS 2D scenes with Sprite/Graphics/Text/Container composition, object separation, occlusion completion and native motion review.
version: 1.0.0
---

# img2pixi2D — img2 skill plugin (2D)

Reconstruct the supplied image in the user's PixiJS project as an editable
2D scene. This plugin provides agent instructions and local image tools; it is
not a playground, demo generator or autonomous image-to-model service.

## Input and routing

- Require one readable reference image. If absent, ask for it; never create a substitute reference.
- Route editable 2D artwork (UI, illustration, objects, weapons, character cutouts) here. Use native PixiJS Containers, Graphics, Sprite, Text and 2D Mesh; layered parallax stays 2D.
- Real 3D scene composition with Mesh3D, Sprite3D or Model3D: hand off to `img2pixi3d`; do not invent a 3D runtime here.
- Novel-view or animation-ready 3D rig reconstruction from images still requires `img2threejs` or supplied geometry. Billboards are not recovered volumes.
- Default to **hybrid fidelity**: preserve difficult reference pixels in independently movable layers; use native Text/Graphics for editable content.
- Use procedural-only reconstruction when explicitly requested. Do not silently substitute simpler geometry or trace the whole image as one background.
- Use the existing project and its preview. Do not build a playground, demo, synthetic corpus or benchmark suite.

## Workflow

Run Python image tools from this skill's directory with Pillow in an isolated environment. The CLI exposes only `intake`, `crop` and `compare`; there is no executable 3D setup, beta installer or runtime integrator in this skill. For requested 3D, follow `img2pixi3d` instead.

1. **Observe before code.** Read `references/intake.md`; inspect the actual image using host vision. Identify subject, hierarchy, text, silhouettes, materials/patterns and identity-defining details. Separate observations from inference.
2. **Admit the reference.** Run `python3 -m forge.cli intake <image> --workspace <project>/.img2pixi2d`. HTTPS needs explicit user consent and `--allow-network`. Preserve the original and normalized working PNG; do not modify either.
3. **Plan ownership and occlusion.** Read `references/reconstruction.md` and `references/object-separation.md`. Write `<project>/.img2pixi2d/reconstruction.json`: reference hash, physical owners, visible mattes, occlusion order, protected neighbours, transforms, critical features and full requested motion/edit envelope. Set acceptance before rendering.
4. **Set up the actual 2D renderer.** Read `references/pixijs.md`; preserve the compatible host pin. Use native 2D containers, sprites, graphics, text and meshes as appropriate; do not import a 3D runtime or invent a parallel application.
5. **Separate and complete before animation.** Review supplied or image-guided inferred mattes at native scale; label inference. Follow `references/occlusion-completion.md` for explicitly authorized hidden-object and underlying-layer completion, with protected observed pixels and provenance. Build the typed factory with independent owners/pivots. `forge crop` only extracts observed pixels using a supplied matte; it cannot segment or inpaint.
6. **Build in order.** Review blockout/layout → layers/details → appearance/text → interaction/motion. Keep one source revision across passes; change only the diagnosed failure. Do not regenerate a generic scene every pass.
7. **Run the real output.** Use the project's existing build/preview and the host browser. Capture the actual Pixi canvas at the reference artboard dimensions, after assets and fonts settle. No separate test application.
8. **Compare one reference.** Read `references/review.md`. Run `python3 -m forge.cli compare --reference <working.png> --render <canvas.png> --out <evidence-dir>`; open the resulting sheet and critical crops with vision. Pixel metrics are diagnostics, not AI scores or proof of editability.
9. **Prove non-destructive motion.** Hide/move each requested owner with other effects frozen; reject damaged neighbours, borrowed pixels, ghosts and holes. Inspect full requested motion, extrema and occluder crossings, alone and combined; reset and verify requested controls. Neutral similarity, FPS and state changes are not animation acceptance.
10. **Correct or stop.** Record exactly one `continue | refine-spec | refine-code | request-input | stop` with evidence and concrete defects. Allow at most 3 corrections per pass, 6 total; inspect the last allowed correction before stopping further attempts. Repeated defects or unavailable reference data require input, not fabricated confidence.
11. **Deliver into the project.** Supply the factory, reconstruction data and permitted assets. Verify disposal/reuse, missing-resource behavior and the actual changed path. Report observed checks, artifact paths and accepted approximations; never claim fidelity from compilation alone.

## Hard rules

- Native agent vision makes visual judgments; scripts never manufacture global/per-feature vision scores.
- A critical identity, ownership, completion or animation-cutting defect blocks completion regardless of aggregate similarity. User-reported failures invalidate prior acceptance.
- Every independent text, moving or interactive part needs an independently controllable node.
- One Sprite is acceptable only for an atomic graphic with no internal editing or movement requirement.
- Alpha-preserving crop is not segmentation. Review supplied or image-guided inferred mattes; never use material-colour gates as physical ownership or claim inferred alpha is artist alpha.
- Exact text requires actual licensed font bytes or an explicitly accepted approximation; do not silently use a system fallback.
- Preserve supplied artwork and code. Do not overwrite unrelated files or claim ownership/license of user images.
- Host owns Application, ticker and resource lifecycle; a scene factory owns only its scene and listeners.
- 3D composition is out of scope here; route requested meshes/models to `img2pixi3d` instead of installing or importing a 3D runtime in this skill.
- Exact hidden artwork is unavailable from one flattened view. Complete only authorized inferred regions with available authoring tools; keep observed owners protected. Missing required tool/font/layer: request the precise prerequisite, finish reachable work, no fake fallback.

## Progressive references

- Admission and uncertainty: `references/intake.md`.
- Layer/spec decisions and crop CLI: `references/reconstruction.md`.
- PixiJS 2D APIs and runtime ownership: `references/pixijs.md`.
- Single-image visual review and evidence: `references/review.md`.
- Object mattes and protected neighbours: `references/object-separation.md`.
- Amodal objects and disoccluded underlying layers: `references/occlusion-completion.md`.