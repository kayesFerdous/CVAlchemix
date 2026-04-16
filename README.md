# CVAlchemix

> Stop sending the same CV to every job. CVAlchemix scrapes LinkedIn postings and rewrites your CV with AI — tailored, compiled, and PDF-ready in seconds.

[![PyPI version](https://badge.fury.io/py/cvalchemix.svg)](https://pypi.org/project/cvalchemix/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## ✨ Features

- Scrapes LinkedIn job title, company, location, and full job description with Playwright.
- Reuses a persistent browser profile so you can keep a logged-in LinkedIn session.
- Prompts for a Gemini API key and a plain-text base CV, then stores them locally for later runs.
- Includes a built-in `cvalchemix login` command to open LinkedIn and persist an authenticated browser session.
- Rewrites the CV into a structured `CVData` schema using Google Gemini.
- Renders the final CV through a Jinja2 LaTeX template and compiles it to PDF with `tectonic`.
- Saves the intermediate `.tex` file alongside the PDF so you can inspect the generated LaTeX.
- Includes `show-config` and `delete` commands for inspection and cleanup.

## 🎯 Use Cases

- A job seeker can paste a LinkedIn posting and generate a tailored CV PDF that mirrors the role's keywords and structure.
- A candidate applying to several roles can reuse the same base CV and produce a separate PDF for each company and posting.
- A developer can automate a job-application workflow by combining the scraper, Gemini rewrite step, and PDF renderer in one CLI.
- Someone keeping a persistent LinkedIn session can avoid repeated logins when scraping job pages over time.
- A career coach or reviewer can inspect the generated `.tex` and final PDF to understand how the CV was reshaped for a role.

## ⚠️ Current Limitations

> These are known limitations in the current version. They will be addressed in future releases.

- **LinkedIn URL format:** Only the following URL pattern is currently supported:
  ```
  https://www.linkedin.com/jobs/collections/recommended/?currentJobId={currentJobId}
  ```
  Other LinkedIn URL shapes such as `/jobs/view/` and search-result pages are not yet supported.

- **AI Provider:** Currently only **Google Gemini** is supported as the AI provider.

- **External renderer:** PDF generation depends on a local `tectonic` binary being available on `PATH`.

- **Scraping fragility:** The scraper relies on LinkedIn CSS selectors, so LinkedIn DOM changes can break extraction.

- **Template scope:** Only one bundled LaTeX template, `classic.tex.j2`, is shipped right now.

- **No built-in fit score:** The repository contains structured analysis models, but there is no user-facing command that emits a standalone job-match score or analysis report yet.

## 🔩 Prerequisites

- Python >= 3.10
- A [Google Gemini API key](https://aistudio.google.com/)
- [`tectonic`](https://tectonic-typesetting.github.io/) installed and available on your `PATH`

> Playwright and its browsers are installed automatically as part of the Python dependencies — no manual step needed.

## 📦 Installation

### Option 1 — pip

```bash
pip install cvalchemix
```

### Option 2 — pipx (recommended for CLI tools)

```bash
pipx install cvalchemix
```

### Option 3 — One-command install (macOS/Linux)

```bash
curl -fsSL https://raw.githubusercontent.com/kayesFerdous/CVAlchemix/main/install.sh | bash
```

If you don't have `curl`:

```bash
wget -qO- https://raw.githubusercontent.com/kayesFerdous/CVAlchemix/main/install.sh | bash
```

### Option 4 — Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/kayesFerdous/CVAlchemix/main/install.ps1 | iex
```

> The installer scripts prefer `pipx` and fall back to `pip --user` when needed. You can override the install source with the `CVALCHEMIX_INSTALL_TARGET` environment variable.

## ✅ Verify Installation

```bash
cvalchemix --help
```

## 🚀 Quick Start

**1. Configure the app with your Gemini key and a plain-text base CV.**

```bash
cvalchemix configure
```

**2. Optional but recommended — open a persistent LinkedIn session once so the scraper can reuse it.**

```bash
cvalchemix login
```

**3. Generate a tailored CV from a LinkedIn job URL.**

```bash
cvalchemix generate "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=1234567890" -o ./output
```

The CLI writes the final PDF to `./output/cv/<company>_<timestamp>/cv.pdf` and saves the intermediate LaTeX source as `cv.tex` in the same directory.

## 📖 Usage

| Command | What it does | Example |
|---|---|---|
| `cvalchemix configure` | Prompts for a Gemini API key and the path to your base CV text file, then saves them in the local config file. | `cvalchemix configure` |
| `cvalchemix login` | Opens LinkedIn in a persistent Playwright browser profile and stores login readiness for later generate runs. | `cvalchemix login` |
| `cvalchemix show-config` | Displays the saved configuration and masks the stored API key. | `cvalchemix show-config` |
| `cvalchemix generate <job-url>` | Scrapes a LinkedIn job post, rewrites your CV with Gemini, and renders a PDF. Use `-o` or `--output` to set the destination directory. | `cvalchemix generate "https://www.linkedin.com/jobs/collections/recommended/?currentJobId=1234567890" -o ./output` |
| `cvalchemix delete` | Removes local CVAlchemix data and uninstalls the package by default. Use `--data-only` to keep the CLI installed, and `-y` to skip confirmation. | `cvalchemix delete -y` |

## ⚙️ Configuration

CVAlchemix uses two layers of configuration:

- **CLI config** — run `cvalchemix configure` to save your `gemini_api_key` and `base_cv_path` into a local JSON config file under your platform user config directory.
- **LinkedIn session** — run `cvalchemix login` once to open LinkedIn and save `linkedin_login_configured` for generate preflight checks.
- A `.env` file in the working directory is also read if present.

### Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | empty | Gemini API key used by the settings layer. |
| `DEFAULT_MODEL` | `gemini-2.5-flash-lite` | Gemini model name used by the LLM wrapper. |
| `PROFILE_DIR` | managed app profile directory | Playwright browser profile location for persistent LinkedIn sessions. |
| `OUTPUT_DIR` | `./output` | Default output directory used by the settings layer. |
| `BROWSER_HEADLESS` | `false` | Launch Playwright in headless mode when set to `true`. |
| `SCRAPE_TIMEOUT_MS` | `30000` | Timeout in ms while waiting for LinkedIn page content to load. |
| `MAX_RETRIES` | `3` | Number of retries defined by the configuration layer. |
| `LOG_LEVEL` | `INFO` | Root logging level. |

A `.env.example` file with starter values for all of the above is included in the repository.

## 🗺️ Roadmap

- [ ] OpenAI / Anthropic provider support
- [ ] Additional CV templates
- [ ] Job-fit score command
- [ ] Broader LinkedIn URL support

## 🛠️ Local Development

```bash
git clone https://github.com/kayesFerdous/CVAlchemix.git
cd CVAlchemix
./install.sh        # macOS/Linux
.\install.ps1       # Windows PowerShell
```

For a development install with editable mode:

```bash
pip install -e ".[dev]"
```

## 🤝 Contributing

1. Fork the repository and create a focused branch for your change.
2. Make the smallest practical change and keep the existing CLI behaviour intact unless the change explicitly requires otherwise.
3. Verify the project still starts, configure the CLI, and run a sample `generate` flow if your change touches the pipeline.
4. Open a pull request with a clear description of the change, the motivation, and any manual verification you performed.

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.