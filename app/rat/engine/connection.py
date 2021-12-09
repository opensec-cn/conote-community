import uuid
import time
import datetime
import typing
import selectors
import threading
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .globals import sel, logger
channel_layer = get_channel_layer()


if typing.TYPE_CHECKING:
    from .listener import Listener


def get_micro_second():
    return time.time() * 1000


class Connection(object):
    def __init__(self, listener: 'Listener'):
        self.serid = str(uuid.uuid4())
        self.listener = listener
        self.sock, self.address_port = listener.sock.accept()
        self.locker = threading.Lock()

        self.sock.setblocking(False)
        sel.register(self, selectors.EVENT_READ, self)

        self._output = []
        self.created_time = datetime.datetime.now()

    def fileno(self):
        return self.sock.fileno()

    def handler(self):
        data = self.sock.recv(1024)
        if data:
            self._output.append(data)
            async_to_sync(channel_layer.group_send)(
                "rat_%s" % self.serid,
                {
                    "type": "send_output",
                    "output": self.output
                }
            )
        else:
            self.listener.remove_connection(self)

            logger.info('closing %s:%d', self.address, self.port)
            self.close()

    def close(self):
        sel.unregister(self)
        self.sock.close()

        self._output.clear()

    def send(self, data):
        with self.locker:
            self.sock.send(data)

    def is_dup(self):
        """
        同一IP地址的连接，只允许3个

        :return:
        """

        i = 3
        for connection in self.listener.connections:
            if connection.address == self.address:
                i -= 1

            if i <= 0:
                return True

        return False

    @property
    def address(self):
        return self.address_port[0]

    @property
    def port(self):
        return self.address_port[1]

    @property
    def output(self):
        return b''.join(self._output).decode(encoding='utf-8', errors='ignore')
