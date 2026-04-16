# CVAlchemix

Install and run the CLI with a single command.

## One-command install

### macOS and Linux

```bash
curl -fsSL https://raw.githubusercontent.com/kayesFerdous/CVAlchemix/main/install.sh | bash
```

If you do not have `curl`:

```bash
wget -qO- https://raw.githubusercontent.com/kayesFerdous/CVAlchemix/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
irm https://raw.githubusercontent.com/kayesFerdous/CVAlchemix/main/install.ps1 | iex
```

## Verify install

```bash
cvalchemix --help
```

## Local development install

From a local clone of this repository:

```bash
./install.sh
```

or on Windows:

```powershell
.\install.ps1
```

## Optional custom source

You can override the install source (local path, wheel, git URL) with:

```bash
CVALCHEMIX_INSTALL_TARGET='git+https://github.com/your-org/your-repo.git' ./install.sh
```
