#!/usr/bin/env python3
"""Verify standalone dependencies, signatures and JavaScript execution."""

import argparse
import json
from pathlib import Path
import plistlib
import subprocess
import tempfile


def output(*arguments):
    """Run a verification command and return its combined output."""
    return subprocess.check_output([str(arg) for arg in arguments],
                                   text=True,
                                   stderr=subprocess.STDOUT)


def verify(app): # pylint: disable=too-many-locals,too-many-branches
    """Reject external dependencies and missing architecture slices."""
    with (app / 'Contents/Info.plist').open('rb') as stream:
        info = plistlib.load(stream)
    assert info['CFBundleIdentifier'] == 'no.aagedal.helium-neo'
    binaries = []
    total = 0
    for path in app.rglob('*'):
        if path.is_symlink():
            assert path.resolve().is_relative_to(app), f'External symlink: {path}'
            continue
        if not path.is_file():
            continue
        total += path.stat().st_size
        with path.open('rb') as stream:
            magic = stream.read(4)
        if magic == b'\xcf\xfa\xed\xfe':
            binaries.append(path)
    assert binaries, 'No Mach-O binaries'
    for path in binaries:
        dependencies = output('otool', '-m', '-L', path)
        install_ids = set(output('otool', '-m', '-D', path).splitlines()[1:])
        commands = '\n'.join(output('otool', '-m', '-l', path).splitlines()[1:])
        load_commands = '\n'.join(dependencies.splitlines()[1:]) + '\n' + commands
        assert '/Users/' not in load_commands, f'Development path in {path}'
        assert '/private/tmp/' not in load_commands, f'Temporary dependency in {path}'
        assert output('lipo', '-archs', path).strip() == 'arm64', path
        for line in dependencies.splitlines()[1:]:
            dependency = line.strip().split(' (compatibility version')[0]
            if dependency in install_ids or dependency.startswith(
                ('/System/Library/', '/usr/lib/')):
                continue
            if dependency.startswith('@rpath/'):
                relative = dependency[len('@rpath/'):]
                assert any(str(candidate).endswith('/' + relative)
                           for candidate in binaries), dependency
            elif dependency.startswith('@loader_path/'):
                assert (path.parent /
                        dependency[len('@loader_path/'):]).resolve().is_file(), dependency
            elif not dependency.startswith('@executable_path/'):
                raise AssertionError(f'External dependency {dependency}')
    output('codesign', '--verify', '--deep', '--strict', app)
    return info, total, binaries


def main():
    """Verify an app and write a machine-readable release report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('app', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    app = args.app.resolve()
    info, total, binaries = verify(app)
    with tempfile.TemporaryDirectory(prefix='helium-neo-smoke-') as profile:
        page = ('data:text/html,<title>Helium Neo</title><body><script>'
                'let n=0;for(let i=0;i<1000000;i++)n+=i%7;'
                'document.body.textContent="NEO_JAVASCRIPT_"+n</script></body>')
        result = subprocess.run([
            str(app / 'Contents/MacOS/Helium Neo'),
            '--headless',
            '--no-first-run',
            '--no-default-browser-check',
            '--use-mock-keychain',
            '--disable-features=DialMediaRouteProvider',
            '--user-data-dir=' + profile,
            '--dump-dom',
            page,
        ],
                                capture_output=True,
                                text=True,
                                timeout=90,
                                check=False)
        args.report.with_suffix('.stdout').write_text(result.stdout, encoding='utf-8')
        args.report.with_suffix('.stderr').write_text(result.stderr, encoding='utf-8')
        assert result.returncode == 0 and 'NEO_JAVASCRIPT_2999997' in result.stdout
    report = {
        'bundle_id': info['CFBundleIdentifier'],
        'version': info['CFBundleShortVersionString'],
        'update_build': info['CFBundleVersion'],
        'architecture': 'arm64',
        'app_bytes': total,
        'mach_o_files': len(binaries),
        'external_build_paths': False,
        'signature_verified': True,
        'standalone_javascript_smoke': True,
    }
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
