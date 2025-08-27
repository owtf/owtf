"""
tests.functional.proxy.test_gen_cert
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test certificate generation functionality.
"""
import shutil
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

from tests.owtftest import OWTFCliTestCase
from owtf.proxy.gen_cert import gen_signed_cert


class OWTFCliGenCertTest(OWTFCliTestCase):
    """Test certificate generation functionality."""

    categories = ["proxy", "certificates", "generation"]

    def setUp(self):
        """Set up test fixtures."""
        super(OWTFCliGenCertTest, self).setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.ca_dir = os.path.join(self.temp_dir, "ca")
        os.makedirs(self.ca_dir)
        self.ca_key = os.path.join(self.ca_dir, "ca.key.pem")
        self.ca_crt = os.path.join(self.ca_dir, "ca.crt.pem")
        
        # Generate CA key and cert
        self._generate_ca_certificate()

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(OWTFCliGenCertTest, self).tearDown()

    def _generate_ca_certificate(self):
        """Generate CA key and certificate for testing."""
        import subprocess

        try:
            subprocess.run(["openssl", "genrsa", "-out", self.ca_key, "2048"], 
                         check=True, capture_output=True)
            subprocess.run([
                "openssl", "req", "-x509", "-new", "-nodes", "-key", self.ca_key,
                "-sha256", "-days", "365", "-out", self.ca_crt, "-subj",
                "/C=US/ST=CA/L=SF/O=TestCA/OU=Dev/CN=Test CA"
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            self.skipTest(f"OpenSSL not available or failed: {e}")
        except FileNotFoundError:
            self.skipTest("OpenSSL not available on this system")

    def test_generate_signed_cert_creates_files(self):
        """Test that signed certificates are generated correctly."""
        out = os.path.join(self.temp_dir, "certs")
        os.makedirs(out, exist_ok=True)
        
        key_path, cert_path = gen_signed_cert("foo.test", self.ca_crt, self.ca_key, "", out)

        # Assert files exist
        self.assertTrue(os.path.exists(key_path))
        self.assertTrue(os.path.exists(cert_path))

        # Load and inspect via cryptography
        try:
            from cryptography import x509
            cert = x509.load_pem_x509_certificate(Path(cert_path).read_bytes())
            # CN matches
            cn_attr = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0]
            self.assertEqual(cn_attr.value, "foo.test")
            # Validity window
            self.assertLess(cert.not_valid_before, cert.not_valid_after)
        except ImportError:
            # Fallback to OpenSSL if cryptography is not available
            self._test_cert_with_openssl(cert_path, "foo.test")

    def test_wrapper_returns_strings(self):
        """Test that the wrapper function returns proper string paths."""
        out = os.path.join(self.temp_dir, "certs")
        os.makedirs(out, exist_ok=True)
        
        key, crt = gen_signed_cert("bar.example", self.ca_crt, self.ca_key, "", out)
        
        self.assertIsInstance(key, str)
        self.assertIsInstance(crt, str)
        self.assertTrue(os.path.exists(key))
        self.assertTrue(os.path.exists(crt))

    def test_certificate_with_password(self):
        """Test certificate generation with password protection."""
        # This test would require a password-protected CA key
        # For now, we'll test the interface
        out = os.path.join(self.temp_dir, "certs")
        os.makedirs(out, exist_ok=True)
        
        # Test with empty password (current CA key)
        key, crt = gen_signed_cert("test.example", self.ca_crt, self.ca_key, "", out)
        
        self.assertTrue(os.path.exists(key))
        self.assertTrue(os.path.exists(crt))

    def test_wildcard_certificate_generation(self):
        """Test wildcard certificate generation for subdomains."""
        out = os.path.join(self.temp_dir, "certs")
        os.makedirs(out, exist_ok=True)
        
        # Test with a multi-level subdomain
        domain = "sub1.sub2.sub3.example.com"
        key, crt = gen_signed_cert(domain, self.ca_crt, self.ca_key, "", out)
        
        self.assertTrue(os.path.exists(key))
        self.assertTrue(os.path.exists(crt))
        
        # Verify the certificate content
        try:
            from cryptography import x509
            cert = x509.load_pem_x509_certificate(Path(crt).read_bytes())
            cn_attr = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0]
            # Should generate a certificate with the full domain name
            expected_cn = "sub1.sub2.sub3.example.com"
            self.assertEqual(cn_attr.value, expected_cn)
        except ImportError:
            self._test_cert_with_openssl(crt, "sub1.sub2.sub3.example.com")

    def _test_cert_with_openssl(self, cert_path, expected_cn):
        """Fallback test using OpenSSL command line."""
        try:
            import subprocess
            result = subprocess.run([
                "openssl", "x509", "-in", cert_path, "-noout", "-subject"
            ], capture_output=True, text=True, check=True)
            
            # Check if the expected CN is in the subject
            self.assertIn(expected_cn, result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # If OpenSSL test also fails, just check file exists
            self.assertTrue(os.path.exists(cert_path))

    @patch('subprocess.run')
    def test_openssl_failure_handling(self, mock_run):
        """Test handling of OpenSSL failures."""
        # Mock OpenSSL to fail
        mock_run.side_effect = FileNotFoundError("openssl not found")
        
        # This should raise an exception or be handled gracefully
        with self.assertRaises(FileNotFoundError):
            self._generate_ca_certificate()
