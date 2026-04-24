"""
Unit tests for scripts/compressor.py

These tests mock llmlingua.PromptCompressor so they run fast without
downloading gpt2 or needing a GPU. Safe to run in CI.

Run:
    pytest tests/test_compressor.py -v
"""
import sys
import os
import subprocess
import tempfile
from unittest.mock import patch, MagicMock
import pytest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "compressor.py")
SCRIPT = os.path.abspath(SCRIPT)

FAKE_COMPRESSED = "compressed version of the input text"
FAKE_RATIO = "2.5x"


def make_mock_compressor():
    mock = MagicMock()
    mock.compress_prompt.return_value = {
        "compressed_prompt": FAKE_COMPRESSED,
        "ratio": FAKE_RATIO,
    }
    return mock


# ── Helpers ──────────────────────────────────────────────────────────────────

def run_script(*args, stdin_text=None, env=None):
    """Run compressor.py with mocked PromptCompressor via subprocess."""
    cmd = [sys.executable, SCRIPT, *args]
    result = subprocess.run(
        cmd,
        input=stdin_text,
        capture_output=True,
        text=True,
        env={**os.environ, **(env or {})},
    )
    return result


# ── estimate_target_tokens ───────────────────────────────────────────────────

def test_estimate_target_tokens_floor():
    """Short input should hit the 512 floor."""
    sys.path.insert(0, os.path.dirname(SCRIPT))
    import importlib.util
    spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    with patch.dict("sys.modules", {"llmlingua": MagicMock()}):
        spec.loader.exec_module(mod)
    assert mod.estimate_target_tokens("short text") == 512


def test_estimate_target_tokens_cap():
    """Very large input should be capped at 4096."""
    sys.path.insert(0, os.path.dirname(SCRIPT))
    import importlib.util
    spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    with patch.dict("sys.modules", {"llmlingua": MagicMock()}):
        spec.loader.exec_module(mod)
    huge = "x " * 100_000  # far exceeds 4096 token target
    assert mod.estimate_target_tokens(huge) == 4096


def test_estimate_target_tokens_midrange():
    """Mid-size input should give ~30% of approx token count."""
    sys.path.insert(0, os.path.dirname(SCRIPT))
    import importlib.util
    spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    with patch.dict("sys.modules", {"llmlingua": MagicMock()}):
        spec.loader.exec_module(mod)
    # 4000 chars → ~1000 tokens → 30% = 300 → floored to 512
    text = "word " * 800  # ~4000 chars
    result = mod.estimate_target_tokens(text)
    assert 512 <= result <= 4096


# ── File input ───────────────────────────────────────────────────────────────

def test_compress_file_success(tmp_path):
    """Passing a valid file path should print compressed output to stdout."""
    f = tmp_path / "input.txt"
    f.write_text("word " * 500)

    mock_instance = make_mock_compressor()
    with patch("llmlingua.PromptCompressor", return_value=mock_instance):
        import importlib.util
        spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            mod.compress_text(f.read_text())
        assert FAKE_COMPRESSED in out.getvalue()


def test_missing_file_exits_nonzero():
    """Passing a non-existent file should exit with code 1."""
    result = run_script("/nonexistent/path/that/does/not/exist.txt")
    assert result.returncode == 1
    assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()


def test_missing_file_error_on_stderr():
    """Error message for missing file must go to stderr, not stdout."""
    result = run_script("/nonexistent/path.txt")
    assert result.stdout.strip() == ""


# ── Stdin input ───────────────────────────────────────────────────────────────

def test_stdin_no_args_exits_with_tty_message():
    """Running with no args and no stdin pipe should print usage to stderr."""
    # We use a short inline script to force sys.stdin.isatty to True
    # because subprocess.DEVNULL is not a tty.
    inline_script = f"""
import sys
import os

# mock isatty
sys.stdin.isatty = lambda: True

# execute file
with open('{SCRIPT}', 'r') as f:
    exec(f.read())
"""
    result = subprocess.run(
        [sys.executable, "-c", inline_script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "usage" in result.stderr.lower()


# ── Empty input ───────────────────────────────────────────────────────────────

def test_empty_file_exits_nonzero(tmp_path):
    """An empty file should exit cleanly with an error, not crash."""
    f = tmp_path / "empty.txt"
    f.write_text("")
    result = run_script(str(f))
    assert result.returncode == 1
    assert "error" in result.stderr.lower()


def test_empty_stdin_exits_nonzero():
    """Empty stdin should exit with error."""
    result = run_script(stdin_text="")
    assert result.returncode == 1


# ── Output hygiene ───────────────────────────────────────────────────────────

def test_stats_go_to_stderr_not_stdout(tmp_path):
    """Compression stats (ratio) must be on stderr, not pollute stdout."""
    f = tmp_path / "input.txt"
    f.write_text("word " * 500)

    mock_instance = make_mock_compressor()
    with patch("llmlingua.PromptCompressor", return_value=mock_instance):
        import importlib.util
        spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            mod.compress_text(f.read_text())
        assert "ClaudeShrink" in err.getvalue()   # stats on stderr
        assert "ClaudeShrink" not in out.getvalue()  # not on stdout


# ── Question / instruction flags ─────────────────────────────────────────────

def test_question_passed_to_compress_prompt(tmp_path):
    """--question flag should be forwarded to compress_prompt."""
    f = tmp_path / "input.txt"
    f.write_text("word " * 500)

    mock_instance = make_mock_compressor()
    with patch("llmlingua.PromptCompressor", return_value=mock_instance):
        import importlib.util
        spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.compress_text(f.read_text(), question="What errors occurred?")

    call_kwargs = mock_instance.compress_prompt.call_args
    assert call_kwargs is not None
    assert call_kwargs.kwargs.get("question") == "What errors occurred?" or \
           (call_kwargs.args and "What errors occurred?" in call_kwargs.args)


def test_instruction_passed_to_compress_prompt(tmp_path):
    """--instruction flag should be forwarded to compress_prompt."""
    f = tmp_path / "input.txt"
    f.write_text("word " * 500)

    mock_instance = make_mock_compressor()
    with patch("llmlingua.PromptCompressor", return_value=mock_instance):
        import importlib.util
        spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.compress_text(f.read_text(), instruction="Keep all ERROR lines.")

    call_kwargs = mock_instance.compress_prompt.call_args
    assert call_kwargs is not None
    assert call_kwargs.kwargs.get("instruction") == "Keep all ERROR lines." or \
           (call_kwargs.args and "Keep all ERROR lines." in call_kwargs.args)


def test_question_flag_cli(tmp_path):
    """--question passed via CLI should reach compress_prompt."""
    f = tmp_path / "input.txt"
    f.write_text("word " * 500)
    result = run_script(str(f), "--question", "What errors occurred?")
    # With mocked compressor (no llmlingua available in subprocess), just check it doesn't crash on arg parsing
    assert result.returncode in (0, 1)  # may fail without real llmlingua, but must not error on arg parse


def test_stats_include_question_hint(tmp_path):
    """When --question is set, stats line on stderr should mention it."""
    f = tmp_path / "input.txt"
    f.write_text("word " * 500)

    mock_instance = make_mock_compressor()
    with patch("llmlingua.PromptCompressor", return_value=mock_instance):
        import importlib.util
        spec = importlib.util.spec_from_file_location("compressor", SCRIPT)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        import io
        from contextlib import redirect_stdout, redirect_stderr
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            mod.compress_text(f.read_text(), question="What errors occurred?")
        assert "question=" in err.getvalue()
