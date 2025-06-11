import unittest
from unittest.mock import patch, MagicMock, call
import argparse

from sagemcom_mcp import cli

class TestCliWrapper(unittest.TestCase):

    def setUp(self):
        # Create a mock client for all tests
        self.mock_client = MagicMock()
        # Patch the create_router_client function to return our mock client
        self.patcher = patch('sagemcom_mcp.cli.create_router_client')
        self.mock_create_client = self.patcher.start()
        self.mock_create_client.return_value = self.mock_client

    def tearDown(self):
        self.patcher.stop()

    def test_open_port_success(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.add_port_forward.return_value = True
        
        args = argparse.Namespace(
            host='1.2.3.4', name='TestRule', local_address='100', 
            local_port=80, external_port=8080, protocol='tcp'
        )
        
        result = cli.open_port(args)
        
        self.assertTrue(result)
        self.mock_create_client.assert_called_with("rest", host="1.2.3.4")
        self.mock_client.authenticate.assert_called_once()
        self.mock_client.add_port_forward.assert_called_once()
        
        # Check that the rule passed to add_port_forward is correct
        call_args, _ = self.mock_client.add_port_forward.call_args
        rule = call_args[0]
        self.assertEqual(rule.name, 'TestRule')
        self.assertEqual(rule.local_address, '192.168.178.100') # Expanded
        self.assertEqual(rule.local_port, 80)

    def test_open_port_auth_fail(self):
        self.mock_client.authenticate.return_value = False
        args = argparse.Namespace(
            host='1.2.3.4', name='TestRule', local_address='100', 
            local_port=80, external_port=8080, protocol='tcp'
        )
        result = cli.open_port(args)
        self.assertFalse(result)

    def test_close_port_success(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.remove_port_forward_by_port.return_value = True
        
        args = argparse.Namespace(host='1.2.3.4', port=8080)
        
        result = cli.close_port(args)
        
        self.assertTrue(result)
        self.mock_client.authenticate.assert_called_once()
        self.mock_client.remove_port_forward_by_port.assert_called_with(8080)

    def test_list_ports(self):
        self.mock_client.authenticate.return_value = True
        self.mock_client.get_port_forwards.return_value = [
            {'name': 'Web Server', 'localAddress': '192.168.178.50', 'localPort': 80, 'externalPort': 8080, 'protocol': 'TCP', 'enabled': True}
        ]
        
        args = argparse.Namespace(host='1.2.3.4')
        
        with patch('sagemcom_mcp.cli.print') as mock_print:
            result = cli.list_ports(args)
            self.assertTrue(result)
            
            # Check if the output contains expected strings
            self.assertTrue(any("Web Server" in str(c) for c in mock_print.call_args_list))
            self.assertTrue(any("8080 -> Internal: 192.168.178.50:80" in str(c) for c in mock_print.call_args_list))

    @patch('subprocess.run')
    def test_open_browser(self, mock_subprocess):
        self.mock_client.authenticate.return_value = True
        self.mock_client.get_session_url.return_value = "http://fake-router"
        
        args = argparse.Namespace(host='1.2.3.4')
        
        result = cli.open_browser(args)
        
        self.assertTrue(result)
        self.mock_client.authenticate.assert_called_once()
        self.mock_client.logout.assert_called_once()
        mock_subprocess.assert_called_with(["open", "http://fake-router"], check=True)

if __name__ == '__main__':
    unittest.main()
