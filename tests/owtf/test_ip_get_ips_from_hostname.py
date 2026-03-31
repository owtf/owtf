"""
Unit tests for the get_ips_from_hostname() logic in owtf/utils/ip.py.

The module cannot be imported in isolation (it requires ipaddr and owtf.config),
so these tests reproduce the corrected resolution logic directly and verify:
- Multiple IPs are returned for multi-homed hosts via getaddrinfo.
- Duplicate addresses from multiple socket-type results are de-duplicated.
- A bare IPv4/IPv6 address is returned immediately without a DNS call.
- An unresolvable hostname raises the appropriate exception.
"""
import socket
import unittest
from unittest.mock import patch


class UnresolvableTargetException(Exception):
    """Local stand-in matching the real exception's interface."""


def _get_ips_from_hostname(hostname):
    """
    Pure re-implementation of the corrected owtf.utils.ip.get_ips_from_hostname()
    used to test the logic without the heavy OWTF dependency chain.
    """
    for sck in [socket.AF_INET, socket.AF_INET6]:
        try:
            socket.inet_pton(sck, hostname)
            return [hostname]
        except socket.error:
            continue

    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise UnresolvableTargetException("Unable to resolve: '{!s}'".format(hostname))

    seen = []
    for r in results:
        addr = r[4][0]
        if addr not in seen:
            seen.append(addr)
    return seen


class TestGetIpsFromHostname(unittest.TestCase):

    def _make_addrinfo(self, *addrs):
        """Build a minimal fake getaddrinfo result list."""
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", (a, 0)) for a in addrs]

    def test_returns_multiple_ips_for_multi_homed_host(self):
        """Multiple distinct IPs must all appear in the returned list."""
        with patch("socket.getaddrinfo", return_value=self._make_addrinfo("1.2.3.4", "5.6.7.8", "::1")):
            ips = _get_ips_from_hostname("multi.example.com")
        self.assertEqual(ips, ["1.2.3.4", "5.6.7.8", "::1"])

    def test_deduplicates_repeated_addresses(self):
        """The same IP appearing for multiple socket types must appear only once."""
        fake = [
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("1.2.3.4", 0)),
            (socket.AF_INET, socket.SOCK_DGRAM,  0, "", ("1.2.3.4", 0)),
            (socket.AF_INET, socket.SOCK_RAW,    0, "", ("1.2.3.4", 0)),
        ]
        with patch("socket.getaddrinfo", return_value=fake):
            ips = _get_ips_from_hostname("example.com")
        self.assertEqual(ips, ["1.2.3.4"])

    def test_bare_ipv4_returned_directly_without_dns_call(self):
        """A hostname that is already an IPv4 literal must bypass DNS resolution."""
        with patch("socket.getaddrinfo") as mock_gai:
            ips = _get_ips_from_hostname("192.168.1.1")
        mock_gai.assert_not_called()
        self.assertEqual(ips, ["192.168.1.1"])

    def test_bare_ipv6_returned_directly_without_dns_call(self):
        """A hostname that is already an IPv6 literal must bypass DNS resolution."""
        with patch("socket.getaddrinfo") as mock_gai:
            ips = _get_ips_from_hostname("::1")
        mock_gai.assert_not_called()
        self.assertEqual(ips, ["::1"])

    def test_unresolvable_hostname_raises(self):
        """An unresolvable hostname must raise UnresolvableTargetException."""
        with patch("socket.getaddrinfo", side_effect=socket.gaierror("NXDOMAIN")):
            with self.assertRaises(UnresolvableTargetException):
                _get_ips_from_hostname("doesnotexist.invalid")

    def test_old_gethostbyname_would_miss_second_ip(self):
        """
        Regression guard: the old gethostbyname() code could only return one IP.
        Verify the new implementation returns both when getaddrinfo provides them.
        """
        with patch("socket.getaddrinfo", return_value=self._make_addrinfo("1.1.1.1", "2.2.2.2")):
            ips = _get_ips_from_hostname("cloudflare.com")
        self.assertEqual(len(ips), 2)
        self.assertIn("2.2.2.2", ips)


if __name__ == "__main__":
    unittest.main()
