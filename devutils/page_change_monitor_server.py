#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Serve change-monitor fixtures using the exact script shipped in the fork patch."""
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from third_party.unidiff import PatchSet

ROOT = Path(__file__).resolve().parent


def production_script():
    """Extract the added production header without maintaining a test copy."""
    patch = PatchSet((ROOT.parent / 'patches/helium/ui/page-change-monitor.patch').read_text())
    header = next(file for file in patch if file.path.endswith('/page_change_monitor_script.h'))
    source = ''.join(line.value for hunk in header for line in hunk if line.is_added)
    return source.split('R"JS(', 1)[1].split(')JS"', 1)[0]


class Handler(BaseHTTPRequestHandler):
    """Serve only controlled fixtures and the production extraction script."""
    changed = False

    def do_POST(self): # pylint: disable=invalid-name
        """Toggle only the controlled statement used for reload/export QA."""
        if self.path != '/change':
            self.send_error(404)
            return
        Handler.changed = not Handler.changed
        self.send_response(204)
        self.end_headers()

    def do_GET(self): # pylint: disable=invalid-name
        """Serve a fixture, production script, or an explicit 404."""
        if self.path.split('?', 1)[0] == '/monitor.js':
            data = ('window.monitorText = ' + production_script() + ';').encode()
            mime = 'text/javascript; charset=utf-8'
        elif self.path.split('?', 1)[0] == '/':
            data = (ROOT / 'page_change_monitor_fixtures.html').read_text()
            if Handler.changed:
                data = data.replace('The meeting will be on Wednesday.',
                                    'The meeting has moved to Thursday.')
            data = data.encode()
            mime = 'text/html; charset=utf-8'
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)


def main():
    """Start the local-only test server."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8240)
    args = parser.parse_args()
    print(f'Change monitoring fixtures: http://127.0.0.1:{args.port}/', flush=True)
    HTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
