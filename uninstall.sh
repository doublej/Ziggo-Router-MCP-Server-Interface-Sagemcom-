#!/bin/bash

# Sagemcom MCP Server and CLI Uninstall Script
# Removes the MCP server, CLI, and Claude Desktop configuration

set -e

echo -e "\033[1;34mUninstalling Sagemcom MCP Server and CLI...\033[0m"

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo -e "\033[1;33mWarning: uv not found - skipping tool uninstall.\033[0m"
else
    echo -e "\033[1;36mChecking for installed Sagemcom tools...\033[0m"
    # Remove sagemcom-mcp-server
    if uv tool list | grep -q "sagemcom-mcp-server"; then
        echo -e "\033[1;36mRemoving sagemcom-mcp-server tool...\033[0m"
        uv tool uninstall sagemcom-mcp-server
        echo -e "\033[1;32msagemcom-mcp-server tool removed.\033[0m"
    else
        echo -e "\033[1;36msagemcom-mcp-server tool not found (already removed or not installed).\033[0m"
    fi

    # Remove sagemcom-cli
    if uv tool list | grep -q "sagemcom-cli"; then
        echo -e "\033[1;36mRemoving sagemcom-cli tool...\033[0m"
        uv tool uninstall sagemcom-cli
        echo -e "\033[1;32msagemcom-cli tool removed.\033[0m"
    else
        echo -e "\033[1;36msagemcom-cli tool not found (already removed or not installed).\033[0m"
    fi
fi

# Remove Claude Desktop MCP configuration
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [[ -f "$CLAUDE_CONFIG" ]]; then
    echo -e "\033[1;36mRemoving Claude Desktop MCP configuration...\033[0m"
    
    # Create backup
    cp "$CLAUDE_CONFIG" "$CLAUDE_CONFIG.uninstall.bak"
    
    # Check if sagemcom configuration exists
    if grep -q "sagemcom" "$CLAUDE_CONFIG"; then
        # Remove MCP server configuration
        python3 -c "
import json
import sys

try:
    with open('$CLAUDE_CONFIG', 'r') as f:
        config = json.load(f)
    
    if 'mcpServers' in config and 'sagemcom' in config['mcpServers']:
        del config['mcpServers']['sagemcom']
        print('\033[1;32mRemoved Sagemcom MCP server from Claude Desktop configuration.\033[0m')
        
        # Clean up empty mcpServers section
        if not config['mcpServers']:
            del config['mcpServers']
            print('\033[1;32mCleaned up empty mcpServers section in Claude Desktop configuration.\033[0m')
    else:
        print('\033[1;36mSagemcom MCP server not found in Claude Desktop configuration.\033[0m')
    
    with open('$CLAUDE_CONFIG', 'w') as f:
        json.dump(config, f, indent=2)

except Exception as e:
    print(f'\033[1;31mError updating Claude Desktop configuration: {e}\033[0m')
    sys.exit(1)
"
    else
        echo -e "\033[1;36mSagemcom MCP server not found in Claude Desktop configuration.\033[0m"
    fi
else
    echo -e "\033[1;33mWarning: Claude Desktop config not found at: $CLAUDE_CONFIG\033[0m"
fi

echo ""
echo -e "\033[1;32mUninstall complete!\033[0m"
echo ""
echo -e "\033[1;34mNotes:\033[0m"
echo -e "  - Restart Claude Desktop to apply changes."
echo -e "  - Configuration backups were created with the .uninstall.bak extension if Claude config was modified."
echo -e "  - To reinstall the MCP server, run the install-mcp.sh script from the distribution."
echo -e "  - To reinstall the CLI, run the install-cli.sh script from the distribution."
