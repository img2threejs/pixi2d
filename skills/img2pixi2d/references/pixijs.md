# PixiJS — implement in the user's project

Resolve current APIs from [PixiJS v8 guides](https://pixijs.com/8.x/guides) and [release API docs](https://pixijs.download/release/docs/). The checked release for this implementation/smoke was **8.22.0**; run `npm view pixi.js version` for a new project. Respect an existing compatible pin rather than silently upgrading it.

For real 3D composition (Mesh3D, Sprite3D or supplied Model3D), hand off to `img2pixi3d`. Ordinary 2D reconstruction, native 2D meshes and layered parallax do not need a 3D runtime; this skill does not vendor, install or import one.

## Host and subject ownership

- Host owns Application, renderer, ticker, canvas, resize and resource loading/cache.
- A subject factory receives loaded resources and returns its root, stable semantic nodes and only requested controls. It does not create an Application or start a private ticker.
- Drive requested motion in seconds (`ticker.deltaMS / 1000`). Seek/reset is deterministic, not dependent on wall clock or frame rate.

## Application readiness and capture

`new Application()` does not initialize its renderer. The existing host awaits `app.init(options)` before constructing/rendering the subject. Do not create a second host to test the reconstruction.

For direct canvas readback, use an explicit fixed width/height/resolution/background and render the intended state immediately before `app.canvas.toDataURL('image/png')`. WebGL may discard its drawing buffer between frames; `preserveDrawingBuffer: true` supports retained-buffer readback but has a cost. Alternatively use the host renderer's current extract API. Do not enable expensive capture settings in production without a reason.

Wait for actual assets and the exact font/glyph readiness before capture. Record renderer, dimensions, resolution, background, state/time and clipping. CSS size alone does not prove canvas pixel dimensions. Inspect real output; blank readback is a capture defect, not a successful render.

## Graphics

Use current shape/path builders and `.fill()` / `.stroke()` / `.cut()`, not deprecated v7 sequencing:

```ts
const shape = new Graphics()
  .roundRect(0, 0, width, height, radius)
  .fill({ color: 0xff0000, alpha: 0.5 })
  .stroke({ width: 2, color: 0xffffff, alpha: 1 });
```

Use Graphics for observed geometry, not an invented simplification of critical painted detail. Reuse GraphicsContext only when appropriate; do not destroy a shared context while another Graphics uses it. Follow ownership explicitly rather than assume all destruction options are safe.

## 2D meshes

Native PixiJS Mesh/MeshGeometry remain 2D. Use them for requested source-textured deformation or UV effects with explicit vertex, UV, winding and resource ownership. Preserve attachment/observed pixels and reject folds, borrowed neighbours or clipping over the full motion envelope; a 2D mesh does not recover hidden anatomy or 3D volume.

## Text and fonts

Load real licensed font bytes through the project's loader/Pixi Assets or FontFace convention before measuring/constructing native Text. Verify the resolved family, weight, style and required glyphs; `document.fonts.ready` alone does not establish identity.

```ts
const label = new Text({
  text: actualLabel,
  style: { fontFamily: loadedFamily, fontSize: measuredSize, fill: 0xffffff },
});
label.text = requestedLabel;
```

Measure actual loaded glyphs via Pixi text metrics/layout, not character-count heuristics. Implement only requested wrapping/overflow. Preserve independent text; no baked duplicate label behind the Text node. HTMLText/BitmapText require an actual project need, not a blanket replacement.

## Assets, color and alpha

- Fetch URL textures with `await Assets.load(url)`, then pass the loaded Texture into Sprite. `Texture.from(urlString)` is cache lookup, not a network loader.
- Place cropped/trimmed textures using logical bounds and trim offsets from the crop metadata. Parent scaling applies consistently to texture and offset.
- Use explicit 24-bit RGB plus a separate normalized alpha for fills/strokes/transforms when the source carries alpha. Parsing an RGBA color and using only its RGB conversion loses opacity. Do not guess channel ranges or infer transparency from a numeric hex value.
- Alpha masks, geometry, texture frames and filter/culling bounds must use the correct coordinate space and cover completed support at transformed extremes. Do not reuse one source-bbox clip across independently moving owners.
- Host unloads shared assets only after every consumer releases them. Scene disposal must not call `Assets.unload` or destroy host-owned textures/fonts.

## Requested interaction and state

Use federated pointer events and current `eventMode`, explicit appropriate hit areas and actual callbacks. Convert global positions through the correct parent's `toLocal` under scale/rotation/reflection. Preserve the grab offset for drag.

Disabled actions suppress input/dispatch, not just tint. Immutable does not mean disabled. Release/outside/cancel leaves no stuck pressed state. Hover/press updates do not accumulate transforms. Requested reduced-motion handling uses a deterministic meaningful state, not blank output.

## Disposal and verification

Implement an idempotent subject-level dispose guard; do not assume Pixi's raw destroy methods are repeat-safe. Remove owned nodes/listeners/filters/geometry without destroying shared resources or host Containers. Recreating the subject and a simultaneous second consumer must remain valid when that lifecycle is requested.

Use the user's existing preview/build and browser surface; no separate playground, demo or shipped capture framework. Exercise requested mutations and inspect their actual pixels/actions. Native agent vision judges identity; the Python compare command supplies diagnostics only.
