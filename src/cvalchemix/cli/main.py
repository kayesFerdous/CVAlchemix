import asyncio
import os
import shutil
import sys
import shlex
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from cvalchemix.config.config import config_dir, get_config_path, load_config, save_config

app = typer.Typer(help="CVAlchemix CLI")
console = Console()

API_KEY_FIELD = "gemini_api_key"
CV_PATH_FIELD = "base_cv_path"
PACKAGE_NAMES = ("cvalchemix", "browse")


def _mask_api_key(value: str) -> str:
	secret = value.strip()
	if not secret:
		return "(not set)"
	if len(secret) <= 4:
		return "*" * len(secret)
	return f"{'*' * (len(secret) - 4)}{secret[-4:]}"


def _load_required_config() -> tuple[str, str]:
	config = load_config()
	api_key = str(config.get(API_KEY_FIELD, "")).strip()
	cv_path = str(config.get(CV_PATH_FIELD, "")).strip()

	if not api_key or not cv_path:
		console.print(
			"[red]Missing configuration.[/red] Run [bold]cvalchemix configure[/bold] first."
		)
		raise typer.Exit(code=1)

	return api_key, cv_path


async def _run_agent(url: str, output_dir: str, api_key: str, cv_text: str) -> str | None:
	"""Run the job-application agent."""
	from google.genai import Client
	from cvalchemix.llm.gemini import GeminiLLM
	from cvalchemix.agents.job_application_agnet import JobApplicationAgent

	client = Client(api_key=api_key)
	llm = GeminiLLM(client)
	agent = JobApplicationAgent(llm, cv=cv_text)
	
	return await agent.run(url, output_dir)


@app.command()
def configure() -> None:
	"""Configure API key and base CV path."""
	api_key = typer.prompt(
		"Gemini API key",
		hide_input=True,
		confirmation_prompt=True,
	).strip()

	cv_path_raw = typer.prompt("Path to your base CV text file").strip()
	cv_path = Path(cv_path_raw).expanduser().resolve()

	if not cv_path.exists() or not cv_path.is_file():
		console.print(f"[red]Invalid CV file path:[/red] {cv_path}")
		raise typer.Exit(code=1)

	save_config({API_KEY_FIELD: api_key, CV_PATH_FIELD: str(cv_path)})
	console.print(f"[green]Configuration saved.[/green] {get_config_path()}")


@app.command("show-config")
def show_config() -> None:
	"""Show current saved configuration."""
	config = load_config()
	if not config:
		console.print("[yellow]No configuration found.[/yellow] Run [bold]cvalchemix configure[/bold].")
		return

	table = Table(title="CVAlchemix Configuration")
	table.add_column("Key", style="cyan")
	table.add_column("Value", style="white")

	for key in sorted(config.keys()):
		value = str(config[key])
		if key == API_KEY_FIELD:
			value = _mask_api_key(value)
		table.add_row(key, value)

	table.add_row("config_file", str(get_config_path()))

	console.print(table)


@app.command()
def delete(
	data_only: bool = typer.Option(
		False,
		"--data-only",
		help="Delete local CVAlchemix data only, keep the installed CLI.",
	),
	yes: bool = typer.Option(
		False,
		"--yes",
		"-y",
		help="Skip the confirmation prompt.",
	),
) -> None:
	"""Uninstall CVAlchemix and delete local data traces."""

	def _handoff_uninstall() -> None:
		pipx = shutil.which("pipx")
		if pipx:
			commands = [
				f"{shlex.quote(pipx)} uninstall {shlex.quote(package)} >/dev/null 2>&1 || true"
				for package in PACKAGE_NAMES
			]
			os.execv("/bin/sh", ["sh", "-lc", "; ".join(commands)])

		os.execv(
			sys.executable,
			[
				sys.executable,
				"-m",
				"pip",
				"uninstall",
				"-y",
				*PACKAGE_NAMES,
			],
		)

	def _remove_installer_path_blocks() -> list[tuple[Path, str]]:
		failed: list[tuple[Path, str]] = []
		profile_files = [Path.home() / ".profile", Path.home() / ".zprofile"]
		marker = "# Added by CVAlchemix installer"
		line = 'export PATH="$HOME/.local/bin:$PATH"'

		for profile_path in profile_files:
			if not profile_path.exists():
				continue

			try:
				lines = profile_path.read_text(encoding="utf-8").splitlines()
			except OSError as exc:
				failed.append((profile_path, str(exc)))
				continue

			new_lines: list[str] = []
			skip_next = False
			for current in lines:
				if current == marker:
					skip_next = True
					continue

				if skip_next and current == line:
					skip_next = False
					continue

				skip_next = False
				new_lines.append(current)

			try:
				profile_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")
			except OSError as exc:
				failed.append((profile_path, str(exc)))

		return failed

	def _remove_data_dirs() -> tuple[list[Path], list[tuple[Path, str]]]:
		removed: list[Path] = []
		failed: list[tuple[Path, str]] = []
		candidate_dirs = {
			config_dir,
			Path.home() / ".config" / "cvalchemix",
			Path.home() / ".config" / "CVAlchemix",
			Path.home() / ".cache" / "cvalchemix",
			Path.home() / ".local" / "share" / "cvalchemix",
		}

		for path in sorted(candidate_dirs, key=str):
			if not path.exists():
				continue
			try:
				shutil.rmtree(path)
				removed.append(path)
			except OSError as exc:
				failed.append((path, str(exc)))

		return removed, failed

	mode = "delete all local data" if data_only else "uninstall the CLI and delete all local data"
	if not yes:
		confirmed = typer.confirm(
			f"This will permanently {mode}. Continue?",
			default=False,
		)
		if not confirmed:
			console.print("[yellow]Delete cancelled.[/yellow]")
			return

	cleanup_failures: list[str] = []
	if not data_only:
		for profile, reason in _remove_installer_path_blocks():
			cleanup_failures.append(f"Could not update profile {profile}: {reason}")

	removed_data, data_failures = _remove_data_dirs()

	if not data_only:
		console.print("[green]Local cleanup completed.[/green]")

	if removed_data:
		console.print("[green]Deleted local data directories:[/green]")
		for path in removed_data:
			console.print(f"  - {path}")
	else:
		console.print("[yellow]No local data directories were found.[/yellow]")

	if cleanup_failures or data_failures:
		console.print("[yellow]Cleanup warnings:[/yellow]")
		for message in cleanup_failures:
			console.print(f"  - {message}")
		for path, reason in data_failures:
			console.print(f"  - Could not remove {path}: {reason}")
		if data_only:
			raise typer.Exit(code=1)

	console.print("[green]Delete complete.[/green]")

	if not data_only:
		console.print("[cyan]Handing off to package uninstaller...[/cyan]")
		_handoff_uninstall()

	raise typer.Exit(code=0)


@app.command()
def generate(
	url: str = typer.Argument(..., help="LinkedIn job post URL"),
	output: str = typer.Option("./output", "--output", "-o", help="Output directory"),
) -> None:
	"""Generate a tailored CV PDF from a LinkedIn job post URL."""
	api_key, cv_path_str = _load_required_config()
	cv_path = Path(cv_path_str)

	if not cv_path.exists() or not cv_path.is_file():
		console.print(
			"[red]Configured CV path is invalid.[/red] Run [bold]cvalchemix configure[/bold] again."
		)
		raise typer.Exit(code=1)

	try:
		cv_text = cv_path.read_text(encoding="utf-8")
	except OSError:
		console.print("[red]Could not read the configured CV file.[/red]")
		raise typer.Exit(code=1)

	try:
		output_pdf = asyncio.run(_run_agent(url, output, api_key, cv_text))
	except ModuleNotFoundError as exc:
		missing_name = exc.name or ""
		if missing_name == "playwright" or missing_name.startswith("playwright."):
			console.print(
				"[red]Missing dependency: playwright.[/red] Install it and run "
				"[bold]playwright install[/bold], then retry."
			)
			raise typer.Exit(code=1)

		console.print("[red]A required module is missing.[/red] Please check your installation.")
		raise typer.Exit(code=1)
	except Exception as exc:
		console.print(f"[red]Generation failed:[/red] {exc}")
		raise typer.Exit(code=1)

	if output_pdf:
		console.print(f"\n[green]✔ CV generated successfully:[/green] {output_pdf}")
		return

	console.print("[red]Generation finished without producing a PDF.[/red]")
	raise typer.Exit(code=1)


def main() -> None:
	app()


if __name__ == "__main__":
	app()
