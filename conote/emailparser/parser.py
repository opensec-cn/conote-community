import functools
import email
import logging
import base64
import re
import datetime
from uuid import uuid4
from typing import Mapping
from email.message import EmailMessage
from email.header import decode_header
from email.errors import HeaderParseError
from unicodedata import normalize


logger = logging.getLogger('conote')


def sanitize(func):
    """ NFC is the normalization form recommended by W3C. """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return normalize('NFC', func(*args, **kwargs))
    return wrapper


@sanitize
def ported_string(raw_data, encoding='utf-8', errors='ignore'):
    if isinstance(raw_data, str):
        return raw_data.strip()

    try:
        return raw_data.decode(encoding, errors).strip()
    except (LookupError, UnicodeDecodeError):
        return raw_data.decode('utf-8', errors).strip()


def decode_header_part(header):
    output = ''
    try:
        for d, c in decode_header(header):
            c = c if c else 'utf-8'
            output += ported_string(d, c, 'ignore')

    # Header parsing failed, when header has charset Shift_JIS
    except (HeaderParseError, UnicodeError):
        logger.error("Failed decoding header part: {}".format(header))
        output += header

    return output


def get_cid(cid):
    if not cid:
        return str(uuid4())

    return re.sub(r'<([\w\.\-]+)>', r'\1', cid)


def convert_mail_date(date):
    d = email.utils.parsedate_tz(date)
    t = email.utils.mktime_tz(d)
    return datetime.datetime.utcfromtimestamp(t)


class Attachment(object):
    def __init__(self, filename, content_type, binary: bytes, origin_obj: EmailMessage):
        self.filename = filename
        self.content_type = content_type
        self.binary = binary
        self.origin_obj = origin_obj

    def get_data_uri(self):
        return 'data:{self.content_type};base64,{data}'.format(
            self=self,
            data=ported_string(base64.b64encode(self.binary))
        )


class MailParser(object):
    def __init__(self, message: EmailMessage=None):
        self.message = message
        self._attachments = {}
        self._body = ''

        self.parse()

    def parse(self):
        body = self.message.get_body(preferencelist=('html', 'plain'))
        charset = body.get_content_charset('utf-8')
        self._body = ported_string(body.get_payload(decode=True), encoding=charset)

        for p in self.message.iter_attachments():
            filename = p.get_filename()
            mail_content_type = p.get_content_type()
            binary = p.get_payload(decode=True)

            if filename:
                attachment = Attachment(
                    filename=filename,
                    content_type=mail_content_type,
                    binary=binary,
                    origin_obj=p
                )
                self._attachments[get_cid(p['content-id'])] = attachment

        return self

    def get_header(self, name, failobj=''):
        value = self.message.get(name, failobj)
        return decode_header_part(value)

    @property
    def subject(self):
        return self.get_header('subject')

    @property
    def attachments(self) -> Mapping[str, Attachment]:
        return self._attachments

    @property
    def body(self) -> str:
        return self._body

    @property
    def date(self):
        date = self.get_header('date')
        conv = None

        try:
            conv = convert_mail_date(date)
        finally:
            return conv

    @classmethod
    def from_file_obj(cls, fp):
        message = email.message_from_file(fp, EmailMessage)
        return cls(message)

    @classmethod
    def from_file(cls, filename):
        with open(filename, 'rb') as f:
            message = email.message_from_binary_file(f, EmailMessage)

        return cls(message)

    @classmethod
    def from_string(cls, s):
        message = email.message_from_string(s, EmailMessage)
        return cls(message)

    @classmethod
    def from_bytes(cls, b):
        message = email.message_from_bytes(b, EmailMessage)
        return cls(message)
