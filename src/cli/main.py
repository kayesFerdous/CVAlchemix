import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from src.config.config import get_config_path, load_config, save_config

app = typer.Typer(help="CVAlchemix CLI")
console = Console()

API_KEY_FIELD = "gemini_api_key"
CV_PATH_FIELD = "base_cv_path"


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
	# Support modules that import from src-rooted packages like "llm" and "agents".
	src_dir = Path(__file__).resolve().parents[1]
	src_dir_str = str(src_dir)
	if src_dir_str not in sys.path:
		sys.path.insert(0, src_dir_str)

	from google.genai import Client
	from src.llm.gemini import GeminiLLM
	from src.agents.job_application_agnet import JobApplicationAgent

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
