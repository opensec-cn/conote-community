import sys
import logging
import subprocess
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings


User = get_user_model()
logger = logging.getLogger('conote')


def reload_nginx():
    logger.info('Nginx is reload.')
    result = subprocess.run(['nginx', '-s', 'reload'])
    return result.returncode == 0


class Command(BaseCommand):
    def handle(self, *args, **options):
        server = SimpleXMLRPCServer(settings.CTRL_SERVER_ADDRESS)
        server.register_introspection_functions()

        server.register_function(reload_nginx)

        try:
            logger.info('Ctrl server \'http://%s:%d\' is running...' % settings.CTRL_SERVER_ADDRESS)
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, exiting.")
            server.server_close()
            sys.exit(0)
