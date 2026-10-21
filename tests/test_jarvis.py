"""Тесты Jarvis: разбор ответов LLM, слово пробуждения, диспетчеризация команд.

Запуск:  python -m unittest discover -s tests -v
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JARVIS_DIR = os.path.join(ROOT, "jarvis")
sys.path.insert(0, JARVIS_DIR)

import config  # noqa: E402
import context  # noqa: E402
import file_ops  # noqa: E402
import llm  # noqa: E402
import recognition  # noqa: E402


class TestExtractJson(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(
            llm.extract_json('{"intent": "help", "args": {}}'),
            {"intent": "help", "args": {}},
        )

    def test_markdown_fence(self):
        text = '```json\n{"intent": "volume", "args": {"volume": 30}}\n```'
        self.assertEqual(
            llm.extract_json(text),
            {"intent": "volume", "args": {"volume": 30}},
        )

    def test_text_around_json(self):
        text = 'Конечно! Вот результат: {"intent": "open_app", "args": {"app": "firefox"}} готово'
        self.assertEqual(
            llm.extract_json(text),
            {"intent": "open_app", "args": {"app": "firefox"}},
        )

    def test_nested_json(self):
        text = '{"intent": "create_file", "args": {"path": "~/a.txt", "content": "x"}}'
        self.assertEqual(llm.extract_json(text)["args"]["content"], "x")

    def test_invalid_raises(self):
        with self.assertRaises(llm.LLMError):
            llm.extract_json("не json вообще")
        with self.assertRaises(llm.LLMError):
            llm.extract_json("")

    def test_json_inside_reasoning_text(self):
        """Модель объясняет по-английски, но JSON внутри есть."""
        text = (
            "We need output JSON only. User says open folder ~. So intent is: "
            '{"intent": "open_folder", "args": {"path": "~/"}, "answer": "Открываю"}'
        )
        result = llm.extract_json(text)
        self.assertEqual(result["intent"], "open_folder")

    def test_python_style_dict(self):
        self.assertEqual(
            llm.extract_json("{'intent': 'help', 'args': {}}")["intent"], "help"
        )

    def test_capitalized_true_false(self):
        result = llm.extract_json(
            '{"intent": "write_file", "args": {"path": "~/a", "append": False}}'
        )
        self.assertIs(result["args"]["append"], False)

    def test_fence_with_python_code_and_json(self):
        """В блоке кода — текст на Python, ниже корректный JSON."""
        content = (
            "```python\nprint('привет')\n```\n"
            '{"intent": "create_file", "args": {"path": "~/rt.py", "content": "x"}}'
        )
        self.assertEqual(llm.extract_json(content)["intent"], "create_file")


class TestNormalizeResult(unittest.TestCase):
    def test_unknown_intent_becomes_answer(self):
        result = llm.normalize_result({"intent": "launch_rocket", "answer": "нет"})
        self.assertEqual(result["intent"], "answer")

    def test_args_not_dict(self):
        result = llm.normalize_result({"intent": "help", "args": ["a"]})
        self.assertEqual(result["args"], {})

    def test_case_insensitive(self):
        self.assertEqual(llm.normalize_result({"intent": "VOLUME"})["intent"], "volume")


class TestBuildMessages(unittest.TestCase):
    def test_no_duplicate_current_message(self):
        history = [
            {"role": "user", "content": "привет"},
            {"role": "assistant", "content": "здравствуйте"},
            {"role": "user", "content": "открой браузер"},
        ]
        messages = llm.build_messages(history, "открой браузер")
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(sum(m["content"] == "открой браузер" for m in messages), 1)


class TestWakeWord(unittest.TestCase):
    def test_latin(self):
        self.assertEqual(recognition.find_wake_word("Jarvis, открой браузер"),
                         (True, "открой браузер"))

    def test_cyrillic(self):
        found, rest = recognition.find_wake_word("Джарвис что открыто")
        self.assertTrue(found)
        self.assertEqual(rest, "что открыто")

    def test_fuzzy_google_variant(self):
        found, rest = recognition.find_wake_word("жарвис громче")
        self.assertTrue(found)
        self.assertEqual(rest, "громче")

    def test_only_wake_word(self):
        self.assertEqual(recognition.find_wake_word("Джарвис"), (True, ""))

    def test_absent(self):
        self.assertEqual(recognition.find_wake_word("открой браузер"), (False, ""))


class TestFileSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = self.tmp.name
        self.patcher = mock.patch.object(config, "ALLOWED_FILE_ROOTS", [self.root])
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.tmp.cleanup()

    def test_create_and_delete_inside_root(self):
        path = os.path.join(self.root, "note.txt")
        self.assertEqual(file_ops.create_file(path, "привет"), path)
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "привет")
        self.assertTrue(file_ops.delete_file(path))
        self.assertFalse(os.path.exists(path))

    def test_create_outside_root_rejected(self):
        self.assertIsNone(file_ops.create_file("/etc/jarvis_test.txt", "x"))
        self.assertFalse(os.path.exists("/etc/jarvis_test.txt"))

    def test_delete_outside_root_rejected(self):
        victim = os.path.join(self.root, "..", "outside.txt")
        with open(victim, "w", encoding="utf-8") as f:
            f.write("x")
        try:
            self.assertFalse(file_ops.delete_file(victim))
            self.assertTrue(os.path.exists(victim))
        finally:
            os.remove(victim)

    def test_create_does_not_overwrite(self):
        path = os.path.join(self.root, "keep.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("важное")
        self.assertIsNone(file_ops.create_file(path, "новое"))
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "важное")

    def test_format_upper(self):
        path = os.path.join(self.root, "t.txt")
        file_ops.create_file(path, "привет мир")
        self.assertTrue(file_ops.format_text_file(path, "upper"))
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "ПРИВЕТ МИР")

    def test_write_file_overwrites(self):
        path = os.path.join(self.root, "code.py")
        file_ops.create_file(path, "старое")
        self.assertEqual(file_ops.write_file(path, "новое"), path)
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "новое")

    def test_write_file_appends(self):
        path = os.path.join(self.root, "log.txt")
        file_ops.write_file(path, "первая")
        file_ops.write_file(path, "вторая", append=True)
        with open(path, encoding="utf-8") as f:
            self.assertEqual(f.read(), "первая\nвторая")

    def test_write_and_read_roundtrip(self):
        path = os.path.join(self.root, "calc.py")
        code = "print('калькулятор')\n"
        file_ops.write_file(path, code)
        self.assertEqual(file_ops.read_file(path), code)

    def test_write_outside_root_rejected(self):
        self.assertIsNone(file_ops.write_file("/etc/jarvis_hack.txt", "x"))
        self.assertFalse(os.path.exists("/etc/jarvis_hack.txt"))


class TestContext(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dialogue = os.path.join(self.tmp.name, "dialogue.json")
        self.patches = [
            mock.patch.object(context, "DATA_DIR", self.tmp.name),
            mock.patch.object(context, "DIALOGUE_PATH", self.dialogue),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_history_trimmed(self):
        for i in range(context.MAX_CONTEXT + 5):
            context.append_message("user", f"msg{i}")
        messages = context.load_dialogue()
        self.assertEqual(len(messages), context.MAX_CONTEXT)
        self.assertEqual(messages[-1]["content"], f"msg{context.MAX_CONTEXT + 4}")

    def test_clear(self):
        context.append_message("user", "привет")
        context.clear_dialogue()
        self.assertEqual(context.get_context(), [])

    def test_corrupt_file(self):
        with open(self.dialogue, "w", encoding="utf-8") as f:
            f.write("{битый json")
        self.assertEqual(context.load_dialogue(), [])


class TestLlmFallback(unittest.TestCase):
    """Перебор моделей и повторы при перегрузке (429)."""

    def setUp(self):
        patcher = mock.patch.object(llm, "OPENROUTER_API_KEY", "test-key")
        patcher.start()
        self.addCleanup(patcher.stop)
        sleep_patcher = mock.patch.object(llm.time, "sleep")
        self.sleep = sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

    @staticmethod
    def _response(status_code, payload=None, headers=None):
        response = mock.Mock()
        response.status_code = status_code
        response.headers = headers or {}
        response.json.return_value = payload or {}
        response.text = json.dumps(payload or {})
        return response

    def _chat_response(self, content):
        return self._response(200, {"choices": [{"message": {"content": content}}]})

    def test_model_order_has_no_duplicates(self):
        models = llm._models()
        self.assertEqual(len(models), len(set(models)))
        self.assertEqual(models[0], config.OPENROUTER_MODEL)

    def test_retry_after_header_is_used(self):
        response = self._response(429, headers={"Retry-After": "7"})
        self.assertEqual(llm._retry_after(response, attempt=0), 7.0)

    def test_missing_api_key_reported(self):
        with mock.patch.object(llm, "OPENROUTER_API_KEY", ""):
            with self.assertRaises(llm.LLMError) as ctx:
                llm.ask_llm([{"role": "user", "content": "привет"}])
        self.assertIn("OPENROUTER_API_KEY", str(ctx.exception))

    def test_retry_after_is_capped(self):
        response = self._response(429, headers={"Retry-After": "999"})
        self.assertEqual(llm._retry_after(response, attempt=0), 30.0)

    def test_falls_back_to_next_model_on_429(self):
        busy = self._response(429, {"error": "rate limited"})
        ok = self._chat_response('{"intent": "help", "args": {}}')
        with mock.patch.object(llm.requests, "post", side_effect=[busy, ok]) as post:
            result = llm.ask_llm([{"role": "user", "content": "помощь"}])
        self.assertEqual(result["intent"], "help")
        self.assertEqual(post.call_count, 2)  # первая модель упала, вторая ответила

    def test_json_object_requested_with_token_budget(self):
        """response_format просим всегда, а бюджет токенов хватает на рассуждения."""
        ok = self._chat_response('{"intent": "help", "args": {}}')
        with mock.patch.object(llm.requests, "post", return_value=ok) as post:
            llm.ask_llm([{"role": "user", "content": "помощь"}])
        payload = post.call_args.kwargs["json"]
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertGreaterEqual(payload["max_tokens"], 1000)

    def test_retries_without_response_format_on_400(self):
        """Модель без поддержки response_format — повторяем без этого поля."""
        bad = self._response(400, {"error": "response_format not supported"})
        ok = self._chat_response('{"intent": "help", "args": {}}')
        with mock.patch.object(llm.requests, "post", side_effect=[bad, ok]) as post:
            self.assertEqual(llm.ask_llm([{"role": "user", "content": "x"}])["intent"], "help")
        self.assertIn("response_format", post.call_args_list[0].kwargs["json"])
        self.assertNotIn("response_format", post.call_args_list[1].kwargs["json"])

    def test_all_models_busy_raises_busy_error(self):
        busy = self._response(429, {"error": "rate limited"})
        with mock.patch.object(llm, "LLM_MAX_RETRIES", 0), \
             mock.patch.object(llm, "OPENROUTER_MODEL", "m1"), \
             mock.patch.object(llm, "OPENROUTER_FALLBACK_MODELS", ["m2"]), \
             mock.patch.object(llm.requests, "post", return_value=busy):
            with self.assertRaises(llm.LLMBusyError):
                llm.ask_llm([{"role": "user", "content": "привет"}])

    def test_understand_reports_busy(self):
        with mock.patch.object(llm, "ask_llm", side_effect=llm.LLMBusyError("429")):
            result = llm.understand("привет")
        self.assertEqual(result["intent"], "busy")

    def test_empty_choices_reported(self):
        empty = self._response(200, {"choices": []})
        with mock.patch.object(llm, "LLM_MAX_RETRIES", 0), \
             mock.patch.object(llm, "OPENROUTER_FALLBACK_MODELS", []), \
             mock.patch.object(llm.requests, "post", return_value=empty):
            with self.assertRaises(llm.LLMError) as ctx:
                llm.ask_llm([{"role": "user", "content": "привет"}])
        self.assertIn("choices", str(ctx.exception))

    def test_bad_api_key_reported_without_request(self):
        with mock.patch.object(llm, "OPENROUTER_API_KEY", ""), \
             mock.patch.object(llm.requests, "post") as post:
            with self.assertRaises(llm.LLMError):
                llm.ask_llm([{"role": "user", "content": "привет"}])
        post.assert_not_called()  # без ключа запрос не уходит


class TestCli(unittest.TestCase):
    def test_help_and_exit_in_text_mode(self):
        env = dict(os.environ, JARVIS_TMP=tempfile.mkdtemp(),
                   JARVIS_DATA_DIR=tempfile.mkdtemp(),
                   OPENROUTER_API_KEY="")
        result = subprocess.run(
            [sys.executable, os.path.join(JARVIS_DIR, "jarvis.py"),
             "--text", "--no-tts"],
            input="помощь\nвыход\n", capture_output=True, text=True,
            timeout=60, env=env, cwd=tempfile.gettempdir(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Команды Jarvis", result.stdout)
        self.assertIn("До свидания", result.stdout)

    def test_unrecognized_command_without_llm(self):
        env = dict(os.environ, JARVIS_TMP=tempfile.mkdtemp(),
                   JARVIS_DATA_DIR=tempfile.mkdtemp(),
                   OPENROUTER_API_KEY="")
        result = subprocess.run(
            [sys.executable, os.path.join(JARVIS_DIR, "jarvis.py"),
             "--text", "--no-tts"],
            input="расскажи стишок\nвыход\n", capture_output=True, text=True,
            timeout=60, env=env, cwd=tempfile.gettempdir(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Не удалось понять команду", result.stdout)
        self.assertIn("OPENROUTER_API_KEY", result.stdout)


if __name__ == "__main__":
    unittest.main()
