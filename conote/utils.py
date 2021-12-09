import time
import functools

from django.conf import settings
from urllib.parse import urlparse, parse_qsl, urlunparse, urlencode, urljoin
from dnslib.dns import DNSRecord, DNSHeader, DNSQuestion, QTYPE
from .const import DNS_SERVER


def get_remote_addr(request):
    if settings.IP_HEADER:
        return request.META[settings.IP_HEADER]
    else:
        return request.META['REMOTE_ADDR']


def get_domain_key(hostname, basedomain=settings.O_SERVER_DOMAIN):
    pos = hostname.find(basedomain)
    if pos < 0:
        return None

    domain_key = hostname[:pos - 1]
    return domain_key.split(".").pop()


def from10_to62(number):
    ret = ''
    table = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    to = len(table)
    while True:
        ret = table[number % to] + ret
        number = number // to
        if number <= 0:
            break
    return ret


def from62_to10(number):
    table = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ret = 0
    if number == "":
        return ret

    for ch in number:
        k = table.find(ch)
        if k >= 0:
           ret = ret * 62 + k
    return ret


def build_url(base_url, **kwargs):
    url_parts = list(urlparse(base_url))
    query = dict(parse_qsl(url_parts[4], keep_blank_values=True))
    query.update(kwargs)
    url_parts[4] = urlencode(query)
    return urlunparse(url_parts)


def query_dns(domain, qtype='A'):
    q = DNSRecord(q=DNSQuestion(domain, getattr(QTYPE, qtype)))
    a_pkt = q.send(*DNS_SERVER, tcp=True, timeout=5)
    a = DNSRecord.parse(a_pkt)
    return a.short()
