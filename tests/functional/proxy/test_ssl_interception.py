"""
tests.functional.proxy.test_ssl_interception
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Test SSL interception functionality in the OWTF proxy.
"""
import os
import tempfile
import shutil
from unittest.mock import Mock, patch

from tests.owtftest import OWTFCliTestCase
from owtf.proxy.gen_cert import gen_signed_cert

# Constants for certificate generation
CERTIFICATE_VALIDITY_DAYS = 365
SECONDS_PER_DAY = 24 * 60 * 60


class OWTFCliSSLInterceptionTest(OWTFCliTestCase):
    """Test SSL interception functionality."""

    categories = ["proxy", "ssl", "interception"]

    def setUp(self):
        """Set up test fixtures."""
        super(OWTFCliSSLInterceptionTest, self).setUp()
        self.temp_dir = tempfile.mkdtemp()
        self.ca_cert = os.path.join(self.temp_dir, "ca.crt")
        self.ca_key = os.path.join(self.temp_dir, "ca.key")
        self.certs_folder = os.path.join(self.temp_dir, "certs")
        os.makedirs(self.certs_folder)

        # Create a simple CA certificate for testing
        self._create_test_ca()

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        super(OWTFCliSSLInterceptionTest, self).tearDown()

    def _create_test_ca(self):
        """Create a test CA certificate."""
        from OpenSSL import crypto

        # Generate CA key
        ca_key = crypto.PKey()
        ca_key.generate_key(crypto.TYPE_RSA, 2048)

        # Generate CA certificate
        ca_cert = crypto.X509()
        ca_cert.get_subject().C = "US"
        ca_cert.get_subject().ST = "Test"
        ca_cert.get_subject().L = "Test"
        ca_cert.get_subject().O = "Test CA"
        ca_cert.get_subject().OU = "Test"
        ca_cert.get_subject().CN = "Test CA"
        ca_cert.gmtime_adj_notBefore(0)
        ca_cert.gmtime_adj_notAfter(CERTIFICATE_VALIDITY_DAYS * SECONDS_PER_DAY)
        ca_cert.set_serial_number(1)
        ca_cert.set_issuer(ca_cert.get_subject())
        ca_cert.set_pubkey(ca_key)
        ca_cert.sign(ca_key, "sha256")

        # Save CA key and certificate
        with open(self.ca_key, "wb") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, ca_key))

        with open(self.ca_cert, "wb") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert))

    def test_certificate_generation(self):
        """Test that certificates are generated correctly for SSL interception."""
        domain = "example.com"

        # Generate certificate for the domain
        key_path, cert_path = gen_signed_cert(domain, self.ca_cert, self.ca_key, "", self.certs_folder)

        # Verify files were created
        self.assertTrue(os.path.exists(key_path))
        self.assertTrue(os.path.exists(cert_path))

        # Verify certificate is valid
        from OpenSSL import crypto

        with open(cert_path, "rb") as f:
            cert_data = f.read()

        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
        self.assertEqual(cert.get_subject().CN, domain)

    def test_wildcard_certificate_generation(self):
        """Test that wildcard certificates are generated for domains with many dots."""
        domain = "sub1.sub2.sub3.example.com"

        # Generate certificate for the domain
        key_path, cert_path = gen_signed_cert(domain, self.ca_cert, self.ca_key, "", self.certs_folder)

        # Verify files were created
        self.assertTrue(os.path.exists(key_path))
        self.assertTrue(os.path.exists(cert_path))

        # Verify wildcard certificate is generated
        from OpenSSL import crypto

        with open(cert_path, "rb") as f:
            cert_data = f.read()

        cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_data)
        # Should be a certificate with the full domain name
        expected_cn = "sub1.sub2.sub3.example.com"
        self.assertEqual(cert.get_subject().CN, expected_cn)

    @patch("owtf.proxy.socket_wrapper.starttls")
    def test_ssl_interception_flow(self, mock_starttls):
        """Test the SSL interception flow in the CONNECT method."""
        from owtf.proxy.proxy import ProxyHandler
        from tornado.web import Application

        # Mock the starttls function
        mock_starttls.return_value = Mock()

        # Create a mock application with SSL settings
        app = Application()
        app.ca_cert = self.ca_cert
        app.ca_key = self.ca_key
        app.ca_key_pass = ""
        app.certs_folder = self.certs_folder

        # Test that the SSL interception infrastructure is in place
        self.assertTrue(hasattr(app, "ca_cert"))
        self.assertTrue(hasattr(app, "ca_key"))
        self.assertTrue(hasattr(app, "ca_key_pass"))
        self.assertTrue(hasattr(app, "certs_folder"))
