#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for steven_voice utility functions."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Mock tkinter before importing steven_voice since it may not be available in CI
tk_mock = MagicMock()
sys.modules["tkinter"] = tk_mock
sys.modules["tkinter.ttk"] = MagicMock()
sys.modules["tkinter.filedialog"] = MagicMock()
sys.modules["tkinter.messagebox"] = MagicMock()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from steven_voice import (
    apply_dictionary,
    load_config,
    load_dictionary,
    save_config,
    save_dictionary,
    save_history_entry,
    list_history,
    load_history_entry,
    DEFAULT_CONFIG,
)


class TestConfig(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._config_file = Path(self._tmpdir) / "config.json"

    def tearDown(self):
        if self._config_file.exists():
            self._config_file.unlink()
        os.rmdir(self._tmpdir)

    @patch("steven_voice.CONFIG_FILE")
    def test_load_config_defaults(self, mock_file):
        mock_file.exists.return_value = False
        cfg = load_config()
        self.assertEqual(cfg["whisper_model"], "medium")
        self.assertEqual(cfg["llm_temperature"], 0.3)

    @patch("steven_voice.CONFIG_FILE")
    def test_save_and_load_config(self, mock_file):
        mock_file.__class__ = Path
        real_path = self._config_file
        mock_file.exists = real_path.exists
        mock_file.__str__ = lambda s: str(real_path)
        mock_file.__fspath__ = lambda s: str(real_path)

        cfg = dict(DEFAULT_CONFIG)
        cfg["whisper_model"] = "large-v3"
        with patch("steven_voice.CONFIG_FILE", real_path):
            save_config(cfg)
            loaded = load_config()
        self.assertEqual(loaded["whisper_model"], "large-v3")


class TestHistory(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._hist_dir = Path(self._tmpdir)

    def tearDown(self):
        for f in self._hist_dir.glob("*.json"):
            f.unlink()
        os.rmdir(self._tmpdir)

    @patch("steven_voice.HISTORY_DIR")
    def test_save_and_load_history(self, mock_dir):
        mock_dir.__class__ = Path
        real = self._hist_dir

        entry = {"raw": "Hello", "polish": "Hello!", "trans": "你好"}
        with patch("steven_voice.HISTORY_DIR", real):
            path = save_history_entry(entry)
            loaded = load_history_entry(path)

        self.assertEqual(loaded["raw"], "Hello")
        self.assertEqual(loaded["polish"], "Hello!")
        self.assertEqual(loaded["trans"], "你好")
        self.assertTrue(path.exists())

    @patch("steven_voice.HISTORY_DIR")
    def test_list_history(self, mock_dir):
        real = self._hist_dir
        (real / "20260101_000000.json").write_text("{}", encoding="utf-8")
        (real / "20260102_000000.json").write_text("{}", encoding="utf-8")

        with patch("steven_voice.HISTORY_DIR", real):
            paths = list_history()

        self.assertEqual(len(paths), 2)
        self.assertGreater(paths[0].name, paths[1].name)


class TestDictionary(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._dict_file = Path(self._tmpdir) / "dictionary.json"

    def tearDown(self):
        if self._dict_file.exists():
            self._dict_file.unlink()
        os.rmdir(self._tmpdir)

    @patch("steven_voice.DICT_FILE")
    def test_load_empty_dictionary(self, mock_file):
        mock_file.exists = lambda: False
        entries = load_dictionary()
        self.assertEqual(entries, [])

    @patch("steven_voice.DICT_FILE")
    def test_save_and_load_dictionary(self, mock_file):
        real = self._dict_file
        with patch("steven_voice.DICT_FILE", real):
            entries = [
                {"enabled": True, "old": "你好", "new": "您好"},
                {"enabled": False, "old": "嗨", "new": "你好"},
            ]
            save_dictionary(entries)
            loaded = load_dictionary()
        self.assertEqual(len(loaded), 2)
        self.assertTrue(loaded[0]["enabled"])
        self.assertFalse(loaded[1]["enabled"])
        self.assertEqual(loaded[0]["old"], "你好")

    def test_apply_dictionary_basic(self):
        entries = [
            {"enabled": True, "old": "你好", "new": "您好"},
        ]
        result = apply_dictionary("你好世界", entries)
        self.assertEqual(result, "您好世界")

    def test_apply_dictionary_disabled_rule(self):
        entries = [
            {"enabled": False, "old": "你好", "new": "您好"},
        ]
        result = apply_dictionary("你好世界", entries)
        self.assertEqual(result, "你好世界")

    def test_apply_dictionary_multiple_rules(self):
        entries = [
            {"enabled": True, "old": "你好", "new": "您好"},
            {"enabled": True, "old": "世界", "new": "天下"},
        ]
        result = apply_dictionary("你好世界", entries)
        self.assertEqual(result, "您好天下")

    def test_apply_dictionary_empty_entries(self):
        result = apply_dictionary("你好世界", [])
        self.assertEqual(result, "你好世界")

    def test_apply_dictionary_missing_fields(self):
        entries = [{"enabled": True}]
        result = apply_dictionary("你好世界", entries)
        self.assertEqual(result, "你好世界")

    def test_apply_dictionary_empty_old(self):
        entries = [{"enabled": True, "old": "", "new": "test"}]
        result = apply_dictionary("你好世界", entries)
        self.assertEqual(result, "你好世界")


class TestTTSEnginePlay(unittest.TestCase):
    @patch("subprocess.Popen")
    @patch("subprocess.call", return_value=0)
    @patch("platform.system", return_value="Linux")
    def test_linux_aplay_no_ffplay_args(self, mock_sys, mock_call, mock_popen):
        from steven_voice import TTSEngine
        engine = TTSEngine({"tts_api_url": "http://localhost:8000", "tts_voice": "Vivian", "tts_speed": 1.0})
        engine.play("/tmp/test.wav")
        args = mock_popen.call_args[0][0]
        self.assertEqual(args[0], "aplay")
        self.assertNotIn("-nodisp", args)
        self.assertNotIn("-autoexit", args)


if __name__ == "__main__":
    unittest.main()
