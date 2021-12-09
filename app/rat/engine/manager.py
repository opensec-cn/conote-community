import time
import selectors
import threading

from .listener import Listener
from .globals import sel, logger, ListenContainer


class SocketManager(object):
    def __init__(self, container: ListenContainer=None):
        if container is None:
            container = ListenContainer()

        self.container = container

    def serve_forever(self):
        keep_alive_activity = time.time()
        while True:
            if not len(self.container):
                time.sleep(0.1)
                continue

            try:
                events = sel.select()
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        objecter = key.data
                        objecter.handler()
                #
                # if time.time() - keep_alive_activity > 30.0:
                #     for connection in self.container.walk():
                #         connection.send(b'\x20')
            except OSError as e:
                logger.exception(e)
                time.sleep(1)
                continue

    def add_listener(self, id):
        if id not in self.container:
            self.container[id] = Listener(id)
            logger.info('bind 0.0.0.0 %d', self.container[id].port)

        return self.container[id]

    def get_listener(self, id) -> Listener:
        return self.container.get(id, None)

    def get_connection(self, id, serid):
        connection = None
        listener = self.get_listener(id)

        if listener:
            connection = listener.get_connection(serid, None)

        return connection

    def close(self, id=None):
        if id:
            listener = self.get_listener(id)
            if listener:
                listener.close()
            self.container.pop(id)
        else:
            for listener in self.container.values():
                listener.close()
            self.container.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
