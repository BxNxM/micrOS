import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from toolkit.DevEnvCompile import Compile
from toolkit.dashboard_apps import SystemTest


class MicrOSVersionTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.compiler = Compile()
        self.compiler.micrOS_dir_path = self.temp_dir.name

    def write_version(self, version):
        Path(self.temp_dir.name, 'Shell.py').write_text(
            "# Unrelated historical version: 1.2.3-4\n"
            "class Shell:\n    MICROS_VERSION = {!r}\n".format(version))

    def test_reads_current_and_legacy_repository_versions(self):
        for version in ('3.7.2', '3.7.2-0', '3.7.2-12'):
            with self.subTest(version=version):
                self.write_version(version)
                self.assertEqual(version, self.compiler.get_micros_version_from_repo())

    def test_reads_current_and_legacy_device_versions(self):
        self.write_version('3.7.2')
        for version in ('3.7.2', '3.7.2-0', '3.7.2-12'):
            for quote in ('"', "'"):
                with self.subTest(version=version, quote=quote):
                    config = '{"other": "9.8.7-6", ' + quote + 'version' + quote
                    config += ': ' + quote + version + quote + '}'
                    self.assertEqual(('3.7.2', version),
                                     self.compiler.get_micrOS_version(config))

    def test_invalid_device_version_does_not_match_unrelated_fields(self):
        self.write_version('3.7.2')
        for version in ('3x7x2', '3.7.2-bad', '3.7.2.1'):
            with self.subTest(version=version):
                config = '{"other": "9.8.7-6", "version": "' + version + '"}'
                with patch.object(self.compiler, 'console') as console:
                    self.assertEqual(('3.7.2', 0), self.compiler.get_micrOS_version(config))
                console.assert_called_once()
                self.assertEqual('warn', console.call_args.kwargs['state'])

    def test_system_version_check_accepts_both_formats(self):
        for version in ('3.7.2', '3.7.2-0', '3.7.2-12'):
            with self.subTest(version=version):
                client = Mock()
                client.execute.return_value = (True, version + '\n')
                with patch.object(SystemTest, 'CLIENT', client):
                    self.assertTrue(SystemTest.micrOS_get_version()[0])
                client.execute.side_effect = [
                    (True, '[]'), (True, version + '\n'),
                    (True, '[MICROS] [CONF] [TASK] [EXEC]')]
                with patch.object(SystemTest, 'CLIENT', client), \
                        patch.object(SystemTest, '_add_metrics'):
                    self.assertTrue(SystemTest.shell_cmds_check()[0])


if __name__ == '__main__':
    unittest.main()
