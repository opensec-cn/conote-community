import os
import logging
import copy
import socketserver
import ipaddress
from dnslib import RR, QTYPE, RCODE, ZoneParser, DNSLabel, A, CNAME
from dnslib.server import DNSServer, DNSHandler, BaseResolver, DNSLogger
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.conf import settings
from django.contrib.auth import get_user_model
from conote.utils import get_domain_key
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.utils import timezone
from app.log import models


User = get_user_model()
log = logging.getLogger('conote')


def is_ipaddress(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except:
        return False


class MysqlLogger(object):
    def log_data(self, dnsobj):
        pass

    def log_error(self, handler, e):
        pass

    def log_pass(self, *args):
        pass

    def log_prefix(self, handler):
        pass

    def log_recv(self, handler, data):
        pass

    def log_reply(self, handler, reply):
        pass

    @transaction.non_atomic_requests
    def log_request(self, handler, request):
        domain = str(request.q.qname)
        domain_key = get_domain_key(domain)
        try:
            if domain_key:
                user = User.objects.get(domain=domain_key)
                models.DNSLog.objects.create(
                    user=user,
                    hostname=domain,
                    dns_type=QTYPE[request.q.qtype],
                    ip_addr=handler.client_address[0]
                )
        except (User.DoesNotExist, ):
            pass

        log.info('receive request %r from %r' % (domain, handler.client_address[0]))

    def log_send(self, handler, data):
        pass

    def log_truncated(self, handler, reply):
        pass


class ZoneResolver(BaseResolver):
    """
        Simple fixed zone file resolver.
    """

    def __init__(self, zone, glob=False):
        """
            Initialise resolver from zone file.
            Stores RRs as a list of (label,type,rr) tuples
            If 'glob' is True use glob match against zone file
        """
        self.zone = [(rr.rname, QTYPE[rr.rtype], rr) for rr in RR.fromZone(zone)]
        self.glob = glob
        self.eq = 'matchGlob' if glob else '__eq__'

    def return_rebinding_record(self, qname, reply):
        try:
            domain_key = get_domain_key(str(qname), settings.O_REBIND_DOMAIN)
            user = User.objects.get(domain=domain_key)
            if timezone.now().timestamp() - user.dnsrecord.last_visited.timestamp() > models.DNSRecord.limit_interval:
                user.dnsrecord.click = 0

            ip_address = user.dnsrecord.ips[user.dnsrecord.click]
            user.dnsrecord.click = (user.dnsrecord.click + 1) % len(user.dnsrecord.ips)
            user.dnsrecord.last_visited = timezone.now()
            user.dnsrecord.save()

            if is_ipaddress(ip_address):
                reply.add_answer(*RR.fromZone("{} 0 IN A {}".format(str(qname), ip_address)))
            else:
                rdata = CNAME(ip_address)
                reply.add_answer(RR(rname=qname, rtype=5, rclass=1, ttl=300, rdata=rdata))

            return reply
        except:
            reply.add_answer(*RR.fromZone("{} 0 IN A {}".format(str(qname), settings.O_SERVER_IP)))
            return reply

    def resolve(self, request, handler):
        """
            Respond to DNS request - parameters are request packet & handler.
            Method is expected to return DNS response
        """
        reply = request.reply()
        qname = request.q.qname
        qtype = QTYPE[request.q.qtype]
        if getattr(qname, self.eq)(DNSLabel('*.{}.'.format(settings.O_REBIND_DOMAIN))) and \
                        qtype in ['A', 'AAAA', 'ANY']:
            return self.return_rebinding_record(qname, reply)

        for name, rtype, rr in self.zone:
            # Check if label & type match
            if getattr(qname, self.eq)(name) and (
                    qtype == rtype or qtype == 'ANY' or rtype == 'CNAME'):
                # If we have a glob match fix reply label
                if self.glob:
                    a = copy.copy(rr)
                    a.rname = qname
                    reply.add_answer(a)
                else:
                    reply.add_answer(rr)
                # Check for A/AAAA records associated with reply and
                # add in additional section
                if rtype in ['CNAME', 'NS', 'MX', 'PTR']:
                    for a_name, a_rtype, a_rr in self.zone:
                        if a_name == rr.rdata.label and a_rtype in ['A', 'AAAA']:
                            reply.add_ar(a_rr)
        if not reply.rr:
            reply.header.rcode = RCODE.NXDOMAIN
        return reply


class ClosedUDPServer(socketserver.UDPServer):
    allow_reuse_address = True
    timeout = 5

    def close_request(self, request):
        connection.close()


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--port', type=int, default=53)
        parser.add_argument('--address', type=str, default='0.0.0.0')

    def handle(self, *args, **options):
        zone = '''
*.{dnsdomain}.      IN      NS      {ns1domain}.
*.{dnsdomain}.      IN      NS      {ns2domain}.
*.{dnsdomain}.      IN      A       {serverip}
{dnsdomain}.        IN      A       {serverip}
{addition_zone}'''.format(
            dnsdomain=settings.O_SERVER_DOMAIN, ns1domain=settings.O_NS1_DOMAIN,
            ns2domain=settings.O_NS2_DOMAIN, serverip=settings.O_SERVER_IP,
            addition_zone=settings.O_ADDITION_ZONE)
        log.info(zone)
        resolver = ZoneResolver(zone, True)
        logger = MysqlLogger()
        print("Starting Zone Resolver (%s:%d) [%s]" % ("*", options['port'], "UDP"))

        udp_server = DNSServer(resolver,
                               port=options['port'],
                               address=options['address'],
                               logger=logger,
                               server=ClosedUDPServer
                               )
        udp_server.start()
