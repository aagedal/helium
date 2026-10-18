#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Compile the production changed-line excerpt helper with sanitizers."""
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
int main() {
  auto diff = tabs::BuildPageChangeDiff("Title\nThe meeting will be on Wednesday.",
                                       "Title\nThe meeting has moved to Thursday.");
  assert(diff.first == "The meeting will be on Wednesday.");
  assert(diff.second == "The meeting has moved to Thursday.");
  diff = tabs::BuildPageChangeDiff("Title\nOld statement.\nFooter", "Title\nNew statement.\nFooter");
  assert(diff.first == "Old statement." && diff.second == "New statement.");
  diff = tabs::BuildPageChangeDiff("same", "same");
  assert(diff.first.empty() && diff.second.empty());
  diff = tabs::BuildPageChangeDiff("", "Added");
  assert(diff.first.empty() && diff.second == "Added");
  diff = tabs::BuildPageChangeDiff("Removed", "");
  assert(diff.first == "Removed" && diff.second.empty());
  diff = tabs::BuildPageChangeDiff("A\nB\nC", "A\nC");
  assert(diff.first == "B" && diff.second.empty());
  diff = tabs::BuildPageChangeDiff("A\nC", "A\nB\nC");
  assert(diff.first.empty() && diff.second == "B");
  diff = tabs::BuildPageChangeDiff("Tittel\nRødgrønn 日本語.", "Tittel\nBlågrønn 日本語.");
  assert(diff.first == "Rødgrønn 日本語." && diff.second == "Blågrønn 日本語.");
  diff = tabs::BuildPageChangeDiff(std::string(15999, 'x') + "日本語", "changed");
  assert(diff.first.size() == 15999);
  for (int count = 0; count < 200; ++count) {
    const std::string prefix(count, 'p'), suffix(count, 's');
    diff = tabs::BuildPageChangeDiff(prefix + "AAA" + suffix, prefix + "BBB" + suffix);
    assert(diff.first == prefix + "AAA" + suffix);
    assert(diff.second == prefix + "BBB" + suffix);
  }
  std::cout << "PASS: 209 changed-line and UTF-8 excerpt cases\n";
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
