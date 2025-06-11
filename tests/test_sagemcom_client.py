import unittest
from unittest.mock import patch, Mock
import os
import json
import subprocess
import requests

from sagemcom_mcp.client import (
    SagemcomRestClient,
    PortForwardingRule,
    expand_ip_shorthand,
    validate_port,
    create_router_client
)

class TestSagemcomClientHelpers(unittest.TestCase):
    """Tests for helper functions in sagemcom_client."""

    def test_expand_ip_shorthand(self):
        self.assertEqual(expand_ip_shorthand("100"), "192.168.178.100")
        self.assertEqual(expand_ip_shorthand("192.168.1.50"), "192.168.1.50")
        self.assertEqual(expand_ip_shorthand("invalid"), "invalid")
        self.assertEqual(expand_ip_shorthand("256"), "256")

    def test_validate_port(self):
        self.assertTrue(validate_port(80))
        self.assertTrue(validate_port("8080"))
        self.assertTrue(validate_port(1))
        self.assertTrue(validate_port(65535))
        self.assertFalse(validate_port(0))
        self.assertFalse(validate_port(65536))
        self.assertFalse(validate_port("abc"))
        self.assertFalse(validate_port(None))

    def test_create_router_client(self):
        client = create_router_client("rest", host="1.2.3.4")
        self.assertIsInstance(client, SagemcomRestClient)
        self.assertEqual(client.host, "1.2.3.4")
        with self.assertRaises(ValueError):
            create_router_client("unsupported_type")


class TestSagemcomRestClient(unittest.TestCase):
    """Tests for the SagemcomRestClient class."""

    def setUp(self):
        self.client = SagemcomRestClient(host="1.2.3.4")

    @patch.dict(os.environ, {"SAGEMCOM_MODEM_PASSWORD": "env_password"})
    def test_get_password_from_env(self):
        self.assertEqual(self.client._get_password(), "env_password")

    @patch.dict(os.environ, {"SAGEMCOM_ONEPASSWORD_ITEM": "TestItem"}, clear=True)
    @patch("shared_resources.sagemcom_client.SagemcomRestClient._get_password_from_1password")
    def test_get_password_from_1password(self, mock_1password):
        mock_1password.return_value = "1p_password"
        self.assertEqual(self.client._get_password(), "1p_password")
        mock_1password.assert_called_with("TestItem")

    @patch.dict(os.environ, {}, clear=True)
    @patch("shared_resources.sagemcom_client.SagemcomRestClient._get_password_from_1password", return_value=None)
    def test_get_password_no_source(self, mock_1password):
        self.assertIsNone(self.client._get_password())

    @patch("subprocess.run")
    def test_get_password_from_1password_cli_success(self, mock_run):
        mock_process = Mock()
        mock_process.stdout = json.dumps({"value": "cli_password"})
        mock_run.return_value = mock_process
        
        password = self.client._get_password_from_1password("MyItem")
        self.assertEqual(password, "cli_password")
        mock_run.assert_called_with(
            ["op", "item", "get", "MyItem", "--fields", "password", "--format", "json"],
            capture_output=True, text=True, check=True
        )

    @patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cmd"))
    def test_get_password_from_1password_cli_fail(self, mock_run):
        self.assertIsNone(self.client._get_password_from_1password("MyItem"))

    @patch("requests.post")
    @patch("shared_resources.sagemcom_client.SagemcomRestClient._get_password", return_value="test_pass")
    def test_authenticate_success(self, mock_get_pass, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {
            "created": {"token": "test_token", "userId": "test_user"}
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        self.assertTrue(self.client.authenticate())
        self.assertEqual(self.client.token, "test_token")
        self.assertEqual(self.client.user_id, "test_user")

    @patch("requests.post", side_effect=requests.RequestException("Connection error"))
    @patch("shared_resources.sagemcom_client.SagemcomRestClient._get_password", return_value="test_pass")
    def test_authenticate_failure(self, mock_get_pass, mock_post):
        self.assertFalse(self.client.authenticate())
        self.assertIsNone(self.client.token)

    @patch("requests.get")
    def test_get_port_forwards(self, mock_get):
        self.client.token = "test_token"
        mock_response = Mock()
        mock_response.json.return_value = {
            "portforwarding": {
                "rules": [
                    {"id": 1, "rule": {"localAddress": "192.168.178.10", "localStartPort": 80, "externalStartPort": 8080, "protocol": "tcp", "enable": True}},
                    {"id": 2, "rule": {"localAddress": "192.168.178.11", "localStartPort": 22, "externalStartPort": 2222, "protocol": "tcp_udp", "enable": False}}
                ]
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        rules = self.client.get_port_forwards()
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0]['externalPort'], 8080)
        self.assertEqual(rules[0]['protocol'], 'tcp')
        self.assertTrue(rules[0]['enabled'])
        self.assertEqual(rules[1]['protocol'], 'tcp/udp')
        self.assertFalse(rules[1]['enabled'])

    @patch("requests.post")
    def test_add_port_forward(self, mock_post):
        self.client.token = "test_token"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        rule = PortForwardingRule("test", "192.168.178.20", 3000, 4000, "udp")
        self.assertTrue(self.client.add_port_forward(rule))
        
        expected_payload = {"rule": {"localAddress": "192.168.178.20", "localStartPort": 3000, "localEndPort": 3000, "externalStartPort": 4000, "externalEndPort": 4000, "protocol": "udp", "enable": True}}
        mock_post.assert_called_with(
            self.client._get_rest_url("network/portforwarding"),
            json=expected_payload,
            headers=self.client._get_auth_headers(),
            timeout=10
        )

    @patch("requests.delete")
    @patch("shared_resources.sagemcom_client.SagemcomRestClient.get_port_forwards")
    def test_remove_port_forward_by_port(self, mock_get_rules, mock_delete):
        self.client.token = "test_token"
        mock_get_rules.return_value = [
            {'id': 1, 'name': 'Rule 1', 'localAddress': '192.168.178.10', 'localPort': 80, 'externalPort': 8080, 'protocol': 'tcp', 'enabled': True}
        ]
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_delete.return_value = mock_response

        self.assertTrue(self.client.remove_port_forward_by_port(8080))
        
        expected_payload = {
            "portforwarding": {
                "rules": [
                    {"id": 1, "rule": {"enable": True, "externalStartPort": 8080, "externalEndPort": 8080, "protocol": "tcp", "localStartPort": 80, "localEndPort": 80, "localAddress": "192.168.178.10", "readOnly": False}}
                ]
            }
        }
        mock_delete.assert_called_with(
            self.client._get_rest_url("network/portforwarding"),
            json=expected_payload,
            headers=self.client._get_auth_headers(),
            timeout=10
        )

    def test_get_session_url(self):
        self.assertEqual(self.client.get_session_url(), "http://1.2.3.4:80")

if __name__ == '__main__':
    unittest.main()
