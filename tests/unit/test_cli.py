from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from qe_platform.cli import cli


class TestCLI:
    def test_parse_command(self, demo_spec_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["parse", str(demo_spec_path)])
        assert result.exit_code == 0
        assert "Petstore API" in result.output
        assert "7" in result.output  # 7 endpoints

    def test_parse_shows_endpoints(self, demo_spec_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["parse", str(demo_spec_path)])
        assert "/pets" in result.output
        assert "GET" in result.output
        assert "POST" in result.output
        assert "DELETE" in result.output

    def test_parse_shows_auth(self, demo_spec_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["parse", str(demo_spec_path)])
        assert "[AUTH]" in result.output

    def test_parse_nonexistent_file(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["parse", "/nonexistent.yaml"])
        assert result.exit_code != 0

    def test_demo_command(self, demo_spec_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["demo"])
        assert result.exit_code == 0
        assert "Petstore API" in result.output

    def test_help(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "QE Intelligent Test Generation Platform" in result.output
