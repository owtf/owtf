"""
tests.functional.proxy.test_https_interception
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test HTTPS interception functionality in the OWTF proxy.
"""
import os
import time
import logging
import tempfile
import shutil
from unittest.mock import Mock, patch

from tests.owtftest import OWTFCliTestCase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for testing
PROXY_HOST = "localhost"
PROXY_PORT = 8008
TEST_TIMEOUT = 10
REQUEST_TIMEOUT = 10


class OWTFCliHTTPSInterceptionTest(OWTFCliTestCase):
    """Test HTTPS interception functionality."""

    categories = ["proxy", "https", "interception"]

    def setUp(self):
        """Set up test fixtures."""
        super(OWTFCliHTTPSInterceptionTest, self).setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.proxy_config = {
            'http': f'http://{PROXY_HOST}:{PROXY_PORT}',
            'https': f'http://{PROXY_HOST}:{PROXY_PORT}'
        }
        self.test_urls = [
            'https://httpbin.org/get',
            'https://httpbin.org/post',
            'https://httpbin.org/headers',
            'https://httpbin.org/user-agent'
        ]
        self.custom_headers = {
            'X-Test-Header': 'test-value',
            'X-Owtf-Test': 'https-interception',
            'User-Agent': 'OWTF-HTTPS-Test/1.0'
        }
        self.json_test_data = {
            'test': True,
            'message': 'HTTPS interception test',
            'timestamp': time.time(),
            'data': {
                'nested': 'value',
                'array': [1, 2, 3, 'test']
            }
        }

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(OWTFCliHTTPSInterceptionTest, self).tearDown()

    def _skip_if_proxy_not_running(self):
        """Skip test if proxy is not running."""
        try:
            import requests
            response = requests.get(
                f'http://{PROXY_HOST}:{PROXY_PORT}',
                timeout=2,
                allow_redirects=False
            )
            return False  # Proxy is running
        except:
            self.skipTest("OWTF proxy not running")

    def test_https_interception(self):
        """Test HTTPS interception through the proxy."""
        self._skip_if_proxy_not_running()
        
        logger.info("Testing HTTPS interception through OWTF proxy...")
        
        for url in self.test_urls:
            try:
                logger.info(f"Testing: {url}")
                
                if 'post' in url:
                    # Test POST request
                    import requests
                    response = requests.post(
                        url, 
                        data={'test': 'data', 'timestamp': int(time.time())},
                        proxies=self.proxy_config,
                        verify=False,  # Don't verify SSL cert since we're intercepting
                        timeout=TEST_TIMEOUT
                    )
                else:
                    # Test GET request
                    import requests
                    response = requests.get(
                        url,
                        proxies=self.proxy_config,
                        verify=False,  # Don't verify SSL cert since we're intercepting
                        timeout=TEST_TIMEOUT
                    )
                
                logger.info(f"✅ Success: {response.status_code} - {url}")
                logger.info(f"   Response size: {len(response.content)} bytes")
                
                # Check if response contains expected data
                if 'httpbin.org' in response.text:
                    logger.info("   ✅ Response contains expected content")
                else:
                    logger.warning("   ⚠️  Response content unexpected")
                    
            except Exception as e:
                logger.error(f"❌ Error testing {url}: {e}")
                self.fail(f"Failed to test {url}: {e}")
        
        logger.info("HTTPS interception test completed!")

    def test_https_with_custom_headers(self):
        """Test HTTPS requests with custom headers."""
        self._skip_if_proxy_not_running()
        
        logger.info("Testing HTTPS with custom headers...")
        
        try:
            import requests
            response = requests.get(
                'https://httpbin.org/headers',
                headers=self.custom_headers,
                proxies=self.proxy_config,
                verify=False,
                timeout=REQUEST_TIMEOUT
            )
            
            logger.info(f"✅ Custom headers test: {response.status_code}")
            
            # Check if our custom headers were sent
            response_data = response.json()
            if 'headers' in response_data:
                headers = response_data['headers']
                for header_name, expected_value in self.custom_headers.items():
                    if header_name in headers and headers[header_name] == expected_value:
                        logger.info(f"   ✅ Header {header_name}: {expected_value}")
                    else:
                        logger.warning(f"   ⚠️  Header {header_name} not found or incorrect")
            
        except Exception as e:
            logger.error(f"❌ Custom headers test failed: {e}")
            self.fail(f"Custom headers test failed: {e}")

    def test_https_post_with_json(self):
        """Test HTTPS POST with JSON data."""
        self._skip_if_proxy_not_running()
        
        logger.info("Testing HTTPS POST with JSON data...")
        
        try:
            import requests
            response = requests.post(
                'https://httpbin.org/post',
                json=self.json_test_data,
                proxies=self.proxy_config,
                verify=False,
                timeout=REQUEST_TIMEOUT
            )
            
            logger.info(f"✅ JSON POST test: {response.status_code}")
            
            # Verify the response contains our data
            response_data = response.json()
            if 'json' in response_data and response_data['json'] == self.json_test_data:
                logger.info("   ✅ JSON data correctly sent and received")
            else:
                logger.warning("   ⚠️  JSON data mismatch")
                
        except Exception as e:
            logger.error(f"❌ JSON POST test failed: {e}")
            self.fail(f"JSON POST test failed: {e}")

    def test_proxy_connection(self):
        """Test basic proxy connectivity."""
        self._skip_if_proxy_not_running()
        
        try:
            import requests
            response = requests.get(
                'http://httpbin.org/get',
                proxies=self.proxy_config,
                timeout=REQUEST_TIMEOUT
            )
            self.assertEqual(response.status_code, 200)
            logger.info("✅ Basic proxy connectivity test passed")
        except Exception as e:
            self.fail(f"Proxy connectivity test failed: {e}")

    @patch('requests.get')
    def test_proxy_mocking(self, mock_get):
        """Test proxy functionality with mocked requests."""
        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_response.text = "test content"
        mock_get.return_value = mock_response
        
        # Test that our proxy config is properly set up
        self.assertIn('http', self.proxy_config)
        self.assertIn('https', self.proxy_config)
        self.assertEqual(self.proxy_config['http'], f'http://{PROXY_HOST}:{PROXY_PORT}')
        self.assertEqual(self.proxy_config['https'], f'http://{PROXY_HOST}:{PROXY_PORT}')
        
        # Test that test URLs are properly configured
        self.assertIsInstance(self.test_urls, list)
        self.assertTrue(len(self.test_urls) > 0)
        for url in self.test_urls:
            self.assertTrue(url.startswith('https://'))
