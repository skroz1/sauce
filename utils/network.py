#!/usr/bin/env python3

import requests
import ipaddress
import socket

def get_public_ip():
    """
    Get the public IP address of the machine.
    :return: Public IP address as a string.
    :raises: RuntimeError if the IP cannot be obtained.
    """
    try:
        response = requests.get("http://httpbin.org/ip")
        response.raise_for_status()
        return response.json()["origin"]
    except Exception as e:
        raise RuntimeError(f"Error obtaining public IP: {e}")

def is_private_ip(ip):
    """
    Check if the IP address is a private address.
    :param ip: IP address as a string.
    :return: True if IP is private, False otherwise.
    """
    return ipaddress.ip_address(ip).is_private

def validate_hostname(hostname):
    """
    Validate and potentially modify the hostname.
    :param hostname: The hostname as a string.
    :return: A tuple of the validated hostname and a boolean indicating if the domain was appended.
    :raises: RuntimeError if system domain cannot be obtained.
    """
    if '.' not in hostname:
        try:
            domain = socket.getfqdn().split('.', 1)[1]
            return f"{hostname}.{domain}", True
        except IndexError as e:
            raise RuntimeError(f"Error obtaining system domain: {e}")
    return hostname, False
