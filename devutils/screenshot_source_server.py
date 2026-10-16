#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Serve real-DOM screenshot permalink fixtures using the production script.

Open http://127.0.0.1:8232/ and inspect runScreenshotSourceTests(). Uses the script
from the fork patch, so the checks do not need a Chromium build or social login.
"""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


def main():
    """Serve fixture HTML and the current production JavaScript."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8232)
    args = parser.parse_args()

    def production_script():
        """Extract the self-contained scripts from the distributed patch."""
        patch = (ROOT.parent /
                 'patches/helium/ui/screenshot-source-documentation.patch').read_text()
        source = '\n'.join(line[1:] for line in patch.splitlines() if line.startswith('+'))
        match = re.search(r'constexpr char kSourceScript\[\] = R"JS\((.*?)\)JS";', source, re.S)
        if not match:
            raise ValueError('Production screenshot source script not found in patch')
        timestamp = re.search(r'constexpr char kTimestampScript\[\] = R"JS\((.*?)\)JS";', source,
                              re.S)
        if not timestamp:
            raise ValueError('Production timestamp script not found in patch')
        return ('window.detectScreenshotSource = ' + match.group(1) + ';\n' +
                'window.detectScreenshotTimestamp = ' + timestamp.group(1) + ';').encode()

    production_script()

    class Handler(BaseHTTPRequestHandler):
        """Serve only the fixture page and its production source."""

        def do_GET(self): # pylint: disable=invalid-name
            """Respond to an allowed fixture request."""
            path = urlsplit(self.path).path
            if path == '/source.js':
                data, mime = production_script(), 'text/javascript'
            elif path == '/':
                data, mime = (ROOT / 'screenshot_source_fixtures.html').read_bytes(), 'text/html'
            elif path == '/linkedin-capture':
                data, mime = (ROOT / 'screenshot_source_linkedin_capture.html').read_bytes(), 'text/html'
            elif path == '/youtube-capture':
                data, mime = (ROOT / 'screenshot_source_youtube_capture.html').read_bytes(), 'text/html'
            elif path == '/reddit-capture':
                data, mime = (ROOT / 'screenshot_source_reddit_capture.html').read_bytes(), 'text/html'
            elif path == '/tiktok-capture':
                data, mime = (ROOT / 'screenshot_source_tiktok_capture.html').read_bytes(), 'text/html'
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', mime + '; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Screenshot source fixtures: http://127.0.0.1:{args.port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
