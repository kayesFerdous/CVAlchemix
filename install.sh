#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10
CLI_NAME="cvalchemix"
PROJECT_GIT_URL="https://github.com/kayesFerdous/CVAlchemix.git"

if [[ -t 1 ]]; then
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  RED='\033[0;31m'
  CYAN='\033[0;36m'
  RESET='\033[0m'
else
  GREEN=''
  YELLOW=''
  RED=''
  CYAN=''
  RESET=''
fi

step() { printf '%b==>%b %s\n' "$CYAN" "$RESET" "$1"; }
ok() { printf '%b%s%b\n' "$GREEN" "$1" "$RESET"; }
warn() { printf '%b%s%b\n' "$YELLOW" "$1" "$RESET"; }
err() { printf '%b%s%b\n' "$RED" "$1" "$RESET" >&2; }

die() {
  err "$1"
  exit 1
}

detect_python() {
  local candidate
  for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

resolve_install_target() {
  if [[ -n "${CVALCHEMIX_INSTALL_TARGET:-}" ]]; then
    printf '%s' "$CVALCHEMIX_INSTALL_TARGET"
    return 0
  fi

  if [[ -f "$ROOT_DIR/pyproject.toml" ]]; then
    printf '%s' "$ROOT_DIR"
    return 0
  fi

  printf 'git+%s' "$PROJECT_GIT_URL"
}

INSTALL_TARGET="$(resolve_install_target)"

python_cmd="$(detect_python)" || die "Python 3.10+ is required, but no Python interpreter was found. Install Python from https://www.python.org/downloads/ and try again."

step "Checking Python..."
python_version="$($python_cmd -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])')"
python_major="$($python_cmd -c 'import sys; print(sys.version_info[0])')"
python_minor="$($python_cmd -c 'import sys; print(sys.version_info[1])')"

if (( python_major < MIN_PYTHON_MAJOR )) || { (( python_major == MIN_PYTHON_MAJOR )) && (( python_minor < MIN_PYTHON_MINOR )); }; then
  die "Python ${MIN_PYTHON_MAJOR}.${MIN_PYTHON_MINOR}+ is required. Found ${python_version}. Install a newer Python version and rerun this script."
fi

ok "Using Python ${python_version}"

ensure_user_bin_on_path() {
  local user_bin="${HOME}/.local/bin"
  local profile_file

  case ":${PATH}:" in
    *":${user_bin}:"*)
      return 0
      ;;
  esac

  for profile_file in "${HOME}/.profile" "${HOME}/.zprofile"; do
    if [[ -f "$profile_file" ]] && grep -Fqs 'export PATH="$HOME/.local/bin:$PATH"' "$profile_file"; then
      return 0
    fi
  done

  step "Adding user bin directory to PATH..."
  printf '\n# Added by CVAlchemix installer\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "${HOME}/.profile"

  if [[ ! -f "${HOME}/.zprofile" ]] || ! grep -Fqs 'export PATH="$HOME/.local/bin:$PATH"' "${HOME}/.zprofile"; then
    printf '\n# Added by CVAlchemix installer\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "${HOME}/.zprofile"
  fi

  warn "Added ~/.local/bin to your shell profile. Restart the terminal if cvalchemix is not found immediately."
}

install_with_pipx() {
  if command -v pipx >/dev/null 2>&1; then
    step "Installing via pipx..."
    pipx install --force "$INSTALL_TARGET"
    return 0
  fi
  return 1
}

install_with_pip_user() {
  step "Installing via pip..."
  "$python_cmd" -m pip install --user --upgrade pip
  "$python_cmd" -m pip install --user "$INSTALL_TARGET"
}

step "Installing dependencies..."
if ! "$python_cmd" -m pip --version >/dev/null 2>&1; then
  warn "pip is not available for this Python. Bootstrapping it with ensurepip..."
  "$python_cmd" -m ensurepip --upgrade >/dev/null
fi

if ! install_with_pipx; then
  warn "pipx is not installed. Falling back to pip --user installation."
  install_with_pip_user
  ensure_user_bin_on_path
fi

step "Setting up CLI..."
if command -v "$CLI_NAME" >/dev/null 2>&1; then
  ok "Installed successfully: $CLI_NAME"
  printf '\nRun %s --help to confirm everything is working.\n' "$CLI_NAME"
else
  ensure_user_bin_on_path
  warn "$CLI_NAME is not on PATH yet. Restart your terminal and try again."
  printf 'You can also run: export PATH="$HOME/.local/bin:$PATH"\n'
fi
