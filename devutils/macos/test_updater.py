#!/usr/bin/env python3
"""Exercise the real browser updater against isolated localhost feeds.

Use a disposable signed app with a lower CFBundleVersion for download tests.
All browser profiles and update endpoints are isolated from production.
"""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import plistlib
import socket
import subprocess
import tempfile
import threading
import time
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from make_appcast import SPARKLE


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def webdriver(base, method, path, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    request = Request(base + path, data=data, method=method,
                      headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=120) as response:
        result = json.load(response)['value']
    if isinstance(result, dict) and 'error' in result:
        raise RuntimeError(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--chromedriver', type=Path, required=True)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--scenario', choices=['current', 'feed-fallback', 'download-fallback', 'both-down', 'bad-signature', 'disabled'], required=True)
    args = parser.parse_args()
    manifest = json.loads((args.release / 'update-manifest.json').read_text())
    archive = args.release / manifest['installer']
    requests = []
    http_port = free_port()
    origin = 'http://127.0.0.1:' + str(http_port)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *unused):
            pass

        def do_GET(self):
            path = self.path.split('?')[0]
            requests.append(path)
            primary = path.startswith('/primary/')
            if args.scenario == 'both-down' or (primary and args.scenario == 'feed-fallback'):
                self.send_error(503)
                return
            if path.endswith('/helium-neo.xml'):
                root = ET.parse(args.release / 'helium-neo.xml').getroot()
                item = root.find('./channel/item')
                enclosure = item.find('enclosure')
                enclosure.set('url', origin + ('/missing.dmg' if primary and args.scenario == 'download-fallback' else '/installer.dmg'))
                if args.scenario == 'bad-signature':
                    enclosure.set(f'{{{SPARKLE}}}edSignature', 'A' * 86 + '==')
                data = ET.tostring(root, encoding='utf-8', xml_declaration=True)
                self.send_response(200)
                self.send_header('Content-Type', 'application/rss+xml')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            elif path == '/installer.dmg':
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', str(archive.stat().st_size))
                self.end_headers()
                try:
                    with archive.open('rb') as stream:
                        while block := stream.read(1024 * 1024):
                            self.wfile.write(block)
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self.send_error(404)

    server = ThreadingHTTPServer(('127.0.0.1', http_port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    results = {}
    succeeded = False
    try:
        with tempfile.TemporaryDirectory(prefix='neo-updater-test-') as temporary:
            root = Path(temporary)
            test_app = root / args.app.name
            subprocess.run(['ditto', str(args.app), str(test_app)], check=True)
            needs_update = args.scenario in ('feed-fallback', 'download-fallback', 'bad-signature')
            if needs_update:
                info_path = test_app / 'Contents/Info.plist'
                with info_path.open('rb') as stream:
                    info = plistlib.load(stream)
                parts = manifest['build'].split('.')
                parts[-1] = str(int(parts[-1]) - 1)
                info['CFBundleVersion'] = '.'.join(parts)
                with info_path.open('wb') as stream:
                    plistlib.dump(info, stream)
                subprocess.run(['codesign', '--force', '--timestamp', '--sign', args.identity,
                                '--options', 'restrict,kill,library,runtime', '--entitlements',
                                str(args.source / 'chrome/app/app-entitlements.plist'), str(test_app)], check=True)
            profile = root / 'profile'
            (profile / 'Default').mkdir(parents=True)
            (profile / 'Default/Preferences').write_text(json.dumps({
                'helium': {'completed_onboarding': True, 'services': {
                    'enabled': True, 'user_consented': True, 'schema_version': 999,
                    'browser_updates': args.scenario != 'disabled',
                    'ext_proxy': False, 'bangs': False, 'spellcheck_files': False,
                    'ublock_assets': False,
                }},
            }))
            port = free_port()
            base = 'http://127.0.0.1:' + str(port)
            with (args.report.with_suffix('.driver.log')).open('w') as log:
                driver = subprocess.Popen([str(args.chromedriver), '--port=' + str(port)], stdout=log, stderr=log)
                session = None
                try:
                    for attempt in range(100):
                        try:
                            webdriver(base, 'GET', '/status')
                            break
                        except OSError:
                            time.sleep(.1)
                    session = webdriver(base, 'POST', '/session', {'capabilities': {'alwaysMatch': {
                        'browserName': 'chrome', 'goog:chromeOptions': {
                            'binary': str(test_app / 'Contents/MacOS/Helium Neo'),
                            'args': ['--headless', '--no-first-run', '--no-default-browser-check',
                                     '--use-mock-keychain', '--user-data-dir=' + str(profile),
                                     '--custom-update-server-url=' + origin + '/primary/',
                                     '--custom-update-fallback-url=' + origin + '/backup/'],
                        },
                    }}})['sessionId']
                    route = '/session/' + session
                    webdriver(base, 'POST', route + '/url', {'url': 'chrome://settings/help'})
                    webdriver(base, 'POST', route + '/execute/async', {'script': '''
                        const done = arguments[arguments.length - 1];
                        import('chrome://resources/js/cr.js').then(({addWebUiListener}) => {
                          window.neoUpdateStatuses = [];
                          addWebUiListener('update-status-changed', e => window.neoUpdateStatuses.push(e));
                          chrome.send('refreshUpdateStatus'); done(true);
                        }).catch(e => done(String(e)));
                    ''', 'args': []})
                    expected = {'current': 'updated', 'feed-fallback': 'nearly_updated',
                                'download-fallback': 'nearly_updated', 'both-down': 'failed',
                                'bad-signature': 'failed', 'disabled': 'disabled'}[args.scenario]
                    deadline = time.monotonic() + 150
                    while time.monotonic() < deadline:
                        statuses = webdriver(base, 'POST', route + '/execute/sync', {
                            'script': 'return window.neoUpdateStatuses || []', 'args': []})
                        if any(s.get('status') == expected for s in statuses):
                            break
                        time.sleep(.5)
                    else:
                        raise AssertionError('Expected ' + expected + '; got ' + repr(statuses) + '; requests ' + repr(requests))
                    if args.scenario in ('feed-fallback', 'download-fallback', 'both-down'):
                        assert 1 <= requests.count('/backup/helium-neo.xml') <= requests.count('/primary/helium-neo.xml'), requests
                    else:
                        assert '/backup/helium-neo.xml' not in requests, requests
                    if args.scenario == 'disabled':
                        assert not requests, requests
                    results = {'scenario': args.scenario, 'passed': True,
                               'requests': list(requests), 'statuses': statuses}
                finally:
                    if session:
                        try:
                            webdriver(base, 'DELETE', '/session/' + session)
                        except OSError:
                            pass
                    driver.terminate()
                    driver.wait(timeout=20)
                if args.scenario in ('feed-fallback', 'download-fallback'):
                    deadline = time.monotonic() + 60
                    while time.monotonic() < deadline:
                        try:
                            with (test_app / 'Contents/Info.plist').open('rb') as stream:
                                installed = plistlib.load(stream)['CFBundleVersion']
                            if installed == manifest['build']:
                                break
                        except FileNotFoundError:
                            pass
                        time.sleep(.5)
                    else:
                        raise AssertionError('Downloaded update was not installed on quit')
                    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(test_app)], check=True)
                    results['installed_build'] = installed
                    results['installed_signature_valid'] = True
                succeeded = True
    finally:
        server.shutdown()
        results['passed'] = succeeded
        args.report.write_text(json.dumps(results or {'scenario': args.scenario, 'passed': False, 'requests': requests}, indent=2) + '\n')
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
