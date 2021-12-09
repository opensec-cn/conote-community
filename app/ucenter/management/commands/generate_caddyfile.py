import sys
import os
import logging
import subprocess
import shutil

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings


User = get_user_model()
logger = logging.getLogger('conote')


def reload_caddy():
    logger.info('reload caddy...')
    result = subprocess.run(['systemctl', 'restart', 'caddy'])
    return result.returncode == 0


def write_configuration(domain_list):
    config = r'''%s {
    import ../conote
}
''' % domain_list
    filename = os.path.join('/etc/caddy', 'vhosts', 'main.conf')
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(config)
    shutil.chown(filename, 'www-data', 'www-data')


class Command(BaseCommand):
    def handle(self, *args, **options):
        domain_list = []

        try:
            logger.info('recreate caddyfile configuration...')
            for user in User.objects.filter(is_active=True).all():
                domain_list.append('http://{domain}.{base}'.format(domain=user.domain, base=settings.O_SERVER_DOMAIN))

            write_configuration(', '.join(domain_list))
            reload_caddy()
        except Exception as e:
            logger.exception(e)
