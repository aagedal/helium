#!/usr/bin/env python3
"""Generate primary and mirror Sparkle feeds for the same signed installer."""

import argparse
import base64
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote
import xml.etree.ElementTree as ET

SPARKLE = 'http://www.andymatuschak.org/xml-namespaces/sparkle'
ET.register_namespace('sparkle', SPARKLE)


def make_feed(config, archive, signature, download_url, published):
    """Both feeds describe identical bytes, differing only in download location."""
    root = ET.Element('rss', version='2.0')
    channel = ET.SubElement(root, 'channel')
    ET.SubElement(channel, 'title').text = 'Helium Neo'
    ET.SubElement(channel, 'link').text = 'https://github.com/aagedal/helium'
    ET.SubElement(channel, 'description').text = 'Helium Neo stable macOS updates'
    item = ET.SubElement(channel, 'item')
    ET.SubElement(item, 'title').text = 'Helium Neo ' + config['version']
    ET.SubElement(item, 'pubDate').text = published
    ET.SubElement(item, f'{{{SPARKLE}}}version').text = config['build']
    ET.SubElement(item, f'{{{SPARKLE}}}shortVersionString').text = config['version']
    ET.SubElement(item, f'{{{SPARKLE}}}minimumSystemVersion').text = config['minimum_macos']
    ET.SubElement(item, f'{{{SPARKLE}}}hardwareRequirements').text = 'arm64'
    ET.SubElement(
        item, 'enclosure', {
            'url': download_url,
            'length': str(archive.stat().st_size),
            'type': 'application/octet-stream',
            f'{{{SPARKLE}}}edSignature': signature,
        })
    ET.indent(root)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def sha256_stream(stream):
    """Hash a file or HTTP response without loading it into memory."""
    digest = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        digest.update(block)
    return digest.hexdigest()


def main():
    """Sign an installer and write both appcasts and their integrity manifest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--sparkle-tools', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('release.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if not re.fullmatch(r'\d+(?:\.\d+)*', config['build']):
        parser.error('Updater build must contain increasing numeric components')
    signer = args.sparkle_tools / 'bin/sign_update'
    public_key = subprocess.check_output([
        str(args.sparkle_tools / 'bin/generate_keys'),
        '--account',
        config['sparkle_keychain_account'],
        '-p',
    ],
                                         text=True).strip()
    if public_key != config['sparkle_public_key']:
        parser.error('Keychain signing key does not match the public key embedded in Neo')
    signed = subprocess.check_output([
        str(signer),
        '--account',
        config['sparkle_keychain_account'],
        str(args.archive),
    ],
                                     text=True)
    # Parse the tool's XML fragment with the Sparkle namespace in scope.
    attrs = ET.fromstring('<enclosure xmlns:sparkle="' + SPARKLE + '" ' + signed.strip() + '/>')
    signature = attrs.attrib[f'{{{SPARKLE}}}edSignature']
    if len(base64.b64decode(signature, validate=True)) != 64:
        parser.error('Invalid Ed25519 signature')
    if int(attrs.attrib['length']) != args.archive.stat().st_size:
        parser.error('Signing tool returned an unexpected archive length')
    subprocess.run([
        str(signer), '--account', config['sparkle_keychain_account'], '--verify',
        str(args.archive), signature
    ],
                   check=True)
    args.output.mkdir(parents=True, exist_ok=True)
    published = format_datetime(datetime.now(timezone.utc))
    filename = quote(args.archive.name)
    primary_url = 'https://github.com/aagedal/helium/releases/download/' + config[
        'tag'] + '/' + filename
    backup_url = config['backup_download_base'] + filename
    (args.output / 'helium-neo.xml').write_bytes(
        make_feed(config, args.archive, signature, primary_url, published))
    (args.output / 'helium-neo-backup.xml').write_bytes(
        make_feed(config, args.archive, signature, backup_url, published))
    with args.archive.open('rb') as stream:
        digest = sha256_stream(stream)
    (args.output / 'SHA256SUMS').write_text(digest + '  ' + args.archive.name + '\n')
    (args.output / 'update-manifest.json').write_text(
        json.dumps(
            {
                **config,
                'installer': args.archive.name,
                'bytes': args.archive.stat().st_size,
                'sha256': digest,
                'ed_signature': signature,
                'primary_download': primary_url,
                'backup_download': backup_url,
                'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                         cwd=Path(__file__).resolve().parents[2],
                                                         text=True).strip(),
            },
            indent=2) + '\n')


if __name__ == '__main__':
    main()
