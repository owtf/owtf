import shutil
import tempfile
from pathlib import Path

import pytest
from owtf.proxy.gen_cert import gen_signed_cert, CertConfig, generate_signed_cert

# Fixture: build a temporary CA
@pytest.fixture(scope="module")
def temp_ca(tmp_path_factory):
    d = tmp_path_factory.mktemp("ca")
    ca_key = d / "ca.key.pem"
    ca_crt = d / "ca.crt.pem"
    # generate CA key and cert
    import subprocess

    subprocess.run(["openssl", "genrsa", "-out", str(ca_key), "2048"], check=True)
    subprocess.run(
        [
            "openssl",
            "req",
            "-x509",
            "-new",
            "-nodes",
            "-key",
            str(ca_key),
            "-sha256",
            "-days",
            "365",
            "-out",
            str(ca_crt),
            "-subj",
            "/C=US/ST=CA/L=SF/O=TestCA/OU=Dev/CN=Test CA",
        ],
        check=True,
    )
    return str(ca_crt), str(ca_key)


def test_generate_signed_cert_creates_files(tmp_path, temp_ca):
    ca_crt, ca_key = temp_ca
    out = tmp_path / "certs"
    config = CertConfig(
        ca_cert_path=Path(ca_crt),
        ca_key_path=Path(ca_key),
        ca_key_password=None,
        certs_folder=out,
    )
    key_path, cert_path = generate_signed_cert("foo.test", config)

    # Assert files exist
    assert key_path.exists()
    assert cert_path.exists()

    # Load and inspect via cryptography
    from cryptography import x509

    cert = x509.load_pem_x509_certificate(cert_path.read_bytes())
    # CN matches
    assert cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value == "foo.test"
    # Validity window
    assert cert.not_valid_before < cert.not_valid_after


def test_wrapper_returns_strings(tmp_path, temp_ca):
    ca_crt, ca_key = temp_ca
    key, crt = gen_signed_cert("bar.example", ca_crt, ca_key, "", str(tmp_path))
    assert isinstance(key, str)
    assert isinstance(crt, str)
    assert Path(key).exists()
    assert Path(crt).exists()
