import sys
import logging
import selectors

from collections import UserDict
from django.utils.crypto import get_random_string


class ListenContainer(UserDict):
    def walk(self):
        for id, listener in self.items():
            for connection in listener.connections:
                yield connection

    def close(self):
        for listener in self.values():
            listener.close()

        self.clear()


port_range = range(42333, 42666)
sel = selectors.DefaultSelector()

# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logger = logging.getLogger('conote')
