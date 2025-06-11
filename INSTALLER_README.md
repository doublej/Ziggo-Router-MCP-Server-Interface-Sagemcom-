# Installation Guide

After extracting the archive, you have several installation options:

## Option 1: GUI Installation (macOS only)
**Double-click "Install Sagemcom MCP.app"**
- A dialog will appear asking you to choose installation type
- Select either "Full Installation" or "CLI Only"
- Terminal will open and run the installer
- Follow the prompts in Terminal to complete installation

## Option 2: Direct Installation (All platforms)
```bash
# For full installation (MCP Server + CLI + Claude Desktop)
./install-dist.sh

# For CLI tools only
./install-cli-dist.sh
```

## Uninstallation
```bash
./uninstall.sh
```

## Troubleshooting
- If scripts aren't executable, run: `chmod +x *.sh`
- If the GUI app doesn't work, use one of the terminal options
- Make sure UV is installed: `curl -LsSf https://astral.sh/uv/install.sh | sh`