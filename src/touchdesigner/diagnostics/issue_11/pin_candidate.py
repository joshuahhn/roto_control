"""Freeze the scoped #11 delta and assembled source tree, including new files.

Uses a temporary index, never the real index/worktree/commit/stash.
Run from the bound #11 checkout. Prints the immutable manifest location.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

COMMON = '61d0e03fc454dba496618fdf33ab4a5169437b19'
BASE = '55ef1a5febecb6c4f2428e49e899e15d5c030fd8'
REVIEW_BASE = 'bc3566b2f60fb1c8c7c08ca2c720f3bd200d4f13'


def git(root, *args, codes=(0,), env=None):
    result = subprocess.run(['git', '-C', str(root), *args], capture_output=True, env=env)
    if result.returncode not in codes:
        raise RuntimeError(result.stderr.decode())
    return result.stdout


def pin():
    root = Path(__file__).resolve().parents[4]
    if git(root, 'rev-parse', 'HEAD').decode().strip() != COMMON:
        raise ValueError('Keep the original common commit; accepted dependency is a tree')
    tracked = git(root, 'diff', '--name-only', COMMON).decode().splitlines()
    new = git(root, 'ls-files', '--others', '--exclude-standard').decode().splitlines()
    paths = sorted(set(tracked + new))
    if not paths or any(not p.startswith('src/touchdesigner/') or Path(p).suffix not in ('.py', '.md', '.json') for p in paths):
        raise ValueError('Only scoped TouchDesigner source/evidence may enter this candidate')
    destination = Path(tempfile.mkdtemp(prefix='roto-issue11-candidate-'))
    with tempfile.TemporaryDirectory(prefix='roto-issue11-index-') as temporary:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / 'index'))
        git(root, 'read-tree', BASE, env=env)
        git(root, 'add', '--', *paths, env=env)
        tree = git(root, 'write-tree', env=env).decode().strip()
    paths = git(root, 'diff', '--name-only', BASE, tree).decode().splitlines()
    allowed = {'src/touchdesigner/code/py/roto_python/RotoPythonExt.py',
               'src/touchdesigner/upgrade_layouts.py',
               'src/touchdesigner/code/py/roto_python/layout_migration.py',
               'src/touchdesigner/test_comp_layout_migration.py',
               'src/touchdesigner/docs/plans/issue-11-comp-migration.md'}
    if any(p not in allowed and not p.startswith('src/touchdesigner/diagnostics/issue_11/') for p in paths):
        raise ValueError('Accepted dependency differs outside the scoped #11 delta')
    patch = git(root, 'diff', '--binary', BASE, tree)
    git(root, 'diff', '--check', BASE, tree)
    (destination / 'candidate.patch').write_bytes(patch)
    correction = git(root, 'diff', '--binary', REVIEW_BASE, tree)
    (destination / 'nativeimport-correction.patch').write_bytes(correction)
    overlay = destination / 'files'; overlay.mkdir()
    manifest = []
    for path in paths:
        data = (root / path).read_bytes()
        target = overlay / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        manifest.append(dict(path=path, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    # Complete assembled TD source for the native helper's __file__ paths.
    archive = git(root, 'archive', '--format=tar.gz', tree, 'src/touchdesigner')
    (destination / 'source.tar.gz').write_bytes(archive)
    source_build_dat = {path: hashlib.sha256(git(root, 'show', tree + ':' + path)).hexdigest()
                       for path in ('src/touchdesigner/upgrade_layouts.py',
                                    'src/touchdesigner/code/py/roto_python/RotoPythonExt.py',
                                    'src/touchdesigner/code/py/roto_python/layouts.py',
                                    'src/touchdesigner/code/py/roto_python/layout_migration.py',
                                    'src/touchdesigner/code/py/roto_python/protocol.py',
                                    'src/touchdesigner/diagnostics/issue_11/native_migration_fixture.py')}
    metadata = dict(base_tree=BASE, common_commit=COMMON, review_base_tree=REVIEW_BASE, candidate_tree=tree,
                    patch_sha256=hashlib.sha256(patch).hexdigest(), files=manifest,
                    correction_patch_sha256=hashlib.sha256(correction).hexdigest(),
                    source_build_dat_sha256=source_build_dat,
                    source_archive_sha256=hashlib.sha256(archive).hexdigest(),
                    runtime_tests=359, inspector_tests=223, diff_check=True,
                    native=False, physical=False)
    (destination / 'manifest.json').write_text(json.dumps(metadata, indent=2) + '\n')
    # Mirrors contain immutable review inputs; later fixes get a new candidate.
    for path in overlay.rglob('*'):
        if path.is_file(): path.chmod(0o444)
    (destination / 'candidate.patch').chmod(0o444)
    (destination / 'manifest.json').chmod(0o444)
    (destination / 'source.tar.gz').chmod(0o444)
    (destination / 'nativeimport-correction.patch').chmod(0o444)
    print(json.dumps(dict(candidate=str(destination), **metadata), indent=2))


if __name__ == '__main__':
    pin()
