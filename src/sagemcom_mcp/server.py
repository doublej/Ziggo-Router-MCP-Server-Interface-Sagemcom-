"""
Sagemcom Router MCP Server
Provides tools for port forwarding management and session transfer to browser.
"""

# Add monitoring and reliability features: AI!
# - Add health check endpoint/tool for router connectivity
# - Add retry logic with exponential backoff for failed operations
# - Add request/response logging with timestamps
# - Add connection pooling for multiple router operations
# - Add rate limiting to prevent router overload

from mcp.server.fastmcp import FastMCP
import sys
import os
from pathlib import Path
import subprocess

from .client import (create_router_client, PortForwardingRule, expand_ip_shorthand, validate_port)

# Configure logging
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("SagemcomRouterMCP")

# Global router client instance
router_client = None


def get_router_client():
    """Get or create router client instance"""
    global router_client
    if router_client is None:
        router_client = create_router_client("rest")
    return router_client


@mcp.tool()
def open_port(name: str, local_address: str, local_port: int, external_port: int, protocol: str = "tcp") -> str:
    """
    Open a port on the router by creating a port forwarding rule.
    
    Args:
        name: Descriptive name for the port forwarding rule
        local_address: Local IP address (e.g., "192.168.178.100" or shorthand "100")
        local_port: Local port number
        external_port: External port number
        protocol: Protocol type ("tcp", "udp", or "tcp_udp")
    
    Returns:
        Success or error message
    """
    try:
        # Validate ports
        if not validate_port(local_port) or not validate_port(external_port):
            return "Error: Invalid port number(s). Ports must be between 1-65535."

        # Handle IP shorthand (e.g., "100" -> "192.168.178.100")
        local_address = expand_ip_shorthand(local_address)

        # Get router client and authenticate
        client = get_router_client()
        if not client.authenticate():
            return "Error: Failed to authenticate with router"

        # Create port forwarding rule
        rule = PortForwardingRule(
                name=name, local_address=local_address, local_port=local_port, external_port=external_port, protocol=protocol
        )

        if client.add_port_forward(rule):
            return f"Successfully opened port {external_port} -> {local_address}:{local_port} ({protocol})"
        else:
            return "Error: Failed to create port forwarding rule"

    except Exception as e:
        logger.error(f"Error in open_port: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def close_port(external_port: int) -> str:
    """
    Close a port on the router by removing the port forwarding rule.
    
    Args:
        external_port: External port number of the rule to remove
    
    Returns:
        Success or error message
    """
    try:
        # Validate port
        if not validate_port(external_port):
            return "Error: Invalid port number. Ports must be between 1-65535."

        # Get router client and authenticate
        client = get_router_client()
        if not client.authenticate():
            return "Error: Failed to authenticate with router"

        if client.remove_port_forward_by_port(external_port):
            return f"Successfully closed port forwarding rule for port {external_port}"
        else:
            return f"Error: Failed to remove port forwarding rule for port {external_port}"

    except Exception as e:
        logger.error(f"Error in close_port: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def list_port_forwards() -> str:
    """
    List all current port forwarding rules on the router.
    
    Returns:
        Formatted list of port forwarding rules
    """
    try:
        # Get router client and authenticate
        client = get_router_client()
        if not client.authenticate():
            return "Error: Failed to authenticate with router"

        rules = client.get_port_forwards()

        if not rules:
            return "No port forwarding rules found"

        result = "Current port forwarding rules:\n"
        for rule in rules:
            name = rule.get("name", "Unknown")
            local_addr = rule.get("localAddress", "Unknown")
            local_port = rule.get("localPort", "Unknown")
            external_port = rule.get("externalPort", "Unknown")
            protocol = rule.get("protocol", "Unknown").lower()
            enabled = rule.get("enabled", False)
            status = "enabled" if enabled else "disabled"

            result += f"- {name}: {external_port} -> {local_addr}:{local_port} ({protocol}) [{status}]\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Error in list_port_forwards: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def get_router_session_url() -> str:
    """
    Get the router's web interface URL for browser access.
    
    Returns:
        Router web interface URL
    """
    try:
        # Get router client 
        client = get_router_client()
        session_url = client.get_session_url()
        return f"Router web interface: {session_url}"

    except Exception as e:
        logger.error(f"Error in get_router_session_url: {e}")
        return f"Error: {str(e)}"


@mcp.tool()
def logout() -> str:
    """
    free up any existing API session to allow browser login.

    Returns:
        Success or error message
    """
    try:
        # Get router client and verify connection
        client = get_router_client()

        # Verify router is accessible, then logout to free session
        if client.authenticate():
            logger.info("Freeing session slot for browser login...")
            client.logout()
            return "Successfully logged out of router"
        else:
            return "Error: Failed to authenticate with router, probably logged out already. Please try again."

    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def open_router_in_browser() -> str:
    """
    Open the router's web interface in the default browser.
    Note: This will free up any existing API session to allow browser login.

    Returns:
        Success or error message
    """
    try:
        # Get router client and verify connection
        client = get_router_client()

        # Verify router is accessible, then logout to free session
        if client.authenticate():
            logger.info("Freeing session slot for browser login...")
            client.logout()

        session_url = client.get_session_url()

        # Open URL in default browser
        subprocess.run(["open", session_url], check=True)

        return f"Opened router web interface in browser: {session_url}\nPlease login with your router password. Note: Only one session is allowed at a time."

    except subprocess.CalledProcessError as e:
        return f"Error: Failed to open browser: {e}"
    except Exception as e:
        logger.error(f"Error in open_router_in_browser: {e}")
        return f"Error: {str(e)}"


@mcp.resource("router://status")
def get_router_status() -> str:
    """Get current router connection status"""
    try:
        client = get_router_client()
        # Try to authenticate to check status
        if hasattr(client, 'token') and client.token:
            return "Connected to router with valid authentication token"
        else:
            return "Not connected to router - authentication required"
    except Exception as e:
        return f"Error checking router status: {str(e)}"


@mcp.resource("router://config")
def get_router_config() -> str:
    """Get router configuration details"""
    client = get_router_client()
    return f"Router: {client.host}:{client.port}\nBase URL: {client.base_url}"


def main():
    """Main entry point for the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
