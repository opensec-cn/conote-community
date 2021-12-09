from defusedxml.xmlrpc import monkey_patch, unmonkey_patch
monkey_patch()

import time
import logging
import threading
from pathlib import Path
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.crypto import get_random_string

from app.rat.engine import SocketManager


User = get_user_model()
logger = logging.getLogger('conote')


class Controller(object):
    def __init__(self, manager: SocketManager):
        self.manager = manager

    def get_listener(self, user_id):
        listener = self.manager.get_listener(user_id)
        return dict(
            port=listener.port,
            connections=[dict(
                serid=connection.serid,
                address=connection.address,
                port=connection.port,
                created_time=connection.created_time
            ) for connection in listener.connections]
        ) if listener is not None else None

    def create_listener(self, user_id):
        listener = self.manager.add_listener(user_id)
        return listener.port

    def stop_listener(self, user_id):
        self.manager.close(user_id)

        return True

    def get_connection(self, user_id, serid):
        connection = self.manager.get_connection(user_id, serid)
        if connection is None:
            return None
        else:
            return dict(
                    serid=connection.serid,
                    address=connection.address,
                    port=connection.port,
                    output=connection.output,
                    created_time=connection.created_time
                )

    def execute(self, user_id, serid, command: bytes):
        connection = self.manager.get_connection(user_id, serid)
        if connection is not None:
            connection.send(b"%s\n" % command.strip())
        else:
            return b''


class Command(BaseCommand):
    help = 'Start the RAT main process'

    def start_daemon_server(self):
        logger.info('start daemon server')
        t = threading.Thread(target=self.manager.serve_forever)
        t.daemon = True
        t.start()

    def handle(self, *args, **options):
        with SimpleXMLRPCServer(addr=(settings.RPC_SETTING['HOST'], settings.RPC_SETTING['PORT']), use_builtin_types=True, allow_none=True) as self.server, \
                SocketManager() as self.manager:
            self.start_daemon_server()

            self.server.register_introspection_functions()
            self.server.register_instance(Controller(self.manager))
            self.server.serve_forever()
