import functools
import asyncio
import logging
import threading
import uuid
from typing import Set
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.template.defaultfilters import date
from django.core.management.base import BaseCommand
from asgiref.sync import sync_to_async
from app.disposable_email import models
from flanker.addresslib import address as address_parser
from conote.emailparser.parser import MailParser
from aiosmtpd.smtp import Envelope, Session, SMTP


User = get_user_model()
logger = logging.getLogger('conote')
loop = asyncio.get_event_loop()


def save_file(data: bytes):
    date_dir = date(timezone.localtime(timezone.now()), 'Y/m/d')
    filename = Path(settings.MEDIA_ROOT) / 'email' / date_dir / ('%s.eml' % uuid.uuid4())

    filename.parent.mkdir(0o755, parents=True, exist_ok=True)
    filename.write_bytes(data)
    return str(filename.relative_to(settings.MEDIA_ROOT))


class SMTPServerHandler(object):
    async def handle_RCPT(self, session, envelope, address, rcpt_options):
        logger.info('Recieve a email from {}'.format(address))

        envelope.rcpt_tos.append(address)
        return '250 OK'

    async def handle_DATA(self, session: Session, envelope: Envelope):
        if not envelope.mail_from:
            return '550 mail from not found'

        to_list = set()
        mail_from = address_parser.parse(envelope.mail_from)
        if not mail_from:
            return '550 mail from not found'

        try:
            parser = MailParser.from_bytes(envelope.original_content)
            to_list |= set(address_parser.parse(email).address for email in envelope.rcpt_tos)

            to = parser.get_header('to', '')
            to_list |= set(email.address for email in address_parser.parse_list(to))

            cc = parser.get_header('cc', '')
            to_list |= set(email.address for email in address_parser.parse_list(cc))

        except Exception as e:
            logger.exception(e)
            return '550 Server error'

        def _save_email_to_model():
            save_path = save_file(envelope.original_content)
            for email in to_list:
                try:
                    box = models.MailBox.objects.get(email=email)
                except models.MailBox.DoesNotExist:
                    continue

                models.Envelope.objects.create(
                    subject=parser.subject,
                    mail_from=mail_from.address,
                    path=save_path,
                    user=box.user,
                    send_time=parser.date or timezone.now()
                )

        if to_list:
            await sync_to_async(_save_email_to_model, thread_sensitive=True)()

        return '250 Message accepted for delivery'


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--port', type=int, default=25)
        parser.add_argument('--address', type=str, default='0.0.0.0')

    def handle(self, *args, **options):
        logger.info("start email server")
        wrapper = functools.partial(SMTP, SMTPServerHandler)

        try:
            s = loop.create_server(wrapper, host=options['address'], port=options['port'])
            server_loop = loop.run_until_complete(s)
        except RuntimeError:  # pragma: nocover
            raise

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        server_loop.close()
        logger.info("Completed asyncio loop")
        loop.run_until_complete(server_loop.wait_closed())
        loop.close()
