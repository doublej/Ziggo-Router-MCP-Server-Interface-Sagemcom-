#!/bin/bash

# Sagemcom MCP Server Distribution Install Script
# This script installs the pre-built Sagemcom MCP server distribution

set -e

echo -e "\033[1;34mInstalling Sagemcom MCP Server (Distribution)...\033[0m"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "\033[1;31mError: uv is required but not installed\033[0m"
    echo "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo -e "\033[1;32muv found\033[0m"

# Get script directory and find the wheel file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEEL_FILE=$(find "$SCRIPT_DIR/" -name "*.whl" 2>/dev/null | head -1)

if [[ -z "$WHEEL_FILE" ]]; then
    echo -e "\033[1;31mError: No wheel file found in this directory\033[0m"
    echo "Expected file pattern: sagemcom_mcp-*.whl"
    exit 1
fi

echo -e "\033[1;36mFound wheel: $WHEEL_FILE\033[0m"

# Verify modem connectivity
echo -e "\033[1;33mVerifying modem connectivity...\033[0m"
if ! ping -c 1 -W 2000 192.168.178.1 &>/dev/null; then
    echo -e "\033[1;33mWarning: Cannot reach modem at 192.168.178.1\033[0m"
    echo "   Please ensure you're connected to the correct network"
    read -p "Continue anyway? [y/N]: " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 1
    fi
else
    echo -e "\033[1;32mRouter reachable at 192.168.178.1\033[0m"
fi

# Modem IP configuration
echo ""
echo "Modem IP Configuration:"
echo "Default modem IP is 192.168.178.1 (Ziggo standard)"
read -p "Use different IP? [y/N]: " CUSTOM_IP
if [[ "$CUSTOM_IP" =~ ^[Yy]$ ]]; then
    read -p "Enter modem IP address: " MODEM_IP
    echo -e "\033[1;32mWill use custom modem IP: $MODEM_IP\033[0m"
else
    MODEM_IP="192.168.178.1"
    echo -e "\033[1;32mUsing default modem IP: $MODEM_IP\033[0m"
fi

# Password configuration options
echo ""
echo "Password Configuration Options:"
echo "1) Enter password manually now"
echo "2) Use 1Password CLI (default: 'Ziggo SmartWifi Modem')"
echo "3) Set SAGEMCOM_MODEM_PASSWORD environment variable later"
echo "4) Skip password configuration"
echo ""
read -p "Choose option [1-4]: " PASSWORD_CHOICE

MODEM_PASSWORD=""
ONEPASSWORD_ITEM=""
DISABLE_ONEPASSWORD=""

case $PASSWORD_CHOICE in
    1)
        echo ""
        read -s -p "Enter modem password: " MODEM_PASSWORD
        echo ""
        echo -e "\033[1;32mPassword will be configured for Claude Desktop\033[0m"
        ;;
    2)
        echo ""
        read -p "Enter 1Password item name (blank = Ziggo SmartWifi Modem): " ONEPASSWORD_ITEM
        if [[ -z "$ONEPASSWORD_ITEM" ]]; then
            ONEPASSWORD_ITEM="Ziggo SmartWifi Modem"
        fi
        echo -e "\033[1;32m1Password will be used: $ONEPASSWORD_ITEM\033[0m"
        ;;
    3)
        echo -e "\033[1;32mWill use SAGEMCOM_MODEM_PASSWORD environment variable\033[0m"
        ;;
    4)
        echo -e "\033[1;36mPassword configuration skipped\033[0m"
        ;;
    *)
        echo -e "\033[1;36mInvalid choice, skipping password configuration\033[0m"
        ;;
esac

# Install using uv tool
echo -e "\033[1;36mInstalling Sagemcom MCP Server...\033[0m"
uv tool install "$WHEEL_FILE"

# Configure Claude Desktop MCP integration
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Verify Claude Desktop installation
if [[ ! -d "/Applications/Claude.app" ]]; then
    echo -e "\033[1;33mWarning: Claude Desktop not found at /Applications/Claude.app\033[0m"
    echo "   MCP integration may not work without Claude Desktop"
    read -p "Continue anyway? [y/N]: " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 1
    fi
else
    echo -e "\033[1;32mClaude Desktop found\033[0m"
fi

if [[ -f "$CLAUDE_CONFIG" ]]; then
    echo -e "\033[1;36mConfiguring Claude Desktop MCP integration...\033[0m"
    
    # Create backup
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.bak"
    
    # Configure MCP server (always overwrite existing configuration)
    python3 -c "
import json
import sys

try:
    with open('$CLAUDE_CONFIG', 'r') as f:
        config = json.load(f)
except:
    config = {}

if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Configure password environment based on choice
password_env = {}
modem_pwd = sys.argv[1] if len(sys.argv) > 1 else ''
onepass_item = sys.argv[2] if len(sys.argv) > 2 else ''
modem_ip = sys.argv[3] if len(sys.argv) > 3 else '192.168.178.1'

if modem_pwd:  # Manual password provided
    password_env['SAGEMCOM_MODEM_PASSWORD'] = modem_pwd
elif onepass_item:  # 1Password item provided
    password_env['SAGEMCOM_ONEPASSWORD_ITEM'] = onepass_item

# Add modem IP if different from default
if modem_ip != '192.168.178.1':
    password_env['SAGEMCOM_MODEM_IP'] = modem_ip

# Get the full path to the installed tool
import subprocess
import os
try:
    tool_path = subprocess.check_output(['which', 'sagemcom-mcp-server'], text=True).strip()
except:
    tool_path = os.path.expanduser('~/.local/bin/sagemcom-mcp-server')

# Always overwrite the sagemcom configuration
config['mcpServers']['sagemcom'] = {
    'command': tool_path,
    'args': [],
    'env': password_env
}

with open('$CLAUDE_CONFIG', 'w') as f:
    json.dump(config, f, indent=2)

print('\033[1;32mConfigured Sagemcom MCP server in Claude Desktop\033[0m')
" "$MODEM_PASSWORD" "$ONEPASSWORD_ITEM" "$MODEM_IP"
else
    echo -e "\033[1;33mClaude Desktop config not found at: $CLAUDE_CONFIG\033[0m"
    echo "   You may need to manually configure MCP integration"
fi

echo ""
echo -e "\033[1;32mInstallation complete!\033[0m"
echo ""
echo "Usage:"
echo "  - Claude Desktop: MCP server automatically configured"
echo "  - Command line: sagemcom-mcp-server"
echo ""
echo "Configuration:"
echo "  Set SAGEMCOM_MODEM_PASSWORD environment variable or use 1Password CLI"
echo "  Default modem IP: 192.168.178.1"
echo ""

# Ask user to restart Claude Desktop
if [[ -d "/Applications/Claude.app" ]]; then
    echo -e "\033[1;33mClaude Desktop needs to be restarted to load the new MCP server.\033[0m"
    read -p "Restart Claude Desktop now? [y/N]: " RESTART_CLAUDE
    
    if [[ "$RESTART_CLAUDE" =~ ^[Yy]$ ]]; then
        echo -e "\033[1;36mRestarting Claude Desktop...\033[0m"
        
        # Kill Claude if running
        pkill -f "Claude" 2>/dev/null || true
        
        # Wait a moment for clean shutdown
        sleep 10
        
        # Start Claude Desktop
        open "/Applications/Claude.app"
        
        echo -e "\033[1;32mClaude Desktop restarted. The Sagemcom MCP server should now be available.\033[0m"
    else
        echo -e "\033[1;36mPlease restart Claude Desktop manually to use the new MCP server.\033[0m"
    fi
else
    echo -e "\033[1;36mPlease restart Claude Desktop to use the new MCP server.\033[0m"
fi