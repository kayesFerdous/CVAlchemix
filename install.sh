#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIN_PYTHON_MAJOR=3
MIN_PYTHON_MINOR=10
CLI_NAME="cvalchemix"
LEGACY_PACKAGE_NAME="browse"
PROJECT_GIT_URL="https://github.com/kayesFerdous/CVAlchemix.git"
ACTION="${1:-install}"

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

usage() {
  cat <<'EOF'
Usage:
  ./install.sh            Install CVAlchemix
  ./install.sh install    Install CVAlchemix
  ./install.sh uninstall  Uninstall CVAlchemix and remove local app data
  ./install.sh --uninstall
EOF
}

normalize_action() {
  case "$ACTION" in
    install|"")
      ACTION="install"
      ;;
    uninstall|--uninstall)
      ACTION="uninstall"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown action: $ACTION"
      ;;
  esac
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

remove_profile_export_block() {
  local profile_file="$1"
  local tmp_file

  [[ -f "$profile_file" ]] || return 0

  tmp_file="${profile_file}.tmp.cvalchemix"
  awk '
    BEGIN { skip_next = 0 }
    $0 == "# Added by CVAlchemix installer" {
      skip_next = 1
      next
    }
    skip_next == 1 && $0 == "export PATH=\"$HOME/.local/bin:$PATH\"" {
      skip_next = 0
      next
    }
    {
      skip_next = 0
      print
    }
  ' "$profile_file" > "$tmp_file"

  mv "$tmp_file" "$profile_file"
}

remove_installer_path_blocks() {
  remove_profile_export_block "${HOME}/.profile"
  remove_profile_export_block "${HOME}/.zprofile"
}

remove_app_data_dirs() {
  "$python_cmd" - <<'PY'
import shutil
from pathlib import Path

dirs = {
    Path.home() / ".config" / "cvalchemix",
    Path.home() / ".config" / "CVAlchemix",
    Path.home() / ".cache" / "cvalchemix",
    Path.home() / ".local" / "share" / "cvalchemix",
}

try:
    from platformdirs import (
        user_cache_dir,
        user_config_dir,
        user_data_dir,
        user_log_dir,
        user_state_dir,
    )
except Exception:
    pass
else:
    for resolver in (
        user_config_dir,
        user_data_dir,
        user_cache_dir,
        user_state_dir,
        user_log_dir,
    ):
        try:
            dirs.add(Path(resolver("cvalchemix")))
        except Exception:
            pass

for path in sorted(dirs):
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
        print(path)
PY
}

uninstall_with_pipx() {
  if command -v pipx >/dev/null 2>&1; then
    pipx uninstall "$CLI_NAME" >/dev/null 2>&1 || true
    pipx uninstall "$LEGACY_PACKAGE_NAME" >/dev/null 2>&1 || true
  fi
}

uninstall_with_pip_user() {
  if "$python_cmd" -m pip --version >/dev/null 2>&1; then
    "$python_cmd" -m pip uninstall --yes "$CLI_NAME" "$LEGACY_PACKAGE_NAME" >/dev/null 2>&1 || true
  fi
}

remove_local_launchers() {
  rm -f \
    "${HOME}/.local/bin/${CLI_NAME}" \
    "${HOME}/.local/bin/cvx" \
    "${HOME}/.local/bin/${LEGACY_PACKAGE_NAME}"
}

remove_stale_pipx_dirs() {
  rm -rf \
    "${HOME}/.local/share/pipx/venvs/${CLI_NAME}" \
    "${HOME}/.local/share/pipx/venvs/${LEGACY_PACKAGE_NAME}"
}

run_uninstall() {
  step "Removing CLI installation..."
  uninstall_with_pipx
  uninstall_with_pip_user
  remove_local_launchers
  remove_stale_pipx_dirs

  step "Removing app data and config..."
  remove_app_data_dirs >/dev/null 2>&1 || true
  remove_installer_path_blocks

  ok "Uninstall complete. cvalchemix files were removed from this machine."
}

normalize_action

python_cmd="$(detect_python)" || die "Python 3.10+ is required, but no Python interpreter was found. Install Python from https://www.python.org/downloads/ and try again."

if [[ "$ACTION" == "uninstall" ]]; then
  run_uninstall
  exit 0
fi

INSTALL_TARGET="$(resolve_install_target)"

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
