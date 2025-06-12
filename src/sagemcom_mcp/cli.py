#!/usr/bin/env python3
"""
CLI Wrapper for Sagemcom Router Management
Provides command-line interface using shared router client
"""
import argparse
import configparser
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

from .client import (
    PortForwardingRule,
    create_router_client,
    expand_ip_shorthand,
    validate_port,
)


class Spinner:
    """A simple spinner context manager."""

    def __init__(self, message: str = "Processing...", silent: bool = False):
        self._message = message
        self.silent = silent
        if not self.silent:
            self._stop_event = threading.Event()
            self._spinner_thread = threading.Thread(target=self._spin)

    def _spin(self):
        spinner_chars = "|/-\\"
        i = 0
        while not self._stop_event.is_set():
            char = spinner_chars[i % len(spinner_chars)]
            sys.stdout.write(f"\r{self._message} {char}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1
        # Clear the line
        sys.stdout.write(f"\r{' ' * (len(self._message) + 2)}\r")
        sys.stdout.flush()

    def __enter__(self):
        if not self.silent:
            self._spinner_thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not self.silent:
            self._stop_event.set()
            self._spinner_thread.join()


def get_config_value(section: str, key: str, fallback: any = None) -> any:
    """Reads a value from ~/.sagemcom.conf."""
    config = configparser.ConfigParser()
    config_file = Path.home() / ".sagemcom.conf"
    if config_file.exists():
        config.read(config_file)
    return config.get(section, key, fallback=fallback)


def print_colored(message: str, color: str = ""):
    """Print colored output for terminal"""
    colors = {
        "red": "\033[0;31m",
        "green": "\033[0;32m",
        "blue": "\033[0;34m",
        "yellow": "\033[1;33m",
        "reset": "\033[0m",
    }

    if color and color in colors:
        print(f"{colors[color]}{message}{colors['reset']}")
    else:
        print(message)


def log_info(message: str):
    """

    :param message:
    """
    print_colored(f"ℹ️  {message}", "blue")


def log_success(message: str):
    """

    :param message:
    """
    print_colored(f"✅ {message}", "green")


def log_error(message: str):
    """

    :param message:
    """
    print_colored(f"❌ {message}", "red")


def log_warning(message: str):
    """

    :param message:
    """
    print_colored(f"⚠️  {message}", "yellow")


def open_port(args):
    """Open a port forwarding rule"""
    if not all([args.name, args.local_address, args.local_port, args.external_port]):
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Missing required parameters for opening port. Required: --name, --local-address, --local-port, --external-port",
                    },
                    indent=2,
                )
            )
        else:
            log_error("Missing required parameters for opening port")
            print("Required: --name, --local-address, --local-port, --external-port")
        return False

    # Validate ports
    if not validate_port(args.local_port) or not validate_port(args.external_port):
        if args.json:
            print(
                json.dumps(
                    {"status": "error", "message": "Invalid port number(s)"}, indent=2
                )
            )
        else:
            log_error("Invalid port number(s)")
        return False

    # Expand IP shorthand
    local_addr = expand_ip_shorthand(args.local_address)

    # Create router client
    client = create_router_client("rest", host=args.host)

    # Authenticate
    with Spinner("Authenticating with router...", silent=args.json):
        authenticated = client.authenticate()

    if not authenticated:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Failed to authenticate with router",
                    },
                    indent=2,
                )
            )
        else:
            log_error("Failed to authenticate with router")
        return False

    # Create port forwarding rule
    rule = PortForwardingRule(
        name=args.name,
        local_address=local_addr,
        local_port=int(args.local_port),
        external_port=int(args.external_port),
        protocol=args.protocol,
    )

    with Spinner(f"Creating port forward: {args.name}...", silent=args.json):
        success = client.add_port_forward(rule)

    if success:
        if args.json:
            rule_dict = {
                "name": rule.name,
                "local_address": rule.local_address,
                "local_port": rule.local_port,
                "external_port": rule.external_port,
                "protocol": rule.protocol,
            }
            print(
                json.dumps(
                    {
                        "status": "success",
                        "message": "Port forward created successfully",
                        "rule": rule_dict,
                    },
                    indent=2,
                )
            )
        else:
            log_success("Port forward created successfully")
            print(f"Rule: {args.name}")
            print(f"External Port: {args.external_port}")
            print(f"Internal: {local_addr}:{args.local_port}")
            print(f"Protocol: {args.protocol.upper()}")
        return True
    else:
        if args.json:
            print(
                json.dumps(
                    {"status": "error", "message": "Failed to create port forward"},
                    indent=2,
                )
            )
        else:
            log_error("Failed to create port forward")
        return False


def close_port(args):
    """Close a port forwarding rule"""
    if not args.port:
        if args.json:
            print(
                json.dumps(
                    {"status": "error", "message": "External port number is required"},
                    indent=2,
                )
            )
        else:
            log_error("External port number is required")
        return False

    # Validate port
    if not validate_port(args.port):
        if args.json:
            print(
                json.dumps(
                    {"status": "error", "message": "Invalid port number"}, indent=2
                )
            )
        else:
            log_error("Invalid port number")
        return False

    # Create router client
    client = create_router_client("rest", host=args.host)

    # Authenticate
    with Spinner("Authenticating with router...", silent=args.json):
        authenticated = client.authenticate()

    if not authenticated:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Failed to authenticate with router",
                    },
                    indent=2,
                )
            )
        else:
            log_error("Failed to authenticate with router")
        return False

    with Spinner(
        f"Removing port forward for external port: {args.port}...", silent=args.json
    ):
        success = client.remove_port_forward_by_port(int(args.port))

    if success:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "success",
                        "message": f"Port forward for port {args.port} removed successfully",
                    },
                    indent=2,
                )
            )
        else:
            log_success(f"Port forward for port {args.port} removed successfully")
        return True
    else:
        if args.json:
            print(
                json.dumps(
                    {"status": "error", "message": "Failed to remove port forward"},
                    indent=2,
                )
            )
        else:
            log_error("Failed to remove port forward")
        return False


def list_ports(args):
    """List all port forwarding rules"""
    # Create router client
    client = create_router_client("rest", host=args.host)

    # Authenticate
    with Spinner("Authenticating with router...", silent=args.json):
        authenticated = client.authenticate()

    if not authenticated:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Failed to authenticate with router",
                    },
                    indent=2,
                )
            )
        else:
            log_error("Failed to authenticate with router")
        return False

    with Spinner("Retrieving port forwards...", silent=args.json):
        rules = client.get_port_forwards()

    if args.json:
        print(json.dumps(rules, indent=2))
        return True

    if not rules:
        print_colored("🔒 No port forwarding rules found", "yellow")
        return True

    print_colored("🌐 Current Port Forwarding Rules:", "blue")

    # Prepare data for table
    header = ["Name", "Status", "External Port", "Internal", "Protocol"]
    rows = []
    for rule in rules:
        status = "✅ Enabled" if rule.get("enabled", False) else "❌ Disabled"
        rows.append(
            [
                rule.get("name", "N/A"),
                status,
                str(rule.get("externalPort", "N/A")),
                f"{rule.get('localAddress', 'N/A')}:{rule.get('localPort', 'N/A')}",
                rule.get("protocol", "N/A").upper(),
            ]
        )

    # Calculate column widths
    col_widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            # Adjust for emoji width which can be 2 chars
            cell_len = len(cell)
            if "✅" in cell or "❌" in cell:
                cell_len -= 1
            if cell_len > col_widths[i]:
                col_widths[i] = cell_len

    # Print table
    header_line = " | ".join(header[i].ljust(col_widths[i]) for i in range(len(header)))
    print(header_line)
    print("-" * len(header_line))

    for row in rows:
        # Manual padding adjustment for emoji
        padded_row = []
        for i, cell in enumerate(row):
            cell_len = len(cell)
            if "✅" in cell or "❌" in cell:
                cell_len -= 1
            padding = " " * (col_widths[i] - cell_len)
            padded_row.append(f"{cell}{padding}")
        print(" | ".join(padded_row))

    return True


def open_browser(args):
    """Open router web interface in browser"""
    # Create router client
    client = create_router_client("rest", host=args.host)

    # Authenticate first to verify connection, then logout to free session
    with Spinner("Verifying router connection...", silent=args.json):
        authenticated = client.authenticate()

    if not authenticated:
        if args.json:
            print(
                json.dumps(
                    {
                        "status": "error",
                        "message": "Failed to authenticate with router",
                    },
                    indent=2,
                )
            )
        else:
            log_error("Failed to authenticate with router")
        return False

    # Logout to free up the session slot for browser login
    with Spinner("Freeing session slot for browser login...", silent=args.json):
        client.logout()

    session_url = client.get_session_url()

    if args.json:
        print(
            json.dumps(
                {
                    "status": "success",
                    "message": "Session URL retrieved.",
                    "url": session_url,
                },
                indent=2,
            )
        )
        return True

    log_info("Opening router web interface...")

    try:
        subprocess.run(
            ["open", session_url],
            check=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
        log_success("Router web interface opened in browser")
        print(f"URL: {session_url}")
        log_info("Please login with your router password")
        log_warning("Note: Only one session is allowed at a time")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        log_error("Unable to open browser automatically")
        print(f"Please open this URL manually: {session_url}")
        return False


def generate_completion_script(args):
    """Generates and prints a shell completion script."""
    if args.shell == "bash":
        # Note: Assumes the script is installed as 'sagemcom-cli'
        script = """
_sagemcom_cli_completion()
{
    local cur prev words cword
    _get_comp_words_by_ref -n : cur prev words cword

    if [[ ${cword} -eq 1 ]]; then
        COMPREPLY=( $(compgen -W "open close list browser completion" -- "${cur}") )
        return 0
    fi

    local command="${words[1]}"
    case "${command}" in
        open)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=( $(compgen -W "--name --local-address --local-port --external-port --protocol --host --json" -- "${cur}") )
            else
                case "${prev}" in
                    --protocol)
                        COMPREPLY=( $(compgen -W "tcp udp tcp_udp" -- "${cur}") )
                        ;;
                esac
            fi
            ;;
        close)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=( $(compgen -W "--port --host --json" -- "${cur}") )
            fi
            ;;
        list|browser)
            if [[ "$cur" == -* ]]; then
                COMPREPLY=( $(compgen -W "--host --json" -- "${cur}") )
            fi
            ;;
        completion)
            if [[ ${cword} -eq 2 ]]; then
                COMPREPLY=( $(compgen -W "bash" -- "${cur}") )
            fi
            ;;
    esac
}
complete -F _sagemcom_cli_completion sagemcom-cli
        """
        print(script.strip())
        print(
            "\n# To enable completion, add the following to your .bashrc or .bash_profile:"
        )
        print('# eval "$(sagemcom-cli completion bash)"')
        print(
            "# Note: You may need to restart your shell for changes to take effect.",
            file=sys.stderr,
        )
        return True
    return False


def main():
    """Main CLI interface"""
    default_host = get_config_value("sagemcom", "host", fallback="192.168.178.1")

    parser = argparse.ArgumentParser(
        description="Sagemcom Router Port Forward Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sagemcom-cli open --name "Web Server" --local-address 100 --local-port 80 --external-port 8080
  sagemcom-cli close --port 8080
  sagemcom-cli list
  sagemcom-cli list --json
  sagemcom-cli browser
  sagemcom-cli completion bash
        """,
    )

    parser.add_argument(
        "--host",
        default=default_host,
        help=f"Router IP address (default: {default_host})",
    )
    parser.add_argument(
        "--json", action="store_true", help="Output in JSON format for machine parsing"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", required=True
    )

    # Open port command
    open_parser = subparsers.add_parser("open", help="Open a port forwarding rule")
    open_parser.add_argument(
        "--name", required=True, help="Name for the port forwarding rule"
    )
    open_parser.add_argument(
        "--local-address",
        required=True,
        help='Local IP address (full IP or shorthand like "100")',
    )
    open_parser.add_argument(
        "--local-port", required=True, type=int, help="Local port number"
    )
    open_parser.add_argument(
        "--external-port", required=True, type=int, help="External port number"
    )
    open_parser.add_argument(
        "--protocol",
        choices=["tcp", "udp", "tcp_udp"],
        default="tcp",
        help="Protocol (default: tcp)",
    )

    # Close port command
    close_parser = subparsers.add_parser("close", help="Close a port forwarding rule")
    close_parser.add_argument(
        "--port",
        required=True,
        type=int,
        help="External port number of the rule to remove",
    )

    # List ports command
    subparsers.add_parser("list", help="List all port forwarding rules")

    # Browser command
    subparsers.add_parser("browser", help="Open router web interface in browser")

    # Completion command
    completion_parser = subparsers.add_parser(
        "completion", help="Generate shell completion script"
    )
    completion_parser.add_argument(
        "shell",
        choices=["bash"],
        default="bash",
        nargs="?",
        help="The shell to generate completion for (default: bash)",
    )

    args = parser.parse_args()

    # Execute command
    success = False
    if args.command == "open":
        success = open_port(args)
    elif args.command == "close":
        success = close_port(args)
    elif args.command == "list":
        success = list_ports(args)
    elif args.command == "browser":
        success = open_browser(args)
    elif args.command == "completion":
        success = generate_completion_script(args)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
