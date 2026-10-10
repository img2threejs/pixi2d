#!/usr/bin/env node
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';

const metadata = JSON.parse(fs.readFileSync(new URL('../package.json', import.meta.url), 'utf8'));
const source = 'https://github.com/img2threejs/pixi2d.git';
const revision = 'ea55d1534ad215ddb8060732ae581dbe2a662cb8';
const origins = new Set([source, source.slice(0, -4), 'git@github.com:img2threejs/pixi2d.git', 'git@github.com:img2threejs/pixi2d', 'ssh://git@github.com/img2threejs/pixi2d.git']);
const help = `img2pixi2d ${metadata.version} — native OMP installer (not an img2 harness plugin)

Usage: img2pixi2d <install|update|doctor|remove> [--directory ABSOLUTE_PATH] [--yes] [--dry-run]
       img2pixi2d --version | --help

Requires Node >=18, OMP, Git, private GitHub repository access, Python >=3.10.
Removal also requires standalone Bun on PATH, as required by OMP.
Install/update clone the pinned source, prepare .venv/Pillow and run omp plugin link.
Mutations require --yes. Dirty/unrelated checkouts and foreign registrations are refused.
--dry-run prints the plan without subprocesses, network or HOME changes.
Remove unregisters the plugin only; the source checkout, .venv and artwork remain.
Default checkout: ~/.local/share/img2threejs/pixi2d
Source pin: ${revision}
Restart OMP after installation, then use /skill:img2pixi2d in your existing PixiJS project.
`;

function fail(message, code = 1) {
  const error = new Error(message);
  error.exitCode = code;
  throw error;
}
function run(command, args, capture = false) {
  const result = spawnSync(command, args, { encoding: 'utf8', stdio: capture ? 'pipe' : 'inherit' });
  if (result.error) fail(`${command}: ${result.error.message}`);
  if (result.status !== 0) fail(`${command} failed (${result.status ?? result.signal}).${capture ? ` ${result.stderr.trim()}` : ''}`);
  return capture ? result.stdout.trim() : '';
}
function checkCheckout(directory) {
  if (!fs.existsSync(directory)) return false;
  if (fs.lstatSync(directory).isSymbolicLink() || !fs.statSync(directory).isDirectory()) fail('Checkout must be a real directory, not a file or symlink.', 2);
  if (!fs.existsSync(path.join(directory, '.git'))) fail('Refusing an existing directory that is not a Git checkout.', 2);
  const root = run('git', ['-C', directory, 'rev-parse', '--show-toplevel'], true);
  if (fs.realpathSync(root) !== fs.realpathSync(directory)) fail('Refusing a nested checkout directory.', 2);
  if (!origins.has(run('git', ['-C', directory, 'remote', 'get-url', 'origin'], true))) fail('Refusing a checkout from another repository.', 2);
  return true;
}
function registration(directory) {
  const listing = JSON.parse(run('omp', ['plugin', 'list', '--json'], true));
  const installed = listing.npm.find(plugin => plugin.name === 'pixi2d');
  if (installed && (!fs.existsSync(installed.path) || !fs.existsSync(directory) || fs.realpathSync(installed.path) !== fs.realpathSync(directory))) fail('pixi2d is registered elsewhere. Keep it intact; pass its --directory explicitly.', 2);
  return installed;
}

try {
  const args = process.argv.slice(2);
  if (args.length === 0 || (args.length === 1 && ['--help', '-h'].includes(args[0]))) {
    console.log(help);
  } else if (args.length === 1 && args[0] === '--version') {
    console.log(metadata.version);
  } else {
    const command = args.shift();
    if (!['install', 'update', 'doctor', 'remove'].includes(command)) fail('Unknown command. Use --help.', 2);
    let directory = path.join(os.homedir(), '.local/share/img2threejs/pixi2d');
    let yes = false;
    let dryRun = false;
    while (args.length) {
      const flag = args.shift();
      if (flag === '--yes') yes = true;
      else if (flag === '--dry-run') dryRun = true;
      else if (flag === '--directory') {
        const value = args.shift();
        if (!value || !path.isAbsolute(value)) fail('--directory requires an absolute path.', 2);
        directory = path.resolve(value);
      } else fail(`Unknown option: ${flag}`, 2);
    }
    if (dryRun) {
      console.log(JSON.stringify({ command, directory, source, revision, changes: command === 'doctor' ? 'none' : command === 'remove' ? 'OMP registration only; keep checkout and artwork' : 'pinned Git checkout, .venv/Pillow, native OMP link' }, null, 2));
    } else {
      if (command !== 'doctor' && !yes) fail('Pass --yes to authorize the documented changes. Use --dry-run to inspect first.', 2);
      const exists = checkCheckout(directory);
      if (command !== 'install' && !exists) fail('Checkout not found. Run install, or provide its absolute --directory.', 2);
      if (['install', 'update'].includes(command) && exists && run('git', ['-C', directory, 'status', '--porcelain', '--untracked-files=all'], true)) fail('Refusing a dirty checkout; preserve or commit your changes before updating.', 2);
      if (['install', 'update'].includes(command)) {
        const environment = path.join(directory, '.venv');
        if (fs.existsSync(environment) && fs.lstatSync(environment).isSymbolicLink()) fail('Refusing a symlinked Python environment; it may belong to another project.', 2);
        run('git', ['--version'], true);
        run('python3', ['-c', 'import sys; assert sys.version_info >= (3, 10), "Python >=3.10 required"'], true);
      }
      if (command === 'remove') run('bun', ['--version'], true);
      const installed = registration(directory);
      if (command === 'remove') {
        if (!installed) fail('pixi2d is not registered in this OMP profile.', 2);
        run('omp', ['plugin', 'uninstall', 'pixi2d', '--json']);
        console.log(`Kept checkout and Python environment: ${directory}`);
      } else if (command === 'doctor') {
        if (!installed) fail('pixi2d is not registered in this OMP profile.', 2);
        if (run('git', ['-C', directory, 'rev-parse', 'HEAD'], true) !== revision) fail('Checkout does not match this installer source pin.', 2);
        if (!fs.existsSync(path.join(directory, 'skills/img2pixi2d/SKILL.md'))) fail('img2pixi2d skill is missing.');
        run(path.join(directory, '.venv/bin/python'), ['-c', 'from PIL import Image; print("Pillow", Image.__version__)']);
        const diagnostics = JSON.parse(run('omp', ['plugin', 'doctor', '--json'], true));
        console.log(JSON.stringify(diagnostics, null, 2));
        if (!diagnostics.some(item => item.name === 'plugin:pixi2d' && item.status === 'ok')) fail('Native OMP diagnostics did not report pixi2d healthy.');
        console.log(`img2pixi2d registered at pinned source ${revision}`);
      } else {
        if (!exists) {
          fs.mkdirSync(path.dirname(directory), { recursive: true });
          run('git', ['clone', '--no-checkout', source, directory]);
        } else run('git', ['-C', directory, 'fetch', 'origin', revision]);
        run('git', ['-C', directory, 'checkout', '--detach', revision]);
        run('python3', ['-m', 'venv', path.join(directory, '.venv')]);
        run(path.join(directory, '.venv/bin/python'), ['-m', 'pip', 'install', '-r', path.join(directory, 'skills/img2pixi2d/requirements.txt')]);
        run('omp', ['plugin', 'link', directory, '--json']);
        console.log(`Installed img2pixi2d at ${revision}. Restart OMP; invoke /skill:img2pixi2d.`);
      }
    }
  }
} catch (error) {
  console.error(`img2pixi2d: ${error.message}`);
  process.exitCode = error.exitCode ?? 1;
}
