import assert from 'node:assert/strict';
import { test } from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const cli = fileURLToPath(new URL('../bin/cli.mjs', import.meta.url));
function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'pixi2d-safety-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const home = path.join(root, 'home');
  fs.mkdirSync(home);
  fs.writeFileSync(path.join(home, 'keep'), 'original');
  return { root, home };
}
function invoke(home, args, emptyPath = true) {
  return spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8', env: { ...process.env, HOME: home, ...(emptyPath ? { PATH: '' } : {}) } });
}
function unchanged(home) {
  assert.deepEqual(fs.readdirSync(home), ['keep']);
  assert.equal(fs.readFileSync(path.join(home, 'keep'), 'utf8'), 'original');
}

test('dry-run works without dependencies and leaves HOME untouched for every command', t => {
  const { home } = fixture(t);
  for (const command of ['install', 'update', 'doctor', 'remove']) {
    const result = invoke(home, [command, '--dry-run']);
    assert.equal(result.status, 0, result.stderr);
    unchanged(home);
  }
});

test('mutations without consent are refused before touching HOME', t => {
  const { home } = fixture(t);
  for (const command of ['install', 'update', 'remove']) {
    const result = invoke(home, [command]);
    assert.equal(result.status, 2);
    unchanged(home);
  }
});

test('relative checkout paths cannot redirect an installation into the project', t => {
  const { home } = fixture(t);
  const result = invoke(home, ['install', '--yes', '--directory', 'relative']);
  assert.equal(result.status, 2);
  unchanged(home);
});

test('an unrelated existing directory is preserved', t => {
  const { root, home } = fixture(t);
  const directory = path.join(root, 'artwork');
  fs.mkdirSync(directory);
  fs.writeFileSync(path.join(directory, 'drawing.txt'), 'owned by user');
  const result = invoke(home, ['install', '--yes', '--directory', directory]);
  assert.equal(result.status, 2);
  assert.deepEqual(fs.readdirSync(directory), ['drawing.txt']);
  assert.equal(fs.readFileSync(path.join(directory, 'drawing.txt'), 'utf8'), 'owned by user');
  unchanged(home);
});

test('a dirty source checkout is refused without losing local edits', t => {
  const { root, home } = fixture(t);
  const directory = path.join(root, 'source');
  fs.mkdirSync(directory);
  const git = (...args) => {
    const result = spawnSync('git', ['-C', directory, ...args], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    return result.stdout.trim();
  };
  git('init', '-q');
  fs.writeFileSync(path.join(directory, 'scene.txt'), 'committed');
  git('add', 'scene.txt');
  git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture');
  git('remote', 'add', 'origin', 'https://github.com/img2threejs/pixi2d.git');
  const before = git('rev-parse', 'HEAD');
  fs.writeFileSync(path.join(directory, 'scene.txt'), 'local edits');
  const result = invoke(home, ['update', '--yes', '--directory', directory], false);
  assert.equal(result.status, 2, result.stderr);
  assert.equal(git('rev-parse', 'HEAD'), before);
  assert.equal(fs.readFileSync(path.join(directory, 'scene.txt'), 'utf8'), 'local edits');
  unchanged(home);
});

test('a symlinked Python environment cannot mutate another workspace', t => {
  const { root, home } = fixture(t);
  const directory = path.join(root, 'source');
  const shared = path.join(root, 'shared-python');
  fs.mkdirSync(directory);
  fs.mkdirSync(shared);
  fs.writeFileSync(path.join(shared, 'keep'), 'shared environment');
  const git = (...args) => {
    const result = spawnSync('git', ['-C', directory, ...args], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
  };
  git('init', '-q');
  fs.writeFileSync(path.join(directory, '.gitignore'), '.venv\n');
  git('add', '.gitignore');
  git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'Fixture');
  git('remote', 'add', 'origin', 'https://github.com/img2threejs/pixi2d.git');
  fs.symlinkSync(shared, path.join(directory, '.venv'), 'dir');
  const before = spawnSync('git', ['-C', directory, 'status', '--porcelain'], { encoding: 'utf8' });
  assert.equal(before.status, 0, before.stderr);
  assert.equal(before.stdout, '');
  const result = invoke(home, ['update', '--yes', '--directory', directory], false);
  assert.equal(result.status, 2, result.stderr);
  assert.equal(fs.readFileSync(path.join(shared, 'keep'), 'utf8'), 'shared environment');
  assert.deepEqual(fs.readdirSync(shared), ['keep']);
  unchanged(home);
});
