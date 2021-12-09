from defusedxml.xmlrpc import monkey_patch, unmonkey_patch
monkey_patch()

import json
import logging
import xmlrpc.client
import channels.layers
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.conf import settings

logger = logging.getLogger('conote')
RPC_SERVER = f"http://{settings.RPC_SETTING['HOST']}:{settings.RPC_SETTING['PORT']}"


class RatConsumer(WebsocketConsumer):
    def connect(self):
        logger.info('incoming a connect')

        self.user = self.scope["user"]
        self.serid = self.scope['url_route']['kwargs']['serid']

        if not self.user.is_authenticated:
            return self.close()

        with xmlrpc.client.ServerProxy(RPC_SERVER, use_builtin_types=True, allow_none=True) as self.client:
            connection = self.client.get_connection(self.user.id, self.serid)

        if connection:
            self.serid_group_name = 'rat_%s' % self.serid
            async_to_sync(self.channel_layer.group_add)(
                self.serid_group_name,
                self.channel_name
            )

            self.accept()
            self.send(text_data=json.dumps({
                'output': connection['output']
            }))
        else:
            self.close()

    def disconnect(self, close_code):
        logger.info('closed a connect')
        async_to_sync(self.channel_layer.group_discard)(
            self.serid_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, byte_data=None):
        logger.info('receive message %r', text_data)
        data = json.loads(text_data)
        command = data['command']

        self.client.execute(self.user.id, self.serid, command.encode())

    def send_output(self, event):
        output = event['output']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'output': output
        }))
