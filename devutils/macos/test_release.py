#!/usr/bin/env python3
"""Checks release/feed integrity and the mirror's rollback protection."""

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from deploy_mirror import check_not_older, validate_bundle
from make_appcast import make_feed


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = json.loads(Path(__file__).with_name('release.json').read_text())
        self.archive = self.root / ('Helium-Neo-' + self.config['version'] + '-macOS-arm64-signed.dmg')
        self.archive.write_bytes(b'installer fixture')
        self.manifest = {
            **self.config, 'installer': self.archive.name, 'bytes': self.archive.stat().st_size,
            'sha256': hashlib.sha256(self.archive.read_bytes()).hexdigest(),
            'ed_signature': 'signature fixture',
            'primary_download': 'https://github.com/aagedal/helium/releases/download/' + self.config['tag'] + '/' + self.archive.name,
            'backup_download': self.config['backup_download_base'] + self.archive.name,
        }
        self.write_bundle()

    def write_bundle(self):
        (self.root / 'update-manifest.json').write_text(json.dumps(self.manifest))
        for name, url in [('helium-neo.xml', self.manifest['primary_download']),
                          ('helium-neo-backup.xml', self.manifest['backup_download'])]:
            (self.root / name).write_bytes(make_feed(self.config, self.archive,
                self.manifest['ed_signature'], url, 'Sat, 17 Oct 2026 00:00:00 +0000'))

    def test_same_signed_archive_on_both_hosts(self):
        self.assertEqual(validate_bundle(self.root), self.manifest)

    def test_modified_archive_rejected_before_upload(self):
        self.archive.write_bytes(b'corrupted installer')
        with self.assertRaisesRegex(ValueError, 'manifest'):
            validate_bundle(self.root)

    def test_backup_pointing_at_github_rejected(self):
        (self.root / 'helium-neo-backup.xml').write_bytes((self.root / 'helium-neo.xml').read_bytes())
        with self.assertRaisesRegex(ValueError, 'disagree'):
            validate_bundle(self.root)

    def test_changed_signature_rejected(self):
        feed = self.root / 'helium-neo.xml'
        feed.write_text(feed.read_text().replace('signature fixture', 'wrong signature'))
        with self.assertRaisesRegex(ValueError, 'disagree'):
            validate_bundle(self.root)

    def test_path_traversal_rejected(self):
        self.manifest['installer'] = '../unrelated.dmg'
        self.write_bundle()
        with self.assertRaisesRegex(ValueError, 'filename'):
            validate_bundle(self.root)

    def test_old_release_cannot_replace_newer_feed(self):
        newer = {**self.config, 'build': '99999999.1'}
        feed = make_feed(newer, self.archive, 'signature', self.manifest['backup_download'], 'now')
        with patch('deploy_mirror.urlopen', return_value=io.BytesIO(feed)):
            with self.assertRaisesRegex(ValueError, 'newer'):
                check_not_older(self.manifest)

    def test_same_release_can_be_retried(self):
        feed = (self.root / 'helium-neo-backup.xml').read_bytes()
        with patch('deploy_mirror.urlopen', return_value=io.BytesIO(feed)):
            check_not_older(self.manifest)


if __name__ == '__main__':
    unittest.main()
