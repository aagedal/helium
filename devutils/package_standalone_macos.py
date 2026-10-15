#!/usr/bin/env python3
"""Relocate a prepared arm64 component app and ad-hoc sign it for local sharing.

Does not modify the build cache. Developer ID signing/notarization is a separate
release step; an ad-hoc signature does not establish a trusted publisher.
"""

import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess


def run(*args):
    return subprocess.check_output([str(arg) for arg in args], text=True)


def macho(path):
    with path.open('rb') as stream:
        return stream.read(4) in (b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe')


def dependencies(path):
    return [line.strip().split(' (compatibility version')[0]
            for line in run('otool', '-m', '-L', path).splitlines()[1:]]


def relocate_rpaths(binary, rpath):
    # Edit only the load-command area, preserving every segment/file offset.
    # Apple's install_name_tool rejects the sectionless framework stub, while
    # LLVM's tool does not support its LC_REEXPORT_DYLIB command.
    with binary.open('r+b') as stream:
        header = stream.read(32)
        if header[:4] != b'\xcf\xfa\xed\xfe':
            raise RuntimeError(f'Expected a thin little-endian Mach-O: {binary}')
        count, size = struct.unpack_from('<II', header, 16)
        original = stream.read(size)
        commands = []
        offset = 0
        for _ in range(count):
            command, length = struct.unpack_from('<II', original, offset)
            if length < 8 or offset + length > size:
                raise RuntimeError(f'Invalid load command: {binary}')
            if command != 0x8000001c:  # LC_RPATH
                commands.append(original[offset:offset + length])
            offset += length
        if offset != size:
            raise RuntimeError(f'Invalid load command size: {binary}')
        encoded = rpath.encode() + b'\0'
        length = (12 + len(encoded) + 7) & ~7
        commands.append(struct.pack('<III', 0x8000001c, length, 12)
                        + encoded + bytes(length - 12 - len(encoded)))
        replacement = b''.join(commands)
        if len(replacement) > size:
            raise RuntimeError(f'Insufficient load command space: {binary}')
        header = bytearray(header)
        struct.pack_into('<II', header, 16, len(commands), len(replacement))
        stream.seek(0)
        stream.write(header + replacement + bytes(size - len(replacement)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-output', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True,
                        help='New directory for the standalone app')
    args = parser.parse_args()
    output = args.build_output.resolve()
    destination = args.destination.resolve()
    source = output / 'Helium Neo.app'
    if destination.exists():
        parser.error('Destination already exists; choose a new directory')
    if not source.is_dir():
        parser.error(f'Missing app: {source}')
    destination.mkdir(parents=True)
    app = destination / source.name
    run('ditto', source, app)
    frameworks = app / 'Contents/Frameworks'
    binaries = [path for path in app.rglob('*')
                if path.is_file() and not path.is_symlink() and macho(path)]
    seen = set(binaries)
    # Close over dependencies instead of copying arbitrary build outputs.
    index = 0
    while index < len(binaries):
        binary = binaries[index]
        index += 1
        for dependency in dependencies(binary):
            if dependency.startswith(('/System/Library/', '/usr/lib/')):
                continue
            if not dependency.startswith('@rpath/'):
                raise RuntimeError(f'Unexpected dependency: {binary}: {dependency}')
            relative = dependency.removeprefix('@rpath/')
            target = frameworks / relative
            if target.exists():
                continue
            origin = output / relative
            if not origin.is_file() or '/' in relative:
                raise RuntimeError(f'Unresolved dependency: {binary}: {dependency}')
            shutil.copy2(origin, target)
            if target not in seen:
                seen.add(target)
                binaries.append(target)
    print(f'Bundled {len(binaries)} Mach-O files', flush=True)
    for binary in binaries:
        if run('lipo', '-archs', binary).strip() != 'arm64':
            raise RuntimeError(f'Expected arm64: {binary}')
        # All component dependencies live under Contents/Frameworks. Remove
        # development rpaths so no loader can fall back to the build cache.
        new_rpath = '@loader_path/' + os.path.relpath(frameworks, binary.parent)
        relocate_rpaths(binary, new_rpath)
        for dependency in dependencies(binary):
            if dependency.startswith('@rpath/'):
                target = frameworks / dependency.removeprefix('@rpath/')
                if not target.is_file():
                    raise RuntimeError(f'Missing bundled dependency: {dependency}')
        run('codesign', '--force', '--sign', '-', binary)
    # Sign nested code first, then seal the containing app.
    bundles = [path for path in app.rglob('*')
               if path.is_dir() and path.suffix in ('.app', '.framework')]
    for bundle in sorted(bundles, key=lambda path: len(path.parts), reverse=True):
        run('codesign', '--force', '--sign', '-', bundle)
    run('codesign', '--force', '--sign', '-', app)
    run('codesign', '--verify', '--deep', '--strict', '--verbose=2', app)
    print(f'Verified standalone app: {app}', flush=True)


if __name__ == '__main__':
    main()
