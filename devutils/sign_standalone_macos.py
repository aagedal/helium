#!/usr/bin/env python3
"""Developer ID sign a relocated component app using Chromium's entitlements.

Run outside a sandbox that hides signing identities. Notarization is a separate
step. This modifies the specified app, never the original build cache.
"""

import argparse
from pathlib import Path
import struct
import subprocess

from package_standalone_macos import macho


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--source-tree', type=Path, required=True)
    parser.add_argument('--identity', required=True)
    args = parser.parse_args()
    app = args.app.resolve()
    entitlements = args.source_tree.resolve() / 'chrome/app'
    if not app.is_dir() or app.suffix != '.app':
        parser.error('Expected an existing standalone .app bundle')
    for name in ('app', 'helper-renderer', 'helper-gpu'):
        if not (entitlements / f'{name}-entitlements.plist').is_file():
            parser.error(f'Missing {name} entitlements')

    def sign(path, options=None, entitlement=None):
        command = ['codesign', '--force', '--sign', args.identity, '--timestamp']
        if options:
            command += ['--options', options]
        if entitlement:
            command += ['--entitlements', str(entitlement)]
        subprocess.run(command + [str(path)], check=True)

    full_options = 'restrict,kill,library,runtime'
    for path in app.rglob('*'):
        if path.is_file() and not path.is_symlink() and macho(path):
            with path.open('rb') as stream:
                executable = struct.unpack_from('<I', stream.read(16), 12)[0] == 2
            sign(path, full_options if executable else None)

    bundles = [path for path in app.rglob('*')
               if path.is_dir() and path.suffix in ('.app', '.framework')]
    for bundle in sorted(bundles, key=lambda path: len(path.parts), reverse=True):
        if bundle.suffix == '.framework':
            sign(bundle)
        elif 'Renderer)' in bundle.name or 'GPU)' in bundle.name:
            name = 'helper-renderer' if 'Renderer)' in bundle.name else 'helper-gpu'
            sign(bundle, 'restrict,kill,runtime',
                 entitlements / f'{name}-entitlements.plist')
        else:
            sign(bundle, full_options)
    sign(app, full_options, entitlements / 'app-entitlements.plist')
    subprocess.run(['codesign', '--verify', '--deep', '--strict', '--verbose=2',
                    str(app)], check=True)
    subprocess.run(['codesign', '--display', '--verbose=4', str(app)], check=True)


if __name__ == '__main__':
    main()
