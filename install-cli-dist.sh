#!/bin/bash

# Sagemcom CLI Distribution Install Script
# This script installs the pre-built Sagemcom CLI from the distribution

set -e

echo -e "\033[1;34mInstalling Sagemcom CLI (Distribution)...\033[0m"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "\033[1;31mError: uv is required but not installed\033[0m"
    echo "Install uv: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo -e "\033[1;32muv found\033[0m"

# Get script directory and find the wheel file
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Assumes CLI tools are packaged in the sagemcom_mcp_server wheel
WHEEL_FILE=$(find "$SCRIPT_DIR/" -name "sagemcom_mcp-*.whl" 2>/dev/null | head -1)

if [[ -z "$WHEEL_FILE" ]]; then
    echo -e "\033[1;31mError: No wheel file found in this directory\033[0m"
    echo "Expected file pattern: sagemcom_mcp-*.whl (which includes CLI tools)"
    exit 1
fi

echo -e "\033[1;36mFound wheel: $WHEEL_FILE\033[0m"

# Verify modem connectivity (general check against default IP)
echo -e "\033[1;33mVerifying modem connectivity (checking default 192.168.178.1)...\033[0m"
DEFAULT_PING_IP="192.168.178.1"
if ! ping -c 1 -W 2000 "$DEFAULT_PING_IP" &>/dev/null; then
    echo -e "\033[1;33mWarning: Cannot reach default modem IP at $DEFAULT_PING_IP\033[0m"
    echo "   Please ensure you're connected to the correct network for your modem."
    read -p "Continue anyway? [y/N]: " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "Installation cancelled"
        exit 1
    fi
else
    echo -e "\033[1;32mRouter reachable at $DEFAULT_PING_IP (default IP). You can specify a different IP next.\033[0m"
fi

# Modem IP configuration
echo ""
echo "Modem IP Configuration for CLI:"
echo "The Sagemcom CLI needs to know your modem's IP address."
echo "Default modem IP is 192.168.178.1 (Ziggo standard)."
read -p "Use different IP for CLI? [y/N]: " CUSTOM_IP
if [[ "$CUSTOM_IP" =~ ^[Yy]$ ]]; then
    read -p "Enter modem IP address: " MODEM_IP
    echo -e "\033[1;32mCLI will be guided to use custom modem IP: $MODEM_IP\033[0m"
else
    MODEM_IP="192.168.178.1"
    echo -e "\033[1;32mCLI will be guided to use default modem IP: $MODEM_IP\033[0m"
fi

# Password configuration options
echo ""
echo "Password Configuration Options for CLI:"
echo "The CLI needs router password access. Choose how it should obtain it:"
echo "1) Guide me to set SAGEMCOM_MODEM_PASSWORD manually with the password."
echo "2) Guide me to use 1Password CLI (set SAGEMCOM_ONEPASSWORD_ITEM)."
echo "3) Skip (I'll handle environment variables later)."
echo ""
read -p "Choose option [1-3]: " PASSWORD_CHOICE_CLI

ONEPASSWORD_ITEM_CLI="" # Store 1Password item name if chosen

case $PASSWORD_CHOICE_CLI in
    1)
        echo ""
        echo -e "\033[1;32mSelected: Guide to set SAGEMCOM_MODEM_PASSWORD manually.\033[0m"
        ;;
    2)
        echo ""
        read -p "Enter 1Password item name (blank = Ziggo SmartWifi Modem): " TEMP_ONEPASSWORD_ITEM
        if [[ -z "$TEMP_ONEPASSWORD_ITEM" ]]; then
            ONEPASSWORD_ITEM_CLI="Ziggo SmartWifi Modem"
        else
            ONEPASSWORD_ITEM_CLI="$TEMP_ONEPASSWORD_ITEM"
        fi
        echo -e "\033[1;32mSelected: Guide to use 1Password CLI with item '$ONEPASSWORD_ITEM_CLI'.\033[0m"
        ;;
    3|*)
        echo -e "\033[1;36mPassword configuration guidance skipped or invalid choice.\033[0m"
        ;;
esac

# Install using uv tool
echo -e "\033[1;36mInstalling Sagemcom CLI tools from $WHEEL_FILE...\033[0m"
# Using --force in case tools from this wheel (e.g. mcp server) were already installed
# by another script, to ensure CLI tools are properly linked.
uv tool install "$WHEEL_FILE" --force

echo ""
echo -e "\033[1;32mSagemcom CLI Installation complete!\033[0m"
echo ""
echo "The 'sagemcom-cli' command should now be available in your path."
echo "If you get 'command not found', you may need to add ~/.local/bin to your PATH"
echo "(e.g., by running 'export PATH=\"\$HOME/.local/bin:\$PATH\"')"
echo "and then restart your terminal or source your shell profile (e.g., 'source ~/.zshrc')."
echo ""
echo "Configuration Reminder:"
echo "-----------------------"
echo "For sagemcom-cli to function, you need to configure environment variables in your shell."
echo ""
echo "1. Modem IP Address:"
echo "   Run this in your terminal (or add to shell profile):"
echo "   export SAGEMCOM_MODEM_IP=\"$MODEM_IP\""
echo ""
echo "2. Router Password:"
case $PASSWORD_CHOICE_CLI in
    1)
        echo "   You opted to set the password via SAGEMCOM_MODEM_PASSWORD."
        echo "   Run this in your terminal (or add to shell profile):"
        echo "   export SAGEMCOM_MODEM_PASSWORD=\"your_router_password\""
        echo "   (Replace 'your_router_password' with your actual password)"
        ;;
    2)
        echo "   You opted to use 1Password CLI."
        echo "   Run this in your terminal (or add to shell profile):"
        echo "   export SAGEMCOM_ONEPASSWORD_ITEM=\"$ONEPASSWORD_ITEM_CLI\""
        echo "   (Ensure 'op' CLI is installed and you are logged in to 1Password)"
        ;;
    3|*)
        echo "   Password configuration method was not specified during install."
        echo "   You need to set one of these environment variables:"
        echo "   - export SAGEMCOM_MODEM_PASSWORD=\"your_router_password\""
        echo "   - export SAGEMCOM_ONEPASSWORD_ITEM=\"Your 1Password Item Name\""
        ;;
esac
echo ""
echo "To make these settings permanent, add the 'export' commands to your shell's"
echo "profile file (e.g., ~/.zshrc, ~/.bash_profile, or ~/.config/fish/config.fish)"
echo "and then source it or open a new terminal."
echo ""
echo ""
echo ""
echo ""
echo "Example CLI Usage:"
echo "------------------"
echo "sagemcom-cli list"
echo "sagemcom-cli open --name MyRule --local-address 100 --local-port 80 --external-port 8080"
echo "sagemcom-cli close --port 8080"
echo "sagemcom-cli browser"
echo ""

# Post-installation check
echo -e "\033[1;33mVerifying 'sagemcom-cli' installation...\033[0m"
if ! command -v sagemcom-cli &> /dev/null; then
    echo -e "\033[1;31mError: 'sagemcom-cli' command not found after installation.\033[0m"
    echo "This commonly happens if the installation directory is not in your PATH."
    echo "The 'sagemcom-mcp-server' executable (installed from the same package) might provide a hint."
    
    INSTALLED_SERVER_PATH=$(which sagemcom-mcp-server 2>/dev/null)
    if [[ -n "$INSTALLED_SERVER_PATH" ]]; then
        TOOL_BIN_DIR=$(dirname "$INSTALLED_SERVER_PATH")
        echo "The 'sagemcom-mcp-server' was found here: $INSTALLED_SERVER_PATH"
        echo "The 'sagemcom-cli' executable should be in the same directory: $TOOL_BIN_DIR"
        if [[ -f "$TOOL_BIN_DIR/sagemcom-cli" ]]; then
            echo -e "\033[1;32m'sagemcom-cli' executable IS present at '$TOOL_BIN_DIR/sagemcom-cli'.\033[0m"
            echo "Please ensure '$TOOL_BIN_DIR' is in your PATH environment variable."
            echo "You can check your current PATH with: echo \$PATH"
            echo "Add it to your shell profile (e.g., ~/.zshrc or ~/.bash_profile) like:"
            echo "  export PATH=\"$TOOL_BIN_DIR:\$PATH\""
            echo "Then, restart your terminal or source your profile (e.g., 'source ~/.zshrc')."
        else
            echo -e "\033[1;31m'sagemcom-cli' executable was NOT found at '$TOOL_BIN_DIR/sagemcom-cli'.\033[0m"
            echo "This suggests an issue with the installation process itself for 'sagemcom-cli'."
        fi
    else
        echo -e "\033[1;31mCould not locate 'sagemcom-mcp-server' using 'which'.\033[0m"
        echo "This indicates a more general installation problem or PATH issue."
        echo "Tools are typically installed by 'uv' into a directory like '~/.local/bin'."
        echo "Please ensure this directory is in your PATH and try again."
        echo "You can check your current PATH with: echo \$PATH"
    fi
    echo "Your current PATH is: $PATH"
else
    INSTALLED_CLI_PATH=$(which sagemcom-cli)
    echo -e "\033[1;32mSuccessfully verified 'sagemcom-cli'. It is available at: $INSTALLED_CLI_PATH\033[0m"
fi
