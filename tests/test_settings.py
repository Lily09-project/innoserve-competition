"""Configuration failures cannot select unintended model locations."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='settings-contract-')
        self.root=Path(self.temp.name)
        self.root_patch=patch.object(settings,'ROOT',self.root);self.root_patch.start()
        self.env_patch=patch.dict(os.environ,{k:v for k,v in os.environ.items() if not k.startswith('INNOSERVE_')},clear=True);self.env_patch.start()

    def tearDown(self):
        self.env_patch.stop();self.root_patch.stop();self.temp.cleanup()

    def write(self,value):
        (self.root/'config.local.json').write_text(json.dumps(value),encoding='utf-8-sig')

    def test_missing_config_uses_root_relative_default(self):
        self.assertEqual(settings.config(),{})
        self.assertEqual(settings.optional_asset_path('missing','runtime'),self.root/'runtime')
        with self.assertRaises(RuntimeError):settings.asset_path('missing')

    def test_bom_and_environment_precedence(self):
        (self.root/'檔案').write_text('x');(self.root/'override').write_text('y')
        self.write({'asset':'檔案'})
        self.assertEqual(settings.asset_path('asset'),self.root/'檔案')
        with patch.dict(os.environ,{'INNOSERVE_ASSET':'override'}):
            self.assertEqual(settings.asset_path('asset'),self.root/'override')

    def test_bad_json_and_non_object_rejected_without_raw_values(self):
        (self.root/'config.local.json').write_text('{ secret-private-path',encoding='utf-8')
        with self.assertRaisesRegex(ValueError,'Invalid local configuration JSON') as error:settings.config()
        self.assertNotIn('secret-private-path',str(error.exception))
        for value in ([],None,False,42):
            self.write(value)
            with self.assertRaises(ValueError):settings.config()

    def test_bad_path_types_and_missing_assets_rejected(self):
        for value in (False,17,{},[], '   '):
            self.write({'asset':value})
            with self.assertRaises(ValueError):settings.asset_path('asset')
        self.write({'asset':'unavailable'})
        with self.assertRaises(FileNotFoundError):settings.asset_path('asset')

    def test_relative_path_does_not_depend_on_working_directory(self):
        self.write({'asset':'relative'})
        (self.root/'relative').write_text('x')
        with patch('pathlib.Path.cwd',return_value=self.root/'elsewhere'):
            self.assertEqual(settings.asset_path('asset'),self.root/'relative')

    def test_execution_values_validate_and_env_override(self):
        self.assertEqual(settings.execution_settings()['network_timeout_seconds'],100)
        self.write({'network_timeout_seconds':120})
        with patch.dict(os.environ,{'INNOSERVE_NETWORK_TIMEOUT_SECONDS':'140'}):
            self.assertEqual(settings.execution_settings()['network_timeout_seconds'],140)
        for value in (False,0,-1,1.5,'bad'):
            self.write({'network_timeout_seconds':value})
            with self.assertRaises(ValueError):settings.execution_settings()
        self.write({'wsl_distribution':' '})
        with self.assertRaises(ValueError):settings.execution_settings()
