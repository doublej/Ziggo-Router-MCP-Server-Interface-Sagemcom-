"""
Shared Sagemcom Router Client
Common interface for tcp_udp REST and XPath API approaches
"""

import requests
import json
import logging
import subprocess
import os
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class PortForwardingRule:
    """Standardized port forwarding rule representation"""
    name: str
    local_address: str
    local_port: int
    external_port: int
    protocol: str  # "tcp", "udp", or "tcp_udp"
    enabled: bool = True

    def to_rest_payload(self) -> Dict[str, Any]:
        """Convert to REST API payload format"""
        return {"rule": {"localAddress": self.local_address, "localStartPort": self.local_port, "localEndPort": self.local_port, "externalStartPort": self.external_port, "externalEndPort": self.external_port, "protocol": self.protocol.lower(), "enable": self.enabled}}


class RouterClientInterface(ABC):
    """Abstract interface for router client implementations"""

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the router"""
        pass

    @abstractmethod
    def get_port_forwards(self) -> List[Dict[str, Any]]:
        """Get current port forwarding rules"""
        pass

    @abstractmethod
    def add_port_forward(self, rule: PortForwardingRule) -> bool:
        """Add a port forwarding rule"""
        pass

    @abstractmethod
    def remove_port_forward(self, rule_name: str) -> bool:
        """Remove a port forwarding rule by name"""
        pass

    @abstractmethod
    def get_session_url(self) -> str:
        """Get URL for browser session transfer"""
        pass


class SagemcomRestClient(RouterClientInterface):
    """REST API client for Sagemcom routers (Ziggo-style)"""

    def __init__(self, host: str = None, port: int = 80):
        # Use environment variable if no host provided
        self.host = host or os.getenv("SAGEMCOM_MODEM_IP", "192.168.178.1")
        self.port = port
        self.base_url = f"http://{self.host}:{port}"
        self.token = None
        self.user_id = None

    def _get_rest_url(self, endpoint: str) -> str:
        """Build REST API URL"""
        return f"{self.base_url}/rest/v1/{endpoint}"

    def _get_password_from_1password(self, item_name) -> Optional[str]:
        """Get router password from 1Password CLI"""
        try:
            result = subprocess.run(["op", "item", "get", item_name, "--fields", "password", "--format", "json"], capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            return data.get("value")
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to get password from 1Password: {e}")
            return None

    def _get_password(self) -> Optional[str]:
        """Get router password from various sources in order of priority"""

        return os.getenv("SAGEMCOM_MODEM_PASSWORD", self._get_password_from_1password(os.getenv("SAGEMCOM_ONEPASSWORD_ITEM", "Ziggo")))

    def authenticate(self) -> bool:
        """Authenticate with the router using REST API"""
        password = self._get_password()
        if not password:
            logger.error("Could not retrieve password from any source (direct, env var SAGEMCOM_MODEM_PASSWORD, or 1Password)")
            return False

        try:
            response = requests.post(
                    self._get_rest_url("user/login"), json={"password": password}, headers={"Connection": "keep-alive"}, timeout=10
            )
            response.raise_for_status()

            data = response.json()
            created = data.get("created", {})
            self.token = created.get("token")
            self.user_id = created.get("userId")

            if self.token:
                logger.info("Successfully authenticated with router via REST API")
                return True

        except requests.RequestException as e:
            logger.error(f"REST API authentication failed: {e}")

        return False

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.token:
            raise ValueError("Not authenticated - call authenticate() first")
        return {"Authorization": f"Bearer {self.token}"}

    def get_port_forwards(self) -> List[Dict[str, Any]]:
        """Get current port forwarding rules via REST API"""
        try:
            response = requests.get(
                    self._get_rest_url("network/portforwarding"), headers=self._get_auth_headers(), timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # The Ziggo router returns nested structure: {"portforwarding": {"rules": [...]}}
            port_forwarding_data = data.get("portforwarding", {})
            if isinstance(port_forwarding_data, dict):
                rules_list = port_forwarding_data.get("rules", [])
            else:
                # Fallback for different API structure
                rules_list = port_forwarding_data if isinstance(port_forwarding_data, list) else []

            # Transform the rules to a more standard format
            formatted_rules = []
            for rule_item in rules_list:
                if isinstance(rule_item, dict) and 'rule' in rule_item:
                    rule_data = rule_item['rule']
                    formatted_rule = {'id':           rule_item.get('id'), 'name': f"Rule {rule_item.get('id', 'Unknown')}",  # Ziggo doesn't have names, use ID
                                      'localAddress': rule_data.get('localAddress'), 'localPort': rule_data.get('localStartPort'), 'externalPort': rule_data.get('externalStartPort'), 'protocol': rule_data.get('protocol', '').replace('_', '/'),  # Convert tcp_udp to tcp/udp
                                      'enabled':      rule_data.get('enable', False)}
                    formatted_rules.append(formatted_rule)

            return formatted_rules

        except requests.RequestException as e:
            logger.error(f"Failed to get port forwards via REST API: {e}")
            return []

    def add_port_forward(self, rule: PortForwardingRule) -> bool:
        """Add a port forwarding rule via REST API"""
        try:
            response = requests.post(
                    self._get_rest_url("network/portforwarding"), json=rule.to_rest_payload(), headers=self._get_auth_headers(), timeout=10
            )
            response.raise_for_status()

            logger.info(f"Successfully added port forward via REST API: {rule.name}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to add port forward via REST API: {e}")
            return False

    def remove_port_forward_by_name(self, rule_name: str) -> bool:
        """Remove a port forwarding rule by name via REST API"""
        # First get all rules to find the one to delete
        rules = self.get_port_forwards()
        rule_to_delete = None

        for rule in rules:
            if rule.get("name") == rule_name:
                rule_to_delete = rule
                break

        if not rule_to_delete:
            logger.error(f"Port forward rule '{rule_name}' not found")
            return False

        return self._delete_port_forward_rule(rule_to_delete, rule_name)

    def remove_port_forward_by_port(self, external_port: int) -> bool:
        """Remove a port forwarding rule by external port number via REST API"""
        # First get all rules to find the one to delete
        rules = self.get_port_forwards()
        matching_rules = []

        for rule in rules:
            if rule.get("externalPort") == external_port:
                matching_rules.append(rule)

        if not matching_rules:
            logger.error(f"No port forward rule found for external port {external_port}")
            return False

        if len(matching_rules) > 1:
            logger.error(f"Multiple rules found for port {external_port}. Found {len(matching_rules)} rules.")
            return False

        rule_to_delete = matching_rules[0]
        rule_identifier = f"port {external_port} (Rule {rule_to_delete.get('id')})"
        return self._delete_port_forward_rule(rule_to_delete, rule_identifier)

    def _delete_port_forward_rule(self, rule_to_delete: dict, identifier: str) -> bool:
        """Helper method to delete a port forwarding rule"""
        try:
            # Need to reconstruct the original API format for deletion
            original_rule = {"id": rule_to_delete.get("id"), "rule": {"enable": rule_to_delete.get("enabled", False), "externalStartPort": rule_to_delete.get("externalPort"), "externalEndPort": rule_to_delete.get("externalPort"), "protocol": rule_to_delete.get("protocol", "tcp").replace("/", "_"), "localStartPort": rule_to_delete.get("localPort"), "localEndPort": rule_to_delete.get("localPort"), "localAddress": rule_to_delete.get("localAddress"), "readOnly": False}}

            response = requests.delete(
                    self._get_rest_url("network/portforwarding"), json={"portforwarding": {"rules": [original_rule]}}, headers=self._get_auth_headers(), timeout=10
            )
            response.raise_for_status()

            logger.info(f"Successfully removed port forward via REST API: {identifier}")
            return True

        except requests.RequestException as e:
            logger.error(f"Failed to remove port forward via REST API: {e}")
            return False

    def remove_port_forward(self, rule_name: str) -> bool:
        """Backward compatibility method - remove by name"""
        return self.remove_port_forward_by_name(rule_name)

    def get_session_url(self) -> str:
        """Get URL for browser session transfer"""
        # For Ziggo routers, the token approach doesn't work properly
        # Just return the base URL since user will need to authenticate manually
        return self.base_url

    def logout(self) -> bool:
        """Logout from current session to free up session slot"""
        if not self.token:
            return True

        try:
            response = requests.delete(
                    self._get_rest_url(f"user/{self.user_id}/token/{self.token}"), headers=self._get_auth_headers(), timeout=10
            )
            # Don't check status code as logout might return various codes
            self.token = None
            self.user_id = None
            logger.info("Successfully logged out from router")
            return True

        except requests.RequestException as e:
            logger.warning(f"Logout request failed: {e}")
            # Still clear local token even if request failed
            self.token = None
            self.user_id = None
            return True


def create_router_client(api_type: str = "rest", **kwargs) -> RouterClientInterface:
    """Factory function to create appropriate router client
    
    Args:
        api_type: Type of API client ("rest")
        **kwargs: Additional arguments passed to client constructor
    """
    if api_type.lower() == "rest":
        return SagemcomRestClient(**kwargs)
    else:
        raise ValueError(f"Unsupported API type: {api_type}")


def expand_ip_shorthand(ip: str) -> str:
    """Expand IP shorthand notation (e.g., '100' -> '192.168.178.100')"""
    if ip.isdigit() and 1 <= int(ip) <= 254:
        return f"192.168.178.{ip}"
    return ip


def validate_port(port: Union[int, str]) -> bool:
    """Validate port number range"""
    try:
        port_num = int(port)
        return 1 <= port_num <= 65535
    except (ValueError, TypeError):
        return False
