import uuid
import random
import socket
import selectors

from collections import UserDict
from tenacity import retry, stop_after_attempt, retry_if_exception_type

from .globals import sel, logger
from .connection import Connection


port_range = range(42333, 42666)


@retry(stop=stop_after_attempt(10), retry=retry_if_exception_type(OSError))
def bind_a_free_port(sock):
    port = random.choice(port_range)
    sock.bind(('0.0.0.0', port))

    return port


class Listener(object):
    def __init__(self, id):
        self.id = id

        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.port = bind_a_free_port(self.sock)

        self.sock.listen(5)
        self.sock.setblocking(False)
        sel.register(self, selectors.EVENT_READ, self)

        self.connections = []

    def handler(self):
        connection = Connection(self)
        if connection.is_dup():
            connection.close()
        else:
            logger.info('connect from %s', connection.address)
            self.connections.append(connection)

    def fileno(self):
        return self.sock.fileno()

    def close(self):
        for connection in self.connections:
            connection.close()

        self.connections.clear()

        sel.unregister(self)
        self.sock.close()
        logger.info('unbind 0.0.0.0 %d', self.port)

    def remove_connection(self, target):
        for i, connection in enumerate(self.connections):
            if connection.fileno() == target.fileno():
                self.connections.pop(i)

    def get_connection(self, serid, fallback=None):
        for connection in self.connections:
            if serid == connection.serid:
                return connection

        return fallback
