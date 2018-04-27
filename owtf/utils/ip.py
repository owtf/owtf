"""
owtf.utils.ip
~~~~~~~~~~~~~

"""
import logging
import socket

from ipaddr import IPAddress
from owtf.config import config_handler
from owtf.lib.exceptions import UnresolvableTargetException


def get_ips_from_hostname(hostname):
    """Get IPs from the hostname

    :param hostname: Target hostname
    :type hostname: `str`
    :return: IP addresses of the target hostname as a list
    :rtype: `list`
    """
    ip = ""
    # IP validation based on @marcwickenden's pull request, thanks!
    for sck in [socket.AF_INET, socket.AF_INET6]:
        try:
            socket.inet_pton(sck, hostname)
            ip = hostname
            break
        except socket.error:
            continue
    if not ip:
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            raise UnresolvableTargetException("Unable to resolve: '{!s}'".format(hostname))

    ipchunks = ip.strip().split("\n")
    return ipchunks


def get_ip_from_hostname(hostname):
    """Get IP from the hostname

    :param hostname: Target hostname
    :type hostname: `str`
    :return: IP address of the target hostname
    :rtype: `str`
    """
    ip = ""
    # IP validation based on @marcwickenden's pull request, thanks!
    for sck in [socket.AF_INET, socket.AF_INET6]:
        try:
            socket.inet_pton(sck, hostname)
            ip = hostname
            break
        except socket.error:
            continue
    if not ip:
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            raise UnresolvableTargetException("Unable to resolve: '{!s}'".format(hostname))

    ipchunks = ip.strip().split("\n")
    alternative_ips = []
    if len(ipchunks) > 1:
        ip = ipchunks[0]
        logging.info("%s has several IP addresses: (%s).Choosing first: %s", hostname, "".join(ipchunks)[0:-3], ip)
        alternative_ips = ipchunks[1:]
    config_handler.set_val("alternative_ips", alternative_ips)
    ip = ip.strip()
    config_handler.set_val("INTERNAL_IP", is_internal_ip(ip))
    logging.info("The IP address for %s is: '%s'", hostname, ip)
    return ip


def hostname_is_ip(hostname, ip):
    """Test if the hostname is an IP.

    :param str hostname: the hostname of the target.
    :param str ip: the IP (v4 or v6) of the target.

    :return: ``True`` if the hostname is an IP, ``False`` otherwise.
    :rtype: :class:`bool`

    """
    return hostname == ip


def is_internal_ip(ip):
    """Parses the input IP and checks if it is a private IP

    :param str ip: IP address

    :return: True if it is a private IP, otherwise False
    :rtype: `bool`
    """
    parsed_ip = IPAddress(ip)
    return parsed_ip.is_private
