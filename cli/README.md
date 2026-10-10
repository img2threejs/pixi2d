# @img2threejs/pixi2d

Installer-only CLI for **img2pixi2d**, the private native OMP skill plugin for editable PixiJS 2D reconstruction. This npm package includes only the installer, metadata, this README and its Apache-2.0 license. It does **not** include the private skill, Python tools, examples, artwork or credentials. The installer license does not license the private source or user artwork.

## Requirements

- macOS/Linux, Node.js >=18, OMP and Git on `PATH`.
- Authorized Git access to the **private** `img2threejs/pixi2d` repository. The public npm installer does not grant repository access.
- Python >=3.10 with `venv`/pip; install prepares an isolated Pillow environment.
- Standalone Bun on `PATH` for removal: OMP's native uninstall uses Bun even when OMP itself is a compiled executable.
- Your existing PixiJS v8 project for reconstruction; verified host release is 8.22.0. The installer never installs host Pixi dependencies or creates a demo app.

Configure private Git access without embedding credentials:

```sh
gh auth login --hostname github.com --git-protocol https
gh auth setup-git --hostname github.com
```

## Install and manage

```sh
npx --yes @img2threejs/pixi2d@latest install --dry-run
npx --yes @img2threejs/pixi2d@latest install --yes
npx --yes @img2threejs/pixi2d@latest doctor
npx --yes @img2threejs/pixi2d@latest update --yes
npx --yes @img2threejs/pixi2d@latest remove --yes
```

The first `--yes` authorizes npx downloading the public CLI. The final `--yes` authorizes installer mutations. Without the final flag, mutations fail before touching HOME. `--dry-run` is offline and does not run subprocesses or write HOME.

Install clones `https://github.com/img2threejs/pixi2d.git` into `~/.local/share/img2threejs/pixi2d`, checks out **`ea55d1534ad215ddb8060732ae581dbe2a662cb8`**, installs pinned Python requirements in its `.venv`, then registers it using `omp plugin link`. Keep the checkout: OMP links it by symlink. Start a **new OMP session** in your existing host project and invoke `/skill:img2pixi2d` with a readable reference image.

Update uses the source pin of the CLI version you run; it does not pull an unreviewed default branch. Existing checkouts must have the expected Git origin and no tracked/untracked changes. A registration pointing elsewhere is never replaced. To reuse another authorized clone, pass its absolute `--directory` on every command:

```sh
npx --yes @img2threejs/pixi2d@latest install --yes --directory /absolute/path/to/pixi2d
npx --yes @img2threejs/pixi2d@latest doctor --directory /absolute/path/to/pixi2d
```

Remove delegates to `omp plugin uninstall pixi2d`. It unregisters only; the source checkout, `.venv`, and host artwork remain. Doctor checks this installer's Git pin, skill file, Pillow import, matching native OMP registration and native plugin diagnostics; it is not a visual reconstruction review.

This is **not an img2 harness plugin**: `img2 add pixi2d` is not supported. The executable is `img2pixi2d`; the npm package is `@img2threejs/pixi2d`. `--version` reports installer version 0.1.0, independently of source skill version 1.0.0.

## Release maintenance

Run `npm test` in `cli/`, inspect `npm pack --dry-run`, then tag `cli-v0.1.0`. The pinned reusable workflow publishes only `cli/` via npm Trusted Publishing. Provenance is disabled because the GitHub source repository is private. Source root `package.json` remains `private: true`.
