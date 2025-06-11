import unittest
from unittest.mock import patch, MagicMock

# Mock the MCP decorator before importing the server
# This prevents the tools from being registered with a real MCP instance
def dummy_decorator(*args, **kwargs):
    def wrapper(func):
        return func
    return wrapper

patch('mcp.server.fastmcp.FastMCP.tool', dummy_decorator).start()
patch('mcp.server.fastmcp.FastMCP.resource', dummy_decorator).start()

from sagemcom_mcp_server import server

class TestMCPServerTools(unittest.TestCase):

    def setUp(self):
        # Create a mock client for all tests
        self.mock_client = MagicMock()
        # Patch the get_router_client function to return our mock client
        self.patcher = patch('sagemcom_mcp_server.server.get_router_client')
        self.mock_get_client = self.patcher.start()
        self.mock_get_client.return_value = self.mock_client

    def tearDown(self):
        self.patcher.stop()

    def test_open_port_success(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.add_port_forward.return_value = True

        result = server.open_port("Test", "100", 80, 8080, "tcp")
        
        self.mock_client.authenticate.assert_called_once()
        self.mock_client.add_port_forward.assert_called_once()
        self.assertIn("Successfully opened port", result)

    def test_open_port_auth_failure(self):
        self.mock_client.authenticate.return_value = False
        result = server.open_port("Test", "100", 80, 8080)
        self.assertIn("Failed to authenticate", result)

    def test_open_port_invalid_port(self):
        result = server.open_port("Test", "100", 70000, 8080)
        self.assertIn("Invalid port number", result)

    def test_close_port_success(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.remove_port_forward_by_port.return_value = True

        result = server.close_port(8080)
        
        self.mock_client.authenticate.assert_called_once()
        self.mock_client.remove_port_forward_by_port.assert_called_with(8080)
        self.assertIn("Successfully closed port", result)

    def test_close_port_failure(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.remove_port_forward_by_port.return_value = False
        result = server.close_port(8080)
        self.assertIn("Failed to remove port", result)

    def test_list_port_forwards_success(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.get_port_forwards.return_value = [
            {"name": "HTTP", "externalPort": 80, "localAddress": "192.168.1.10", "localPort": 80, "protocol": "tcp", "enabled": True}
        ]
        result = server.list_port_forwards()
        self.assertIn("HTTP: 80 -> 192.168.1.10:80 (tcp) [enabled]", result)

    def test_list_port_forwards_no_rules(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.get_port_forwards.return_value = []
        result = server.list_port_forwards()
        self.assertEqual("No port forwarding rules found", result)

    @patch('subprocess.run')
    def test_open_router_in_browser_success(self, mock_subprocess):
        self.mock_client.authenticate.return_value = True
        self.mock_client.get_session_url.return_value = "http://fake-router"
        
        result = server.open_router_in_browser()

        self.mock_client.logout.assert_called_once()
        mock_subprocess.assert_called_with(["open", "http://fake-router"], check=True)
        self.assertIn("Opened router web interface", result)

if __name__ == '__main__':
    unittest.main()
