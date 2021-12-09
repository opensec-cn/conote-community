import logging
import docker
import docker.types
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings

User = get_user_model()
logger = logging.getLogger('conote')
client = docker.from_env()


class Command(BaseCommand):
    help = 'Control the sandbox docker containers'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['start', 'stop', 'restart'], type=str, help='command action: start/stop/restart')

    def handle(self, *args, **options):
        if hasattr(self, options['action']):
            getattr(self, options['action'])(*args, **options)

    def start(self, *args, **options):
        root = Path(settings.BASE_DIR)
        sandbox_root = Path(settings.SANDBOX_ROOT)
        if not sandbox_root.exists():
            sandbox_root.mkdir(0o755, True, True)

        try:
            for key, config in settings.DOCKER_CONFIG.items():
                ipam_pool = docker.types.IPAMPool(
                    subnet=config['subnet'],
                    gateway=config['gateway']
                )
                ipam = docker.types.IPAMConfig(pool_configs=[ipam_pool])
                network = client.networks.create(
                    name=config['network_name'],
                    driver='bridge',
                    internal=True,
                    ipam=ipam
                )
                logger.info('create network %r success.' % config['network_name'])

                networking_config = client.api.create_networking_config({
                    config['network_name']: client.api.create_endpoint_config(
                        ipv4_address=config['ip']
                    )
                })
                volume = {
                    str(sandbox_root): {
                        'bind': str(sandbox_root),
                        'mode': 'ro'
                    },
                    str(root / 'app' / 'sandbox' / 'php' / 'conote-php.ini'): {
                        'bind': '/usr/local/etc/php/conf.d/conote-php.ini',
                        'mode': 'ro'
                    }
                }
                if config.get('tmp', None):
                    volume[config['tmp']] = {
                        'bind': '/tmp',
                        'mode': 'rw'
                    }

                host_config = client.api.create_host_config(
                    binds=volume,
                    mem_limit='32m',
                    restart_policy={"Name": "on-failure", "MaximumRetryCount": 3}
                )
                client.api.create_container(
                    image=config['image'],
                    name=config['container_name'],
                    detach=True,
                    host_config=host_config,
                    volumes=[v['bind'] for k, v in volume.items()],
                    networking_config=networking_config,
                    runtime='runsc'
                )

                container = client.containers.get(config['container_name'])
                container.start()

                container.exec_run(["sh", "-c", "echo -e '[www]\n\nlisten.allowed_clients = {}' > "
                                   "/usr/local/etc/php-fpm.d/sandbox.conf".format(config['gateway'])])
                container.restart()
                logger.info('create container %r success.' % config['container_name'])
        except Exception as e:
            logger.exception(e)

    def stop(self, *args, **options):
        try:
            for key, config in settings.DOCKER_CONFIG.items():
                container = client.containers.get(config['container_name'])
                container.stop()
                container.remove()

                network = client.networks.get(config['network_name'])
                network.remove()

                logger.info('%s container is stopped.' % config['container_name'])
        except Exception as e:
            logger.exception(e)

    def restart(self, *args, **options):
        self.stop(*args, **options)
        self.start(*args, **options)
