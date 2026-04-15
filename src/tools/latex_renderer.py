from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from tools.base import BaseTool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LaTeX escaping
# ---------------------------------------------------------------------------
# Order matters: braces and backslash are handled carefully to avoid
# self-corruption.  We escape `\` LAST (as \textbackslash) *after* every
# other replacement has already been applied, so the braces and backslash
# we inject are never re-processed.
# ---------------------------------------------------------------------------

_LATEX_SPECIAL: dict[str, str] = {
    "&":  r"\&",
    "%":  r"\%",
    "$":  r"\$",
    "#":  r"\#",
    "_":  r"\_",
    "{":  r"\{",
    "}":  r"\}",
    "~":  r"\textasciitilde{}",
    "^":  r"\textasciicircum{}",
}


def _latex_escape(text: str) -> str:
    """Escape LaTeX special characters in *display* text.

    Do NOT use this for URLs — use ``_url_escape`` instead.
    """
    if not isinstance(text, str) or not text:
        return ""

    # 1. Protect existing backslashes first by replacing them with a
    #    placeholder that cannot collide with any other replacement.
    _PLACEHOLDER = "\x00BACKSLASH\x00"
    text = text.replace("\\", _PLACEHOLDER)

    # 2. Replace every other special character.
    for char, escaped in _LATEX_SPECIAL.items():
        text = text.replace(char, escaped)

    # 3. Swap the placeholder for the final \textbackslash{}.
    text = text.replace(_PLACEHOLDER, r"\textbackslash{}")

    return text


def _url_escape(url: str) -> str:
    """Minimal escaping for URLs inside ``\\href{…}``.

    ``hyperref`` handles most URL characters natively.  Only ``%`` and
    ``#`` genuinely need escaping (``#`` starts a LaTeX comment on some
    drivers, ``%`` always does).  We also escape ``\\`` just in case.
    """
    if not isinstance(url, str) or not url:
        return ""
    url = url.replace("\\", r"\%5C")
    url = url.replace("%", r"\%")
    url = url.replace("#", r"\#")
    return url


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

_REQUIRED_TOP_LEVEL_KEYS = {"contact", "education", "experience", "skill_groups"}


class LatexRenderer(BaseTool):
    name: str = "latex_renderer"
    description: str = "Renders CV data into a PDF via a Jinja2 LaTeX template."

    def __init__(self, template_dir: str = "/home/kayes/new_world/python/browse/templates") -> None:
        self._template_dir = template_dir
        self._env = self._create_environment(template_dir)

    # ------------------------------------------------------------------ #
    #  Jinja2 environment                                                #
    # ------------------------------------------------------------------ #
    def _create_environment(self, template_dir: str) -> Environment:
        """Create a Jinja2 environment configured for LaTeX rendering."""
        env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False,
            block_start_string=r"\BLOCK{",
            block_end_string="}",
            variable_start_string=r"\VAR{",
            variable_end_string="}",
            comment_start_string=r"\#{",
            comment_end_string="}",
            trim_blocks=True,
            lstrip_blocks=True,
        )
        env.filters["latex_escape"] = _latex_escape
        env.filters["url_escape"] = _url_escape
        return env

    # ------------------------------------------------------------------ #
    #  Validation                                                        #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _validate_data(data: dict[str, Any]) -> None:
        """Check that the data dict has the minimum keys the template needs."""
        missing = _REQUIRED_TOP_LEVEL_KEYS - set(data.keys())
        if missing:
            raise ValueError(
                f"CV data is missing required keys: {', '.join(sorted(missing))}"
            )

        contact = data.get("contact", {})
        if not contact.get("full_name"):
            raise ValueError("contact.full_name is required")

    # ------------------------------------------------------------------ #
    #  Template rendering                                                #
    # ------------------------------------------------------------------ #
    def render_template(
        self,
        data: dict[str, Any],
        template_name: str = "classic.tex.j2",
    ) -> str:
        self._validate_data(data)

        try:
            template = self._env.get_template(template_name)
        except Exception as e:
            raise RuntimeError(f"Template '{template_name}' not found: {e}") from e

        try:
            rendered = template.render(data=data)
        except Exception as e:
            raise RuntimeError(f"Template rendering failed: {e}") from e

        logger.info("Template rendered successfully (%d characters).", len(rendered))
        return rendered

    # ------------------------------------------------------------------ #
    #  Compilation                                                       #
    # ------------------------------------------------------------------ #
    def compile_to_pdf(self, tex_content: str, output_path: str) -> str:
        output_path_obj = Path(output_path).resolve()
        debug_tex = output_path_obj.with_suffix(".tex")

        # Always save the intermediate .tex for inspection.
        debug_tex.parent.mkdir(parents=True, exist_ok=True)
        debug_tex.write_text(tex_content, encoding="utf-8")
        logger.info("Intermediate .tex saved to %s", debug_tex)

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_file = os.path.join(tmpdir, "cv.tex")

            with open(tex_file, "w", encoding="utf-8") as f:
                f.write(tex_content)

            logger.info("Running tectonic …")
            result = subprocess.run(
                ["tectonic", tex_file],
                cwd=tmpdir,
                capture_output=True,
                text=True,
            )

            if result.stdout:
                logger.debug("tectonic stdout:\n%s", result.stdout)
            if result.stderr:
                logger.debug("tectonic stderr:\n%s", result.stderr)

            if result.returncode != 0:
                raise RuntimeError(
                    f"Tectonic compilation failed (see {debug_tex}):\n"
                    f"{result.stderr}"
                )

            pdf_file = Path(tex_file).with_suffix(".pdf")
            if not pdf_file.exists():
                raise RuntimeError(
                    "Tectonic reported success but no PDF was produced."
                )

            output_path_obj.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(str(pdf_file), str(output_path_obj))
            logger.info("PDF written to %s", output_path_obj)
            return str(output_path_obj)

    # ------------------------------------------------------------------ #
    #  Public entry point                                                 #
    # ------------------------------------------------------------------ #
    def run(  # type: ignore[override]
        self,
        data: dict[str, Any],
        template_name: str = "classic.tex.j2",
        output_path: str = "output.pdf",
    ) -> str:
        tex = self.render_template(data, template_name)
        return self.compile_to_pdf(tex, output_path)
