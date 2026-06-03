"""cvalchemix conv – paste LaTeX, compile to PDF, open & exit."""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

BASE_OUTPUT_DIR = Path("/home/kayes/Documents/kayes/job_hunt")

# Sentinel the user types on its own line to finish pasting.
_END_MARKER = "END"

_PDFTEX_UNICODE_DIRECTIVE_RE = re.compile(
    r"""
    ^\s*
    (?:
        \\input\s*\{glyphtounicode\}
        |
        \\input\s+glyphtounicode
        |
        \\pdfgentounicode\s*=\s*\d+
    )
    \s*(?:%.*)?$
    """,
    re.VERBOSE,
)

_LINEBREAK_BARE_SPACING_RE = re.compile(
    r"(?<!\\)\\\\(?!\\)\s*\[\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+))\s*\]"
)


def _normalize_tex_for_tectonic(tex_content: str) -> tuple[str, int, int]:
    """Normalize common pasted-LaTeX issues before compiling with Tectonic.

    Tectonic uses a XeTeX-based engine. Common resume templates copied from
    pdfLaTeX examples often include ``glyphtounicode`` and ``\\pdfgentounicode``
    lines for searchable PDFs, but those pdfTeX primitives fail under Tectonic.
    XeTeX already emits Unicode text without those directives. LLM output also
    sometimes writes line breaks like ``\\ [2]``; TeX requires a dimension unit,
    so those bare numeric spacing values are treated as points.
    """
    normalized_lines: list[str] = []
    removed_count = 0
    fixed_spacing_count = 0

    for line in tex_content.splitlines(keepends=True):
        if _PDFTEX_UNICODE_DIRECTIVE_RE.match(line.rstrip("\r\n")):
            removed_count += 1
            continue
        line, line_fixed_spacing_count = _LINEBREAK_BARE_SPACING_RE.subn(
            lambda match: rf"\\[{match.group(1)}pt]",
            line,
        )
        fixed_spacing_count += line_fixed_spacing_count
        normalized_lines.append(line)

    return "".join(normalized_lines), removed_count, fixed_spacing_count


def _read_multiline(prompt_msg: str) -> str:
    """Read multi-line input from stdin until the user types END on its own line."""
    console.print(
        Panel(
            f"{prompt_msg}\n\n"
            f"[dim]Paste your LaTeX code below, then type [bold]{_END_MARKER}[/bold] "
            f"on a new line and press Enter to finish.[/dim]",
            title="[bold cyan]LaTeX Input[/bold cyan]",
            border_style="cyan",
        )
    )

    lines: list[str] = []
    try:
        while True:
            line = input()
            if line.strip() == _END_MARKER:
                break
            lines.append(line)
    except EOFError:
        pass  # Ctrl-D also finishes input

    return "\n".join(lines)


def _compile_tex(tex_content: str, output_dir: Path) -> Path:
    """Write *tex_content* to a .tex file inside *output_dir* and compile it
    with tectonic.  Returns the path to the generated PDF.

    Tectonic is invoked with ``--keep-intermediates=false`` so that only the
    PDF is left behind (no .log / .aux / .out clutter).
    """
    tex_file = output_dir / "Fardows_Alam_Kayes.tex"
    tex_content, removed_directives, fixed_spacings = _normalize_tex_for_tectonic(
        tex_content
    )
    tex_file.write_text(tex_content, encoding="utf-8")
    if removed_directives:
        console.print(
            "[yellow]Note:[/yellow] Removed "
            f"{removed_directives} pdfLaTeX-only Unicode directive(s) "
            "that Tectonic does not support."
        )
    if fixed_spacings:
        console.print(
            "[yellow]Note:[/yellow] Added pt units to "
            f"{fixed_spacings} LaTeX line-break spacing value(s)."
        )

    tectonic = shutil.which("tectonic")
    if tectonic is None:
        console.print(
            "[red]Error:[/red] [bold]tectonic[/bold] is not installed or not on PATH.\n"
            "Install it from [link=https://tectonic-typesetting.github.io]"
            "tectonic-typesetting.github.io[/link] and try again."
        )
        raise typer.Exit(code=1)

    console.print("\n[cyan]⟳  Compiling LaTeX with tectonic …[/cyan]")
    result = subprocess.run(
        [tectonic, "--keep-intermediates", str(tex_file)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        console.print("[red]✘  Compilation failed.[/red]\n")
        if result.stderr:
            console.print(Panel(result.stderr.strip(), title="tectonic stderr", border_style="red"))
        if result.stdout:
            console.print(Panel(result.stdout.strip(), title="tectonic stdout", border_style="yellow"))
        raise typer.Exit(code=1)

    pdf_path = tex_file.with_suffix(".pdf")
    if not pdf_path.exists():
        console.print("[red]✘  Compilation reported success but no PDF was produced.[/red]")
        raise typer.Exit(code=1)

    # Clean up intermediate files tectonic may leave behind
    for ext in (".aux", ".log", ".out", ".toc", ".bbl", ".blg"):
        artefact = tex_file.with_suffix(ext)
        if artefact.exists():
            artefact.unlink()

    return pdf_path


def _open_pdf(pdf_path: Path) -> None:
    """Open *pdf_path* in the default system viewer (fire-and-forget)."""
    opener = "xdg-open" if sys.platform.startswith("linux") else "open"
    try:
        subprocess.Popen(
            [opener, str(pdf_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        console.print(
            f"[yellow]Could not auto-open the PDF.[/yellow] "
            f"Open it manually:\n  {pdf_path}"
        )


def conv() -> None:
    """Paste LaTeX code, compile to PDF, and open it."""

    console.print(
        Panel(
            "[bold]Paste-to-PDF Converter[/bold]\n"
            "Paste LaTeX from your favourite LLM, compile it locally, and view the result.",
            border_style="bright_magenta",
        )
    )

    # ── 1. Ask for folder name ────────────────────────────────────────
    folder_name = Prompt.ask(
        f"\n[bold]Folder name[/bold] (will be created under [cyan]{BASE_OUTPUT_DIR}[/cyan])"
    ).strip()

    if not folder_name:
        console.print("[red]Folder name cannot be empty.[/red]")
        raise typer.Exit(code=1)

    output_dir = BASE_OUTPUT_DIR / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✔  Output directory:[/green] {output_dir}\n")

    # ── 2. Capture pasted LaTeX ───────────────────────────────────────
    tex_content = _read_multiline("Paste your LaTeX code")

    if not tex_content.strip():
        console.print("[red]No LaTeX content received. Aborting.[/red]")
        raise typer.Exit(code=1)

    # ── 3. Compile ────────────────────────────────────────────────────
    pdf_path = _compile_tex(tex_content, output_dir)
    console.print(f"[green]✔  PDF generated:[/green] {pdf_path}")

    # ── 4. Open & exit ────────────────────────────────────────────────
    _open_pdf(pdf_path)
    console.print("[green]Done![/green] Exiting.")
    raise typer.Exit(code=0)
