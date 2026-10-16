#!/usr/bin/env python3
"""Stage, Developer ID sign, notarize and create a Neo stable DMG.

Uses an existing official non-component output; never resets or prepares sources.
Requires Sparkle's official distribution for sign_update and generate_keys.
"""

import argparse
import json
from pathlib import Path
import plistlib
import shutil
import subprocess


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def is_macho(path):
    with path.open('rb') as stream:
        return stream.read(4) in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xca\xfe\xba\xbf')


def sign_app(app, source, identity):
    """Sign inside out, including Sparkle's embedded installer application."""
    def sign(path, options=None, entitlement=None):
        args = ['codesign', '--force', '--sign', identity, '--timestamp']
        if options:
            args += ['--options', options]
        if entitlement:
            args += ['--entitlements', str(entitlement)]
        run(*args, path)

    for path in app.rglob('*'):
        if path.is_file() and not path.is_symlink() and is_macho(path):
            architectures = subprocess.check_output(['lipo', '-archs', str(path)], text=True).split()
            if 'arm64' not in architectures:
                raise RuntimeError('Missing arm64 slice: ' + str(path))
            if architectures != ['arm64']:
                # Only thin the staging copy, preserving the build output.
                run('lipo', path, '-thin', 'arm64', '-output', path)
            sign(path, 'runtime')
    bundles = [p for p in app.rglob('*') if not p.is_symlink() and p.is_dir()
               and p.suffix in ('.app', '.framework', '.xpc')]
    for bundle in sorted(bundles, key=lambda p: len(p.parts), reverse=True):
        entitlement = None
        if 'Renderer)' in bundle.name or 'GPU)' in bundle.name:
            kind = 'helper-renderer' if 'Renderer)' in bundle.name else 'helper-gpu'
            entitlement = source / 'chrome/app' / (kind + '-entitlements.plist')
        sign(bundle, 'runtime' if bundle.suffix != '.framework' else None, entitlement)
    sign(app, 'restrict,kill,library,runtime', source / 'chrome/app/app-entitlements.plist')
    run('codesign', '--verify', '--deep', '--strict', '--verbose=2', app)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--build-output', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--notary-profile', default='notary')
    parser.add_argument('--sparkle-tools', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('release.json'))
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    gn_args = (args.build_output / 'args.gn').read_text().replace(' ', '')
    for required in ('is_component_build=false', 'is_official_build=true', 'enable_sparkle=true'):
        if required not in gn_args:
            parser.error('Release output must include ' + required)
    stage = args.output / 'standalone'
    if stage.exists():
        parser.error('Staging already exists; inspect it before trying again')
    args.output.mkdir(parents=True, exist_ok=True)
    stage.mkdir()
    app = stage / 'Helium Neo.app'
    run('ditto', args.build_output / app.name, app)
    plist_path = app / 'Contents/Info.plist'
    with plist_path.open('rb') as stream:
        info = plistlib.load(stream)
    if info['CFBundleIdentifier'] != 'no.aagedal.helium-neo':
        parser.error('Unexpected bundle identifier')
    if info['CFBundleShortVersionString'] != config['version']:
        parser.error('Release display version does not match the build')
    if info.get('SUPublicEDKey') != config['sparkle_public_key']:
        parser.error('Build does not contain the Neo update key')
    info.update(CFBundleVersion=config['build'], SUFeedURL=config['primary_feed'],
                SUEnableAutomaticChecks=True, SUAutomaticallyUpdate=True,
                SUVerifyUpdateBeforeExtraction=True, SUScheduledCheckInterval=86400,
                SUSendProfileInfo=False)
    with plist_path.open('wb') as stream:
        plistlib.dump(info, stream)
    versions = app / 'Contents/Frameworks/Helium Neo Framework.framework/Versions'
    current = (versions / 'Current').resolve()
    for path in versions.iterdir():
        if path.is_dir() and not path.is_symlink() and path != current:
            shutil.rmtree(path)
    sign_app(app, args.source, args.identity)
    (stage / 'Applications').symlink_to('/Applications')
    filename = 'Helium-Neo-' + config['version'] + '-macOS-arm64-signed.dmg'
    dmg = args.output / filename
    run('hdiutil', 'create', '-volname', 'Helium Neo', '-srcfolder', stage, '-format', 'ULMO', dmg)
    run('codesign', '--force', '--timestamp', '--sign', args.identity,
        '--identifier', 'no.aagedal.helium-neo.installer', dmg)
    result = subprocess.check_output(['xcrun', 'notarytool', 'submit', str(dmg),
                                     '--keychain-profile', args.notary_profile,
                                     '--wait', '--output-format', 'json'], text=True)
    (args.output / 'notarization-result.json').write_text(result)
    if json.loads(result).get('status') != 'Accepted':
        raise RuntimeError('Notarization did not accept the installer')
    run('xcrun', 'stapler', 'staple', dmg)
    run('xcrun', 'stapler', 'validate', dmg)
    run('codesign', '--verify', '--strict', dmg)
    run('spctl', '--assess', '--type', 'open', '--context', 'context:primary-signature', '--verbose=2', dmg)
    run('python3', Path(__file__).with_name('make_appcast.py'), dmg,
        '--sparkle-tools', args.sparkle_tools, '--config', args.config, '--output', args.output)
    run('python3', Path(__file__).with_name('deploy_mirror.py'), args.output, '--validate-only')


if __name__ == '__main__':
    main()
