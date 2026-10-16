# Copyright 2026 The Helium Authors
# You can use, redistribute, and/or modify this source code under
# the terms of the GPL-3.0 license that can be found in the LICENSE file.
"""Separate the private macOS fork's profile and Keychain identity.

Run after platform patches, which introduce the upstream Helium identities.
The name substitution entry point calls this for both fresh and prepared trees.
"""


def apply_macos_identity(tree, dry_run=False):
    """Update known identity declarations, preserving all other source changes."""
    replacements = {
        'chrome/app/theme/chromium/BRANDING': {
            'PRODUCT_FULLNAME=Helium\n': 'PRODUCT_FULLNAME=Helium Neo\n',
            'PRODUCT_SHORTNAME=Helium\n': 'PRODUCT_SHORTNAME=Helium Neo\n',
            'PRODUCT_INSTALLER_FULLNAME=Helium Installer\n': (
                'PRODUCT_INSTALLER_FULLNAME=Helium Neo Installer\n'),
            'PRODUCT_INSTALLER_SHORTNAME=Helium Installer\n': (
                'PRODUCT_INSTALLER_SHORTNAME=Helium Neo Installer\n'),
            'MAC_BUNDLE_ID=net.imput.helium\n': 'MAC_BUNDLE_ID=no.aagedal.helium-neo\n',
        },
        'chrome/common/chrome_paths_mac.mm': {
            'product_dir_name = "net.imput.helium";': 'product_dir_name = "no.aagedal.helium-neo";',
        },
        'components/os_crypt/common/keychain_password_mac.mm': {
            'kDefaultServiceName[] = "Helium Storage Key";': (
                'kDefaultServiceName[] = "Helium Neo Storage Key";'),
            'kDefaultAccountName[] = "Helium";': 'kDefaultAccountName[] = "Helium Neo";',
        },
    }
    pending = []
    for relative, mapping in replacements.items():
        path = tree / relative
        if not path.exists():
            continue
        original = path.read_text(encoding='utf-8')
        # Other platforms retain Chromium's unused macOS source files.
        if relative.endswith('chrome_paths_mac.mm') and not any(
                marker in original for marker in ('net.imput.helium', 'no.aagedal.helium-neo')):
            continue
        if relative.endswith('keychain_password_mac.mm') and not any(
                marker in original for marker in ('Helium Storage Key', 'Helium Neo Storage Key')):
            continue
        text = original
        for old, new in mapping.items():
            if old not in text and new not in text:
                raise ValueError(f'Unexpected branding in {path}: {old.strip()}')
            text = text.replace(old, new)
        if text != original:
            pending.append((path, original, text))
    for path, original, text in pending:
        print(f'Updated Helium Neo identity in {path.relative_to(tree)}')
        if not dry_run:
            path.write_text(text, encoding='utf-8')
    return [(str(path.relative_to(tree)), original) for path, original, _ in pending]
