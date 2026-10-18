#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Compile the production mobile-fit and refresh-interval helpers.

This checks viewport geometry and allowed intervals, not browser integration.
Run PaneSettingsTest.* in a Chromium build for timer and tab lifecycle checks.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from third_party.unidiff import PatchSet

REPO = Path(__file__).resolve().parent.parent
HEADER = 'chrome/browser/ui/tabs/pane_settings_geometry.h'

HARNESS = r'''
#include "settings.h"
#include <cassert>
#include <iostream>

int main() {
  int cases = 0;
  for (int width : {0, 1, 2, 3, 17, 200, 401, 402, 403, 800, 1600, 3000}) {
    for (int height : {0, 1, 2, 3, 19, 400, 873, 874, 875, 1000, 2000}) {
      const auto fit = tabs::FitMobilePreview(width, height);
      assert(fit.x >= 0 && fit.y >= 0);
      assert(fit.width >= 0 && fit.height >= 0);
      assert(fit.x + fit.width <= width);
      assert(fit.y + fit.height <= height);
      if (width == 0 || height == 0) {
        assert(fit.width == 0 && fit.height == 0 && fit.scale == 0);
      } else {
        assert(fit.scale > 0 && fit.scale <= 1);
        assert(fit.width > 0 && fit.height > 0);
        assert(std::abs(fit.width - 402 * fit.scale) <= 1);
        assert(std::abs(fit.height - 874 * fit.scale) <= 1);
        assert(std::abs(width - fit.width - 2 * fit.x) <= 1);
        assert(std::abs(height - fit.height - 2 * fit.y) <= 1);
      }
      const auto flexible = tabs::FitMobilePreview(width, height, true);
      if (width == 0 || height == 0) {
        assert(flexible.width == 0 && flexible.height == 0);
      } else {
        assert(flexible.width == std::min(width, 402));
        assert(flexible.height == height && flexible.y == 0);
        assert(flexible.scale > 0 && flexible.scale <= 1);
        assert(std::abs(flexible.width - 402 * flexible.scale) <= 1);
        assert(std::abs(width - flexible.width - 2 * flexible.x) <= 1);
      }
      ++cases;
    }
  }
  const auto full = tabs::FitMobilePreview(1600, 2000);
  assert(full.width == 402 && full.height == 874 && full.scale == 1);
  const auto tall = tabs::FitMobilePreview(1600, 2000, true);
  assert(tall.width == 402 && tall.height == 2000 && tall.scale == 1);
  const auto narrow = tabs::FitMobilePreview(201, 2000, true);
  assert(narrow.width == 201 && narrow.height == 2000 && narrow.scale == 0.5);
  for (int seconds = -300; seconds <= 7200; ++seconds) {
    const bool expected = seconds == 0 || seconds == 5 || seconds == 10 ||
        seconds == 15 || seconds == 30 || seconds == 45 || seconds == 60 ||
        seconds == 90 || seconds == 120 || seconds == 180 || seconds == 300 ||
        seconds == 600 || seconds == 1800 || seconds == 3600 ||
        (seconds > 0 && seconds <= 180 && seconds % 15 == 0);
    assert(tabs::IsValidAutoRefreshInterval(seconds) == expected);
  }
  assert(tabs::kAutoRefreshIntervals.size() == 14);
  assert(tabs::kAutoRefreshIntervals[1] == 5);
  assert(tabs::kAutoRefreshIntervals.back() == 3600);
  for (int seconds : tabs::kAutoRefreshIntervals) {
    for (int i = 0; i <= 100; ++i) {
      const double unit = i / 100.0;
      const double jittered = tabs::RefreshDelaySeconds(seconds, true, unit);
      assert(jittered >= seconds * 0.95 - 1e-9);
      assert(jittered <= seconds * 1.05 + 1e-9);
      assert(tabs::RefreshDelaySeconds(seconds, false, unit) == seconds);
    }
  }

  std::cout << "PASS: " << cases
            << " viewport cases, 7501 interval checks and 1414 jitter checks\n";
}
'''


def extract_header():
    """Extract the production geometry header from the preview patch."""
    patch = PatchSet((REPO / 'patches/helium/ui/tab-preview-workspaces.patch').read_text())
    file = next(file for file in patch if file.path == HEADER)
    lines = ''.join(line.value for hunk in file for line in hunk if line.is_added).splitlines(True)
    followup = PatchSet((REPO / 'patches/helium/ui/pinned-split-pane-state.patch').read_text())
    changes = next(file for file in followup if file.path == HEADER)
    for hunk in reversed(changes):
        start = hunk.source_start - 1
        before = [line.value for line in hunk if not line.is_added]
        after = [line.value for line in hunk if not line.is_removed]
        assert lines[start:start + len(before)] == before
        lines[start:start + len(before)] = after
    monitoring = PatchSet((REPO / 'patches/helium/ui/page-change-monitor.patch').read_text())
    changes = next(file for file in monitoring if file.path == HEADER)
    for hunk in reversed(changes):
        start = hunk.source_start - 1
        before = [line.value for line in hunk if not line.is_added]
        after = [line.value for line in hunk if not line.is_removed]
        assert lines[start:start + len(before)] == before
        lines[start:start + len(before)] = after
    return ''.join(lines)


def main():
    """Compile and run the viewport and refresh-interval checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-tree', type=Path)
    parser.add_argument('--cxx', default='clang++')
    args = parser.parse_args()
    compiler = shutil.which(args.cxx)
    if not compiler:
        parser.error(f'C++ compiler not found: {args.cxx}')
    with tempfile.TemporaryDirectory(prefix='helium-preview-test-') as directory:
        temp = Path(directory)
        header = ((args.source_tree / HEADER).read_text() if args.source_tree else extract_header())
        (temp / 'settings.h').write_text(header)
        (temp / 'test.cc').write_text(HARNESS)
        subprocess.run([
            compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
            str(temp / 'test.cc'), '-o',
            str(temp / 'test')
        ],
                       check=True)
        subprocess.run([str(temp / 'test')], check=True)


if __name__ == '__main__':
    main()
