#!/usr/bin/env python3
# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Regenerate Helium Neo's vector, bitmap and macOS icon resources.

Run on macOS with Pillow, librsvg's rsvg-convert, and Xcode installed.
The checked-in macOS catalogs allow other platforms to prepare sources without
running Apple's tools. product_logo.svg is the full-color master; the transparent
Icon Composer foreground and Chromium vector paths share the orbital geometry.
"""

from pathlib import Path
import math
import shutil
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BRANDING = ROOT / 'resources/branding'
LICENSE = '''// Copyright 2026 The Helium Authors
// You can use, redistribute, and/or modify this source code under
// the terms of the GPL-3.0 license that can be found in the LICENSE file.

'''


def vector_mark(scale):
    """Create a filled orbital arc, central core, and satellite."""
    angle = math.radians(-35)

    def point(radius_x, radius_y, theta):
        point_x, point_y = radius_x * math.cos(theta), radius_y * math.sin(theta)
        return ((128 + point_x * math.cos(angle) - point_y * math.sin(angle)) * scale,
                (128 + point_x * math.sin(angle) + point_y * math.cos(angle)) * scale)

    angles = [.34 + (2 * math.pi - .68) * i / 96 for i in range(97)]
    polygon = [point(96, 60, t) for t in angles]
    polygon += [point(84, 48, t) for t in reversed(angles)]
    lines = ['FILL_RULE_NONZERO,']
    for i, (point_x, point_y) in enumerate(polygon):
        lines.append(f'{"MOVE_TO" if i == 0 else "LINE_TO"}, {point_x:.4f}f, {point_y:.4f}f,')
    lines += [
        'CLOSE,', 'NEW_PATH,', f'CIRCLE, {128*scale:.4f}f, {128*scale:.4f}f, {30*scale:.4f}f,',
        'NEW_PATH,', f'CIRCLE, {201.724*scale:.4f}f, {76.378*scale:.4f}f, {11.5*scale:.4f}f,'
    ]
    return '\n'.join(lines) + '\n'


def main(): # pylint: disable=too-many-locals
    """Generate all formats without modifying any prepared Chromium tree."""
    renderer = shutil.which('rsvg-convert')
    if not renderer:
        raise SystemExit('Install librsvg (rsvg-convert) before generating icons.')
    subprocess.run([
        renderer, '-w', '1024', '-h', '1024',
        str(BRANDING / 'product_logo.svg'), '-o',
        str(BRANDING / 'app_icon/raw.png')
    ],
                   check=True)
    raw = Image.open(BRANDING / 'app_icon/raw.png').convert('RGBA')
    raw.resize((512, 512), Image.Resampling.LANCZOS).save(BRANDING / 'app_icon/file.png')
    (BRANDING / 'product_logo.icon').write_text(LICENSE + 'CANVAS_DIMENSIONS, 56,\n' +
                                                vector_mark(56 / 256))
    (BRANDING / 'product_logo_color.icon').write_text(
        LICENSE + 'CANVAS_DIMENSIONS, 256,\nNEW_PATH,\n'
        'PATH_COLOR_ARGB, 0xFF, 0x79, 0x45, 0xE8,\n'
        'ROUND_RECT, 5.5f, 5.5f, 245, 245, 61,\nNEW_PATH,\n'
        'PATH_COLOR_ARGB, 0xFF, 0xF7, 0xF2, 0xFF,\n' +
        vector_mark(1).replace('NEW_PATH,', 'NEW_PATH,\nPATH_COLOR_ARGB, 0xFF, 0xF7, 0xF2, 0xFF,'))
    with tempfile.TemporaryDirectory(prefix='helium-neo-icons-') as temporary:
        temp = Path(temporary)
        foreground = temp / 'foreground.png'
        subprocess.run([
            renderer, '-w', '1024', '-h', '1024',
            str(BRANDING / 'macos/AppIcon.icon/Assets/logo.svg'), '-o',
            str(foreground)
        ],
                       check=True)
        # Icon Composer's SVG importer changes stroked arcs into filled shapes
        # and uses the SVG's intrinsic size. Supply a full-resolution raster of
        # the same vector artwork for predictable modern macOS rendering.
        shutil.copy2(foreground, BRANDING / 'macos/AppIcon.icon/Assets/logo.png')
        glyph = Image.open(foreground).convert('RGBA')
        glyph.resize((22, 22), Image.Resampling.LANCZOS).save(BRANDING / 'product_logo_22_mono.png')
        for scale, suffix in [(1, ''), (2, '_200')]:
            for light in [False, True]:
                wordmark = Image.new('RGBA', (140 * scale, 32 * scale))
                wordmark.alpha_composite(
                    raw.resize((32 * scale, 32 * scale), Image.Resampling.LANCZOS))
                size = 18 * scale
                while True:
                    font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', size, index=1)
                    if font.getlength('Helium Neo') <= 102 * scale:
                        break
                    size -= 1
                draw = ImageDraw.Draw(wordmark)
                draw.text((38 * scale, 16 * scale),
                          'Helium Neo',
                          font=font,
                          fill='white' if light else '#211534',
                          anchor='lm')
                wordmark.save(BRANDING / f'product_logo{"_white" if light else ""}{suffix}.png')
        catalog = temp / 'Assets.xcassets'
        shutil.copytree(BRANDING / 'macos/Assets.xcassets', catalog)
        appset = catalog / 'AppIcon.appiconset'
        for size in [16, 32, 64, 128, 256, 512, 1024]:
            raw.resize((size, size), Image.Resampling.LANCZOS).save(appset / f'appicon_{size}.png')
        iconset = temp / 'AppIcon.iconset'
        iconset.mkdir()
        for size in [16, 32, 128, 256, 512]:
            for factor in [1, 2]:
                raw.resize((size * factor, size * factor), Image.Resampling.LANCZOS).save(
                    iconset / f'icon_{size}x{size}{"@2x" if factor == 2 else ""}.png')
        subprocess.run(
            ['iconutil', '-c', 'icns',
             str(iconset), '-o',
             str(BRANDING / 'macos/app.icns')],
            check=True)
        output = temp / 'compiled'
        output.mkdir()
        subprocess.run([
            'xcrun',
            'actool',
            '--output-format',
            'human-readable-text',
            '--notices',
            '--warnings',
            '--errors',
            '--platform',
            'macosx',
            '--target-device',
            'mac',
            '--minimum-deployment-target',
            '13.0',
            '--app-icon',
            'AppIcon',
            '--include-all-app-icons',
            '--enable-icon-stack-fallback-generation=enabled',
            '--lightweight-asset-runtime-mode=enabled',
            '--output-partial-info-plist',
            str(temp / 'partial.plist'),
            '--compile',
            str(output),
            str(catalog),
            str(BRANDING / 'macos/AppIcon.icon'),
        ],
                       check=True)
        shutil.copy2(output / 'Assets.car', BRANDING / 'macos/Assets.car')
    print('Generated Helium Neo orbital icons, wordmarks, app.icns and Assets.car.')


if __name__ == '__main__':
    main()
