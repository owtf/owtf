#!/usr/bin/env python3
"""
Test script for enhanced HTTPS interception with live interceptor support.
"""

import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_https_interception():
    """Test HTTPS interception through the proxy."""
    
    # Configure proxy
    proxies = {
        'http': 'http://localhost:8008',
        'https': 'http://localhost:8008'
    }
    
    # Test URLs
    test_urls = [
        'https://httpbin.org/get',
        'https://httpbin.org/post',
        'https://httpbin.org/headers',
        'https://httpbin.org/user-agent'
    ]
    
    logger.info("Testing HTTPS interception through OWTF proxy...")
    
    for url in test_urls:
        try:
            logger.info(f"Testing: {url}")
            
            if 'post' in url:
                # Test POST request
                response = requests.post(
                    url, 
                    data={'test': 'data', 'timestamp': int(time.time())},
                    proxies=proxies,
                    verify=False,  # Don't verify SSL cert since we're intercepting
                    timeout=10
                )
            else:
                # Test GET request
                response = requests.get(
                    url,
                    proxies=proxies,
                    verify=False,  # Don't verify SSL cert since we're intercepting
                    timeout=10
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
    
    logger.info("HTTPS interception test completed!")

def test_https_with_custom_headers():
    """Test HTTPS requests with custom headers."""
    
    proxies = {
        'http': 'http://localhost:8008',
        'https': 'http://localhost:8008'
    }
    
    custom_headers = {
        'X-Test-Header': 'test-value',
        'X-Owtf-Test': 'https-interception',
        'User-Agent': 'OWTF-HTTPS-Test/1.0'
    }
    
    logger.info("Testing HTTPS with custom headers...")
    
    try:
        response = requests.get(
            'https://httpbin.org/headers',
            headers=custom_headers,
            proxies=proxies,
            verify=False,
            timeout=10
        )
        
        logger.info(f"✅ Custom headers test: {response.status_code}")
        
        # Check if our custom headers were sent
        response_data = response.json()
        if 'headers' in response_data:
            headers = response_data['headers']
            for header_name, expected_value in custom_headers.items():
                if header_name in headers and headers[header_name] == expected_value:
                    logger.info(f"   ✅ Header {header_name}: {expected_value}")
                else:
                    logger.warning(f"   ⚠️  Header {header_name} not found or incorrect")
        
    except Exception as e:
        logger.error(f"❌ Custom headers test failed: {e}")

def test_https_post_with_json():
    """Test HTTPS POST with JSON data."""
    
    proxies = {
        'http': 'http://localhost:8008',
        'https': 'http://localhost:8008'
    }
    
    json_data = {
        'test': True,
        'message': 'HTTPS interception test',
        'timestamp': time.time(),
        'data': {
            'nested': 'value',
            'array': [1, 2, 3, 'test']
        }
    }
    
    logger.info("Testing HTTPS POST with JSON data...")
    
    try:
        response = requests.post(
            'https://httpbin.org/post',
            json=json_data,
            proxies=proxies,
            verify=False,
            timeout=10
        )
        
        logger.info(f"✅ JSON POST test: {response.status_code}")
        
        # Verify the response contains our data
        response_data = response.json()
        if 'json' in response_data and response_data['json'] == json_data:
            logger.info("   ✅ JSON data correctly sent and received")
        else:
            logger.warning("   ⚠️  JSON data mismatch")
            
    except Exception as e:
        logger.error(f"❌ JSON POST test failed: {e}")

if __name__ == "__main__":
    logger.info("🚀 Starting Enhanced HTTPS Interception Tests")
    logger.info("=" * 50)
    
    # Run all tests
    test_https_interception()
    print()
    test_https_with_custom_headers()
    print()
    test_https_post_with_json()
    
    logger.info("=" * 50)
    logger.info("🎉 All HTTPS interception tests completed!")
    logger.info("\nCheck the proxy logs to see intercepted HTTPS traffic:")
    logger.info("tail -f /tmp/owtf/request_response.log")
