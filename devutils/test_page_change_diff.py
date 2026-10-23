#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Compile the production line diff helper with sanitizers."""
from pathlib import Path
import shutil
import subprocess
import tempfile
from third_party.unidiff import PatchSet

ROOT = Path(__file__).resolve().parent.parent
HARNESS = r'''
#include "diff.h"
#include <cassert>
#include <iostream>
#include <string>
#include <vector>
using Kind = tabs::PageChangeLine::Kind;
static int cases = 0;
static std::string render(const std::vector<tabs::PageChangeLine>& rows) {
  std::string out;
  for (const auto& row : rows) {
    switch (row.kind) {
      case Kind::kContext: out += " " + row.text; break;
      case Kind::kRemoved: out += "-" + row.text; break;
      case Kind::kAdded: out += "+" + row.text; break;
      case Kind::kGap: out += "~" + std::to_string(row.hidden); break;
      case Kind::kTruncated: out += "!"; break;
    }
    out += "|";
  }
  return out;
}
static void expect(const std::string& before, const std::string& after,
                   const std::string& expected, size_t context = 2) {
  const auto actual = render(tabs::BuildPageChangeLines(before, after, context));
  if (actual != expected) {
    std::cerr << "expected " << expected << "\n  actual " << actual << "\n";
    assert(false);
  }
  ++cases;
}
int main() {
  expect("Title\nThe meeting will be on Wednesday.",
         "Title\nThe meeting has moved to Thursday.",
         " Title|-The meeting will be on Wednesday.|+The meeting has moved to Thursday.|");
  expect("same", "same", "");
  expect("", "Added", "+Added|");
  expect("Removed", "", "-Removed|");
  expect("A\nB\nC", "A\nC", " A|-B| C|");
  expect("A\nC", "A\nB\nC", " A|+B| C|");
  // Context is limited and the rest is summarized.
  expect("1\n2\n3\n4\n5\nold\n6\n7\n8\n9", "1\n2\n3\n4\n5\nnew\n6\n7\n8\n9",
         "~3| 4| 5|-old|+new| 6| 7|~2|");
  // Separate edits keep their own context and a gap between them.
  expect("a\nb\nc\nd\ne\nf\ng\nh\ni", "A\nb\nc\nd\ne\nf\ng\nh\nI",
         "-a|+A| b| c|~3| g| h|-i|+I|");
  // A moved block is shown as a removal and an addition, not a rewrite.
  expect("x\ny\nz", "y\nz\nx", "-x| y| z|+x|");
  // Removals precede additions within one edit.
  expect("k\n1\n2\nk", "k\n3\n4\nk", " k|-1|-2|+3|+4| k|");
  expect("Tittel\nRødgrønn 日本語.", "Tittel\nBlågrønn 日本語.",
         " Tittel|-Rødgrønn 日本語.|+Blågrønn 日本語.|");
  // Long lines are clipped without splitting a UTF-8 sequence.
  {
    const auto rows = tabs::BuildPageChangeLines(std::string(1999, 'x') + "日本語", "changed");
    assert(rows.size() == 2 && rows[0].kind == Kind::kRemoved);
    assert(rows[0].text == std::string(1999, 'x') + "…");
    ++cases;
  }
  // Large edits fall back without the LCS table and stay bounded.
  {
    std::string before, after;
    for (int i = 0; i < 1500; ++i) {
      before += "old " + std::to_string(i) + "\n";
      after += "new " + std::to_string(i) + "\n";
    }
    const auto rows = tabs::BuildPageChangeLines(before, after);
    assert(rows.size() == 301 && rows.back().kind == Kind::kTruncated);
    for (size_t i = 0; i < 300; ++i) assert(rows[i].kind == Kind::kRemoved);
    ++cases;
  }
  for (int count = 0; count < 200; ++count) {
    std::string prefix, suffix;
    for (int i = 0; i < count; ++i) {
      prefix += "p" + std::to_string(i) + "\n";
      suffix += "\ns" + std::to_string(i);
    }
    const auto rows = tabs::BuildPageChangeLines(prefix + "AAA" + suffix, prefix + "BBB" + suffix);
    size_t removed = 0, added = 0, context = 0;
    for (const auto& row : rows) {
      removed += row.kind == Kind::kRemoved && row.text == "AAA";
      added += row.kind == Kind::kAdded && row.text == "BBB";
      context += row.kind == Kind::kContext;
    }
    assert(removed == 1 && added == 1 && context == static_cast<size_t>(std::min(count, 2) * 2));
    ++cases;
  }
  std::cout << "PASS: " << cases << " line diff, context and UTF-8 cases\n";
}
'''


def main():
    """Extract, compile and exercise the actual shipped C++ helper."""
    compiler = shutil.which('clang++')
    if not compiler:
        raise RuntimeError('clang++ is required')
    patch = PatchSet((ROOT / 'patches/helium/ui/page-change-monitor.patch').read_text())
    header = next(file for file in patch if file.path.endswith('/page_change_monitor_diff.h'))
    source = ''.join(line.value for hunk in header for line in hunk if line.is_added)
    with tempfile.TemporaryDirectory(prefix='helium-monitor-diff-') as directory:
        folder = Path(directory)
        (folder / 'diff.h').write_text(source)
        (folder / 'test.cc').write_text(HARNESS)
        subprocess.run([
            compiler, '-std=c++20', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined',
            str(folder / 'test.cc'), '-o',
            str(folder / 'test')
        ],
                       check=True)
        subprocess.run([str(folder / 'test')], check=True)


if __name__ == '__main__':
    main()
