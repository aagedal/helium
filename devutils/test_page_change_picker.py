#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Drive the shipped section picker with real pointer input through chromedriver.

The page is served with a strict CSP and Trusted Types so the overlay is
checked under the restrictions popular sites use. The scripts run in the main
world here; the browser runs them in an isolated world.
"""
import argparse
import base64
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re
import socket
import subprocess
import tempfile
import threading
import time
import urllib.request

from third_party.unidiff import PatchSet

ROOT = Path(__file__).resolve().parent
STRINGS = json.dumps({
    'hint': 'Drag across the part of the page to watch, or click a block of text.',
    'cancel': 'Cancel',
    'empty': 'There is no readable text there. Try a larger area.',
    'done': 'Watching this section for changes',
})


def production_scripts():
    """Extract the added production scripts without maintaining a test copy."""
    patch = PatchSet((ROOT.parent / 'patches/helium/ui/page-change-monitor.patch').read_text())
    header = next(file for file in patch if file.path.endswith('/page_change_monitor_script.h'))
    source = ''.join(line.value for hunk in header for line in hunk if line.is_added)
    return dict(re.findall(r'char (\w+)\[\] = R"JS\((.*?)\)JS"', source, re.S))


class Handler(SimpleHTTPRequestHandler):
    """Serve only the fixture, with a restrictive policy."""

    def do_GET(self): # pylint: disable=invalid-name
        """Serve the picker fixture."""
        data = (ROOT / 'page_change_picker_fixture.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Security-Policy',
                         "style-src 'none'; script-src 'none'; require-trusted-types-for 'script'")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args): # pylint: disable=arguments-differ
        pass


class Driver:
    """Minimal W3C WebDriver client."""

    def __init__(self, port, binary):
        self.base = f'http://127.0.0.1:{port}'
        profile = tempfile.mkdtemp(prefix='helium-picker-')
        options = {
            'binary': binary,
            'args': [
                '--headless=new', '--window-size=1000,800', '--user-data-dir=' + profile,
                '--no-first-run'
            ]
        }
        self.session = '/session/' + self.request(
            'POST', '/session', {'capabilities': {
                'alwaysMatch': {
                    'goog:chromeOptions': options
                }
            }})['sessionId']

    def request(self, method, path, body=None):
        """Send one WebDriver command."""
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(self.base + path,
                                         data=data,
                                         method=method,
                                         headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())['value']

    def command(self, method, path, body=None):
        """Send a session command."""
        return self.request(method, self.session + path, body)

    def run(self, script, *args):
        """Evaluate a script body."""
        return self.command('POST', '/execute/sync', {'script': script, 'args': list(args)})

    def pointer(self, actions):
        """Perform mouse actions; button state persists between calls."""
        self.command(
            'POST', '/actions', {
                'actions': [{
                    'type': 'pointer',
                    'id': 'mouse',
                    'parameters': {
                        'pointerType': 'mouse'
                    },
                    'actions': actions
                }]
            })

    def key(self, value):
        """Press and release one key."""
        self.command(
            'POST', '/actions', {
                'actions': [{
                    'type': 'key',
                    'id': 'keyboard',
                    'actions': [{
                        'type': 'keyDown',
                        'value': value
                    }, {
                        'type': 'keyUp',
                        'value': value
                    }]
                }]
            })

    def screenshot(self, path):
        """Save a PNG screenshot."""
        Path(path).write_bytes(base64.b64decode(self.command('GET', '/screenshot')))


def move(left, top, duration=0):
    """Pointer move in viewport coordinates."""
    return {
        'type': 'pointerMove',
        'x': int(left),
        'y': int(top),
        'origin': 'viewport',
        'duration': duration
    }


DOWN, UP = {'type': 'pointerDown', 'button': 0}, {'type': 'pointerUp', 'button': 0}
ESCAPE = '\ue00c'


class PickerChecks:
    """Pointer and keyboard scenarios for the section picker."""

    def __init__(self, driver, url, scripts, screenshots):
        self.driver, self.url, self.scripts = driver, url, scripts
        self.screenshots = Path(screenshots) if screenshots else None
        self.scan = '(' + scripts['kPageChangeMonitorScript'] + ')'
        self.failures = 0
        self.base = 0

    def check(self, name, condition, detail=''):
        """Report one result."""
        print(('PASS ' if condition else 'FAIL ') + name, '' if condition else detail)
        self.failures += not condition

    def inject(self):
        """Start the picker on the current page."""
        self.driver.run('return (' + self.scripts['kPageChangeMonitorPickerScript'] + ')(' +
                        self.scan + ',' + STRINGS + ')')

    def start(self):
        """Load the fixture and start a picker."""
        self.driver.command('POST', '/url', {'url': self.url})
        self.base = self.driver.run('return document.body.children.length')
        self.inject()

    def poll(self):
        """Read the picker state the way the browser does."""
        return self.driver.run('return (' + self.scripts['kPageChangeMonitorPollScript'] + ')')

    def rect(self, selector):
        """Viewport rectangle of an element."""
        return self.driver.run(
            'const r = document.querySelector(arguments[0]).getBoundingClientRect();'
            'return [r.left, r.top, r.right, r.bottom]', selector)

    def overlay_gone(self):
        """Whether the page is back to its original children."""
        return self.driver.run('return document.body.children.length') == self.base

    def capture(self, name):
        """Save a screenshot when requested."""
        if self.screenshots:
            time.sleep(0.2)
            self.driver.screenshot(self.screenshots / name)

    def drag(self, box, inset):
        """Drag across a rectangle, inset from its edges."""
        self.driver.pointer([
            move(box[0] + inset, box[1] + inset), DOWN,
            move(box[2] - inset, box[3] - inset, 100), UP
        ])

    def two_paragraphs(self):
        """A drag across part of an article watches only the touched blocks."""
        self.start()
        first, second = self.rect('#p1'), self.rect('#p2')
        self.driver.pointer(
            [move(first[0] + 5, first[1] + 3), DOWN,
             move(first[0] + 300, second[3] - 3, 150)])
        self.capture('picker-drag.png')
        self.driver.pointer([UP])
        result = self.poll()
        self.check('Dragging over two paragraphs watches only those',
                   result.get('selector') == '#p1,#p2', result)
        text = self.driver.run('return ' + self.scan + '(arguments[0])', result.get('selector',
                                                                                    '')).get('text')
        self.check(
            'Both picked paragraphs are read in order',
            text == 'The meeting will be on Wednesday.\nResidents may submit questions in advance.')
        time.sleep(1.1)
        self.check('Overlay removes itself after a choice', self.overlay_gone())

    def blocks(self):
        """Clicks and drags snap to sensible blocks."""
        self.start()
        box = self.rect('#p2')
        self.driver.pointer([move(box[0] + 20, box[1] + 8)])
        self.capture('picker-hover.png')
        self.driver.pointer([DOWN, UP])
        self.check('Clicking picks the block under the pointer',
                   self.poll().get('selector') == '#p2')
        self.start()
        self.drag(self.rect('#story'), 2)
        self.check('Dragging over everything picks the shared block',
                   self.poll().get('selector') == '#story')
        self.start()
        self.drag(self.rect('#box'), 4)
        self.check('Dragging inside a card picks the card', self.poll().get('selector') == '#box')

    def empty_and_cancel(self):
        """Empty areas keep the picker open; Escape and the browser close it."""
        self.start()
        box = self.rect('#empty')
        self.driver.pointer([move(box[0] + 4, box[1] + 4), DOWN, UP])
        self.check('An empty box keeps the picker open', self.poll().get('state') == 'picking')
        self.driver.pointer([move(8, 400), DOWN, UP])
        self.check('The page margin keeps the picker open', self.poll().get('state') == 'picking')
        self.driver.key(ESCAPE)
        self.check('Escape cancels', self.poll().get('state') == 'cancelled')
        self.check('Overlay is removed after cancelling', self.overlay_gone())
        self.check('A finished picker is gone', self.poll().get('state') == 'gone')
        self.start()
        self.driver.run('return (' + self.scripts['kPageChangeMonitorCancelScript'] + ')')
        self.check('The browser can remove the overlay', self.overlay_gone())
        self.start()
        self.inject()
        self.check('Restarting replaces the existing overlay',
                   self.driver.run('return document.body.children.length') == self.base + 1)

    def run(self):
        """Run every scenario and return the number of failures."""
        self.two_paragraphs()
        self.blocks()
        self.empty_and_cancel()
        return self.failures


def main():
    """Start the fixture server and chromedriver, then run the checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chromedriver', required=True, type=Path)
    parser.add_argument('--binary', required=True, help='Browser executable')
    parser.add_argument('--screenshots', help='Folder for overlay screenshots')
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    with subprocess.Popen([str(args.chromedriver), f'--port={port}'],
                          stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL) as driver_process:
        try:
            time.sleep(1.5)
            driver = Driver(port, args.binary)
            try:
                failures = PickerChecks(driver, f'http://127.0.0.1:{server.server_address[1]}/',
                                        production_scripts(), args.screenshots).run()
            finally:
                driver.command('DELETE', '')
        finally:
            driver_process.terminate()
            server.shutdown()
    if failures:
        raise SystemExit(f'{failures} picker check(s) failed')
    print('PASS: all section picker checks')


if __name__ == '__main__':
    main()
