# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Regression coverage for the upstream prepared-source merge and pruning."""

from pathlib import Path
import shutil
import tarfile

from .. import _extraction, prune_binaries


def test_dependency_archive_creates_nested_output_directory(tmp_path):
    source = tmp_path / 'input'
    source.mkdir()
    (source / 'encoder.cc').write_text('encoder')
    archive = tmp_path / 'encoder.tar'
    with tarfile.open(archive, 'w') as stream:
        stream.add(source, arcname='encoder')
    destination = tmp_path / 'chromium/third_party/helium_jxl/src'
    _extraction._extract_tar_with_tar(shutil.which('tar'), archive, destination, Path('encoder'))
    assert (destination / 'encoder.cc').read_text() == 'encoder'


def write(root, name, content='data'):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def test_archive_layers_preserve_existing_tools_and_replace_overlaps(tmp_path):
    tool = write(tmp_path, 'third_party/toolchain/compiler', 'compiler')
    write(tmp_path, 'third_party/library/header.h', 'old')
    write(tmp_path, 'layer/third_party/library/header.h', 'new')
    write(tmp_path, 'layer/third_party/library/source.cc')

    _extraction._process_relative_to(tmp_path, Path('layer'))

    assert tool.read_text() == 'compiler'
    assert (tmp_path / 'third_party/library/header.h').read_text() == 'new'
    assert (tmp_path / 'third_party/library/source.cc').is_file()
    assert not (tmp_path / 'layer').exists()


def test_archive_layer_replaces_symlink_without_touching_target(tmp_path):
    outside = tmp_path / 'outside'
    retained = write(outside, 'retained', 'keep')
    (tmp_path / 'linked').symlink_to(outside, target_is_directory=True)
    write(tmp_path, 'layer/linked/new')

    _extraction._process_relative_to(tmp_path, Path('layer'))

    assert retained.read_text() == 'keep'
    assert not (outside / 'new').exists()
    assert not (tmp_path / 'linked').is_symlink()
    assert (tmp_path / 'linked/new').is_file()


def test_build_dependencies_survive_both_pruning_passes(tmp_path):
    paths = ('third_party/llvm-build/compiler', 'third_party/node/linux/node',
             'third_party/rust-toolchain/bin/rustc',
             'third_party/rust/chromium_crates_io/vendor/windows_aarch64_msvc-1/lib.a')
    for path in paths:
        write(tmp_path, path)
    removed = write(tmp_path, 'third_party/hunspell/tests/unneeded.bin')
    metadata = write(tmp_path, 'third_party/hunspell/tests/BUILD.gn')
    explicit = write(tmp_path, 'unneeded.bin')
    prune_binaries.prune_dirs(tmp_path, False, None, keep_build_dependencies=True)
    missing = prune_binaries.prune_files(tmp_path, (*paths, 'unneeded.bin'),
                                         keep_build_dependencies=True)

    assert not missing
    assert all((tmp_path / path).exists() for path in paths)
    assert metadata.exists()
    assert not removed.exists()
    assert not explicit.exists()


def test_build_dependencies_are_pruned_when_not_requested(tmp_path):
    path = 'third_party/llvm-build/compiler'
    compiler = write(tmp_path, path)
    assert not prune_binaries.prune_files(tmp_path, (path, ))
    assert not compiler.exists()
