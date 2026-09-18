"""CLI unit tests for `wia config` command."""

from pathlib import Path
from click.testing import CliRunner
from wia.cli.app import main


def test_config_cmd_show(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(main, ["config", "--show"])
    assert result.exit_code == 0
    assert "WIA Configuration" in result.output
    assert "Active AI Provider" in result.output
    assert "API Key Status" in result.output


def test_config_cmd_set_and_clear(tmp_path: Path, monkeypatch):
    test_config_path = tmp_path / "config.json"
    monkeypatch.setattr("wia.cli.commands.config_cmd.CONFIG_FILE_PATH", test_config_path)

    runner = CliRunner()

    # 1. Set provider
    res1 = runner.invoke(main, ["config", "--set-provider", "nvidia"])
    assert res1.exit_code == 0
    assert "Default AI provider set to 'nvidia'" in res1.output

    # 2. Set key
    res2 = runner.invoke(main, ["config", "--set-key", "nvapi-secret-key-12345"])
    assert res2.exit_code == 0
    assert "AI API key saved successfully" in res2.output

    # 3. Verify masking on show
    res3 = runner.invoke(main, ["config", "--show"])
    assert res3.exit_code == 0
    assert "nvapi-" in res3.output
    assert "..." in res3.output
    # Secret must never be printed unmasked
    assert "nvapi-secret-key-12345" not in res3.output

    # 4. Clear key
    res4 = runner.invoke(main, ["config", "--clear-key"])
    assert res4.exit_code == 0
    assert "Stored AI API key removed" in res4.output
