#!/usr/bin/env python3
"""Apply Neo updater patches to an already prepared macOS release source tree."""

import argparse
import json
from pathlib import Path
import re
import subprocess


def main():
    """Apply missing updater changes without resetting prepared source or outputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build-output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    config = json.loads(Path(__file__).with_name('release.json').read_text(encoding='utf-8'))
    args_file = args.build_output / 'args.gn'
    gn_args = args_file.read_text(encoding='utf-8')
    for name in ('is_component_build=false', 'is_official_build=true'):
        if name not in gn_args.replace(' ', ''):
            parser.error('Use an existing official standalone release output: ' + name)
    for patch in (root / 'patches/helium/core/neo-update-feeds.patch',
                  Path(__file__).with_name('neo-sparkle-fallback.patch')):
        reverse = subprocess.run(['git', 'apply', '--reverse', '--check',
                                  str(patch)],
                                 cwd=args.source,
                                 capture_output=True,
                                 check=False)
        if reverse.returncode == 0:
            print('Already applied:', patch.name)
            continue
        subprocess.run(['git', 'apply', '--check', str(patch)], cwd=args.source, check=True)
        subprocess.run(['git', 'apply', str(patch)], cwd=args.source, check=True)
    for name, value in [('enable_sparkle', 'true'),
                        ('sparkle_ed_key', json.dumps(config['sparkle_public_key']))]:
        gn_args = re.sub(r'^\s*' + name + r'\s*=.*\n?', '', gn_args, flags=re.MULTILINE)
        gn_args += '\n' + name + '=' + value + '\n'
    args_file.write_text(gn_args)
    print('Updater enabled in release output; development output untouched.')


if __name__ == '__main__':
    main()
