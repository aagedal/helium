#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Compile and exercise the production grid helper without a Chromium build.

With --source-tree, compile the actual patched Chromium header. Otherwise,
extract the helper verbatim from the patch and supply only its enum dependency.
This checks geometry, not browser integration; run the Chromium model tests and
manual browser checks in devutils/README.md before shipping.
"""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

from third_party.unidiff import PatchSet

REPO = Path(__file__).resolve().parent.parent
HEADER = 'components/split_tabs/split_tab_visual_data.h'

HARNESS = r'''
#include "grid.h"
#include <algorithm>
#include <cassert>
#include <iostream>
using namespace split_tabs;

int Area(GridPaneBounds r) { return r.width * r.height; }
int Intersection(GridPaneBounds a, GridPaneBounds b) {
  return std::max(0, std::min(a.x + a.width, b.x + b.width) -
                        std::max(a.x, b.x)) *
         std::max(0, std::min(a.y + a.height, b.y + b.height) -
                        std::max(a.y, b.y));
}

int main() {
  int cases = 0;
  for (auto arrangement : {SplitTabArrangement::kGrid,
                            SplitTabArrangement::kLinear,
                            SplitTabArrangement::kLeadingSingle,
                            SplitTabArrangement::kTrailingSingle}) {
    for (auto orientation : {SplitTabLayout::kSideBySide,
                             SplitTabLayout::kStacked}) {
      for (size_t count : {2u, 3u, 4u}) {
        for (int extent : {0, 1, 2, 3, 7, 33, 200, 901}) {
          for (int cross : {0, 1, 2, 3, 17, 400, 703}) {
            for (int first_size : {0, extent / 3, extent / 2, extent}) {
              GridPaneBounds first{11, 23, first_size, cross};
              GridPaneBounds second{11 + first_size + 10, 23,
                                    extent - first_size, cross};
              if (orientation == SplitTabLayout::kStacked) {
                first = {11, 23, cross, first_size};
                second = {11, 23 + first_size + 10, cross, extent - first_size};
              }
              const auto panes = CalculateSplitPaneBounds(first, second, count,
                                                          orientation, arrangement);
              int area = 0;
              for (size_t i = 0; i < count; ++i) {
                auto p = panes[i];
                assert(p.width >= 0 && p.height >= 0);
                area += Area(p);
                const auto parent = i < FirstSplitPaneCount(count, arrangement)
                                        ? first : second;
                assert(p.x >= parent.x && p.y >= parent.y);
                assert(p.x + p.width <= parent.x + parent.width);
                assert(p.y + p.height <= parent.y + parent.height);
                for (size_t j = 0; j < i; ++j) {
                  assert(Intersection(p, panes[j]) == 0);
                }
              }
              assert(area == Area(first) + Area(second));
              for (size_t i = count; i < panes.size(); ++i) {
                assert(Area(panes[i]) == 0);
              }
              if (arrangement == SplitTabArrangement::kLinear) {
                for (size_t i = 0; i < count; ++i) {
                  if (orientation == SplitTabLayout::kSideBySide) {
                    assert(panes[i].y == 23 && panes[i].height == cross);
                  } else {
                    assert(panes[i].x == 11 && panes[i].width == cross);
                  }
                }
              }
              if (arrangement == SplitTabArrangement::kGrid) {
                const auto legacy = CalculateGridPaneBounds(first, second, count,
                                                            orientation);
                for (size_t i = 0; i < count; ++i) {
                  assert(panes[i].x == legacy[i].x && panes[i].y == legacy[i].y);
                  assert(panes[i].width == legacy[i].width);
                  assert(panes[i].height == legacy[i].height);
                }
              }
              if (count == 2) {
                assert(Intersection(panes[0], first) == Area(first));
                assert(Intersection(panes[1], second) == Area(second));
              }
              ++cases;
            }
          }
        }
      }
    }
  }
  for (size_t invalid_count : {0u, 1u, 5u, 100u}) {
    const auto panes = CalculateSplitPaneBounds({0, 0, 100, 100},
                                               {110, 0, 100, 100},
                                               invalid_count,
                                               SplitTabLayout::kSideBySide,
                                               SplitTabArrangement::kLinear);
    for (auto p : panes) { assert(Area(p) == 0); }
  }
  std::cout << "PASS: " << cases
            << " geometry cases plus invalid pane counts\n";
}
'''


def extract_helper():
    """Extract the production grid helper from the split-view patch."""
    patch = PatchSet((REPO / 'patches/helium/ui/multi-pane-split-view.patch').read_text())
    file = next(file for file in patch if file.path == HEADER)
    inserted = ''.join(line.value for hunk in file for line in hunk if line.is_added)
    start = inserted.index('struct GridPaneBounds')
    end = inserted.index('\n  return panes;\n}', start) + len('\n  return panes;\n}')
    followup = PatchSet((REPO / 'patches/helium/ui/split-layout-options.patch').read_text())
    header = next(file for file in followup if file.path == HEADER)
    additions = ''.join(line.value for hunk in header for line in hunk if line.is_added)
    extra_start = additions.index('enum class SplitTabArrangement')
    extra_end = additions.index('\n  return panes;\n}', extra_start) + len('\n  return panes;\n}')
    return ('#include <array>\n#include <cstddef>\nnamespace split_tabs {\n'
            'enum class SplitTabLayout { kSideBySide, kStacked };\n' + inserted[start:end] + '\n' +
            additions[extra_start:extra_end] + '\n}\n')


def main():
    """Compile and run the multi-pane geometry checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-tree',
                        type=Path,
                        help='Chromium source tree with the Helium patches applied')
    parser.add_argument('--cxx', default='clang++')
    args = parser.parse_args()
    compiler = shutil.which(args.cxx)
    if not compiler:
        parser.error(f'C++ compiler not found: {args.cxx}')
    with tempfile.TemporaryDirectory(prefix='helium-grid-test-') as directory:
        temp = Path(directory)
        header = ((args.source_tree / HEADER).read_text() if args.source_tree else extract_helper())
        (temp / 'grid.h').write_text(header)
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
