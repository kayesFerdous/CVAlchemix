param(
  [switch]$Uninstall
)

$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageName = 'cvalchemix'
$LegacyPackageName = 'browse'
$MinPythonMajor = 3
$MinPythonMinor = 10
$ProjectGitUrl = 'https://github.com/kayesFerdous/CVAlchemix.git'
$InstallTarget = $null
$PythonExe = $null
$PythonArgs = @()

function Write-Step {
  param([string]$Message)
  Write-Host "> $Message" -ForegroundColor Cyan
}

function Write-Ok {
  param([string]$Message)
  Write-Host $Message -ForegroundColor Green
}

function Write-Warn {
  param([string]$Message)
  Write-Host $Message -ForegroundColor Yellow
}

function Write-ErrorLine {
  param([string]$Message)
  Write-Host $Message -ForegroundColor Red
}

function Get-PythonCommand {
  if (Get-Command python -ErrorAction SilentlyContinue) {
    $script:PythonExe = 'python'
    $script:PythonArgs = @()
    return $true
  }

  if (Get-Command py -ErrorAction SilentlyContinue) {
    $script:PythonExe = 'py'
    $script:PythonArgs = @('-3')
    return $true
  }

  return $false
}

$PythonCommand = Get-PythonCommand
if (-not $PythonCommand) {
  Write-ErrorLine "Python 3.10+ is required, but no Python installation was found. Install Python from https://www.python.org/downloads/ and rerun this script."
  exit 1
}

function Invoke-Python {
  param([string[]]$Args)
  & $PythonExe @PythonArgs @Args
}

function Remove-AppDataDirs {
  $pythonScript = @'
from pathlib import Path
import shutil

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
'@

  try {
    Invoke-Python -Args @('-c', $pythonScript) | Out-Null
  } catch {
    # Ignore data cleanup failures to keep uninstall resilient.
  }
}

function Remove-LocalLaunchers {
  try {
    $UserBase = (Invoke-Python -Args @('-c', 'import site; print(site.getuserbase())')).Trim()
    $UserScripts = Join-Path $UserBase 'Scripts'

    $Launchers = @(
      'cvalchemix.exe',
      'cvalchemix-script.py',
      'cvx.exe',
      'cvx-script.py',
      'browse.exe',
      'browse-script.py'
    )

    foreach ($Launcher in $Launchers) {
      Remove-Item (Join-Path $UserScripts $Launcher) -Force -ErrorAction SilentlyContinue
    }
  } catch {
    # No-op when user scripts directory cannot be resolved.
  }
}

function Remove-StalePipxVenvs {
  $pipxRoots = @(
    (Join-Path $HOME '.local/share/pipx/venvs'),
    (Join-Path $HOME '.local/pipx/venvs')
  )

  foreach ($root in $pipxRoots) {
    Remove-Item (Join-Path $root $PackageName) -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $root $LegacyPackageName) -Recurse -Force -ErrorAction SilentlyContinue
  }
}

function Run-Uninstall {
  Write-Step 'Removing CLI installation...'

  if (Get-Command pipx -ErrorAction SilentlyContinue) {
    try { & pipx uninstall $PackageName | Out-Null } catch {}
    try { & pipx uninstall $LegacyPackageName | Out-Null } catch {}
  }

  try {
    Invoke-Python -Args @('-m', 'pip', 'uninstall', '--yes', $PackageName, $LegacyPackageName) | Out-Null
  } catch {
    # Ignore pip uninstall failures when package isn't installed in this interpreter.
  }

  Remove-LocalLaunchers
  Remove-StalePipxVenvs

  Write-Step 'Removing app data and config...'
  Remove-AppDataDirs

  Write-Ok 'Uninstall complete. cvalchemix files were removed from this machine.'
}

function Resolve-InstallTarget {
  if ($env:CVALCHEMIX_INSTALL_TARGET) {
    return $env:CVALCHEMIX_INSTALL_TARGET
  }

  if (Test-Path (Join-Path $RootDir 'pyproject.toml')) {
    return $RootDir
  }

  return "git+$ProjectGitUrl"
}

$InstallTarget = Resolve-InstallTarget

if ($Uninstall) {
  Run-Uninstall
  exit 0
}

Write-Step 'Checking Python...'
$PythonVersion = (Invoke-Python -Args @('-c', "import sys; print('{}.{}.{}'.format(*sys.version_info[:3]))")).Trim()
$VersionParts = $PythonVersion.Split('.')
$PythonMajor = [int]$VersionParts[0]
$PythonMinor = [int]$VersionParts[1]

if ($PythonMajor -lt $MinPythonMajor -or ($PythonMajor -eq $MinPythonMajor -and $PythonMinor -lt $MinPythonMinor)) {
  Write-ErrorLine "Python $MinPythonMajor.$MinPythonMinor+ is required. Found $PythonVersion. Install a newer Python version and rerun this script."
  exit 1
}

Write-Ok "Using Python $PythonVersion"

function Ensure-UserScriptsOnPath {
  $UserBase = (Invoke-Python -Args @('-c', 'import site; print(site.getuserbase())')).Trim()
  $UserScripts = Join-Path $UserBase 'Scripts'

  if ($env:Path -split ';' | Where-Object { $_ -and ($_ -ieq $UserScripts) }) {
    return
  }

  Write-Step 'Adding user Scripts directory to PATH...'
  $NewPath = "$env:Path;$UserScripts"
  [Environment]::SetEnvironmentVariable('Path', $NewPath, 'User')
  $env:Path = $NewPath
  Write-Warn "Added $UserScripts to your user PATH. Open a new terminal if cvalchemix is not found immediately."
}

Write-Step 'Installing dependencies...'
try {
  Invoke-Python -Args @('-m', 'pip', '--version') | Out-Null
} catch {
  Invoke-Python -Args @('-m', 'ensurepip', '--upgrade') | Out-Null
}

$PipxAvailable = [bool](Get-Command pipx -ErrorAction SilentlyContinue)

if ($PipxAvailable) {
  Write-Step 'Installing via pipx...'
  & pipx install --force $InstallTarget
  if (-not (Get-Command $PackageName -ErrorAction SilentlyContinue)) {
    Ensure-UserScriptsOnPath
  }
} else {
  Write-Warn 'pipx is not installed. Falling back to pip --user installation.'
  Write-Step 'Installing via pip...'
  Invoke-Python -Args @('-m', 'pip', 'install', '--user', '--upgrade', 'pip') | Out-Null
  Invoke-Python -Args @('-m', 'pip', 'install', '--user', $InstallTarget)
  Ensure-UserScriptsOnPath
}

Write-Step 'Setting up CLI...'
if (Get-Command $PackageName -ErrorAction SilentlyContinue) {
  Write-Ok "Installed successfully: $PackageName"
  Write-Host "Run $PackageName --help to confirm everything is working."
} else {
  Ensure-UserScriptsOnPath
  Write-Warn "$PackageName is not on PATH yet. Restart your terminal and try again."
}
