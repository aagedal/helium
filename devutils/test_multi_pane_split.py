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
                            SplitTabArrangement::kTrailingSingle,
                            SplitTabArrangement::kLeadingStacked}) {
    for (auto orientation : {SplitTabLayout::kSideBySide,
                             SplitTabLayout::kStacked}) {
      for (size_t count : {2u, 3u, 4u, 5u, 6u}) {
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
  // Every new boundary must reserve a hit-testable gutter, and resizing an
  // adjacent pair must preserve the other panes and the group's total weight.
  int resize_cases = 0;
  for (auto orientation : {SplitTabLayout::kSideBySide, SplitTabLayout::kStacked}) {
    for (auto arrangement : {SplitTabArrangement::kGrid, SplitTabArrangement::kLinear,
                              SplitTabArrangement::kLeadingSingle,
                              SplitTabArrangement::kTrailingSingle,
                            SplitTabArrangement::kLeadingStacked}) {
      for (size_t count : {3u, 4u, 5u, 6u}) {
        const size_t first_count = FirstSplitPaneCount(count, arrangement);
        GridPaneBounds first{11, 23, 601, 601}, second{622, 23, 601, 601};
        if (orientation == SplitTabLayout::kStacked) second = {11, 634, 601, 601};
        const std::array<double, 6> initial{1, 1, 1, 1, 1, 1};
        const auto original = CalculateSplitPaneBounds(first, second, count,
                                                        orientation, arrangement,
                                                        initial, 6);
        for (size_t boundary = 0; boundary < count - 2; ++boundary) {
          const size_t leaf = boundary < first_count - 1 ? boundary : boundary + 1;
          const bool vertical = SplitPaneGroupIsVertical(orientation, arrangement,
                                                          leaf < first_count);
          const auto a = original[leaf], b = original[leaf + 1];
          assert((vertical ? b.y - a.y - a.height : b.x - a.x - a.width) == 6);
          const int start = vertical ? a.height : a.width;
          const int total = start + (vertical ? b.height : b.width);
          for (int delta : {-10000, -60, 60, 10000}) {
            auto weights = ResizeSplitPaneWeights(initial, leaf, start, total, delta);
            assert(std::abs(weights[leaf] + weights[leaf + 1] - 2) < 1e-12);
            for (size_t i = 0; i < 6; ++i) {
              assert(weights[i] > 0);
              if (i != leaf && i != leaf + 1) assert(weights[i] == initial[i]);
            }
            const auto panes = CalculateSplitPaneBounds(first, second, count,
                                                         orientation, arrangement,
                                                         weights, 6);
            assert((vertical ? panes[leaf].height : panes[leaf].width) >= 79);
            assert((vertical ? panes[leaf + 1].height : panes[leaf + 1].width) >= 79);
            for (size_t i = 0; i < count; ++i) {
              if (i == leaf || i == leaf + 1) continue;
              assert(panes[i].x == original[i].x && panes[i].y == original[i].y);
              assert(panes[i].width == original[i].width &&
                     panes[i].height == original[i].height);
            }
            ++resize_cases;
          }
        }
        // Tiny windows must never yield negative panes or overlapping gutters.
        for (int extent : {0, 1, 2, 5, 6, 7, 12}) {
          auto tiny = CalculateSplitPaneBounds({0, 0, extent, extent},
                                               {extent + 6, 0, extent, extent},
                                               count, orientation, arrangement,
                                               {0.1, 1.9, 1.2, 0.8, 1, 1}, 6);
          for (size_t i = 0; i < count; ++i) {
            assert(tiny[i].width >= 0 && tiny[i].height >= 0);
            for (size_t j = 0; j < i; ++j) assert(Intersection(tiny[i], tiny[j]) == 0);
          }
        }
      }
    }
  }
  const auto six = CalculateSplitPaneBounds({0, 0, 600, 300}, {0, 306, 600, 300},
                                             6, SplitTabLayout::kStacked,
                                             SplitTabArrangement::kGrid,
                                             {1, 1, 1, 1, 1, 1}, 6);
  for (size_t i = 0; i < six.size(); ++i) {
    assert(six[i].x == static_cast<int>(i % 3) * 202);
    assert(six[i].y == (i < 3 ? 0 : 306));
    assert(six[i].width == 196 && six[i].height == 300);
  }
  const auto five = CalculateSplitPaneBounds({0, 0, 200, 600}, {206, 0, 600, 600},
                                              5, SplitTabLayout::kSideBySide,
                                              SplitTabArrangement::kLeadingStacked,
                                              {1, 1, 1, 1, 1, 1}, 6);
  assert(five[0].width == 200 && five[0].height == 297 && five[1].y == 303);
  for (size_t i = 2; i < 5; ++i) {
    assert(five[i].x == 206 + static_cast<int>(i - 2) * 202);
    assert(five[i].y == 0 && five[i].width == 196 && five[i].height == 600);
  }
  assert(DefaultSplitPaneRatio(5, SplitTabArrangement::kLeadingStacked) == .25);
  std::cout << "PASS: exact 3 x 2 and five-pane mixed layouts\n";
  std::cout << "PASS: " << resize_cases << " divider resizing cases\n";
  for (size_t invalid_count : {0u, 1u, 7u, 100u}) {
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
    patch = PatchSet((REPO / 'patches/helium/ui/extended-pane-layouts.patch').read_text())
    header = next(file for file in patch if file.path == HEADER)
    # The final header hunk includes its full context for standalone compilation.
    return ''.join(line.value for hunk in header for line in hunk if not line.is_removed)



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
