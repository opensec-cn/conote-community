import re
import logging
import django.http.response
from pathlib import Path
from urllib.parse import parse_qsl
from requests.structures import CaseInsensitiveDict

from django.conf import settings
from django.http import HttpResponse, Http404, FileResponse, HttpResponsePermanentRedirect
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render
from django.utils.encoding import force_bytes, force_text
from django.utils import timezone

from conote.utils import get_remote_addr, get_domain_key, build_url, from62_to10
from app.log import models
from app.xss import models as xss_models
from app.sandbox import models as sandbox_models
from conote.ipdata.parser import IPData
from .tasks import send_notification
from app.sandbox.fastcgi.client import FastCGIClient


User = get_user_model()
log = logging.getLogger('django')


class LogRequestMixin(object):
    def get_headers(self, request):
        headers = {}
        for k, v in request.META.items():
            if k.startswith('HTTP_') and k[5:]:
                headers[k[5:]] = v

        if 'CONTENT_TYPE' in request.META and request.META['CONTENT_TYPE']:
            headers['CONTENT_TYPE'] = request.META['CONTENT_TYPE']

        if 'CONTENT_LENGTH' in request.META and request.META['CONTENT_LENGTH']:
            headers['CONTENT_LENGTH'] = request.META['CONTENT_LENGTH']

        return headers

    def send_headers(self, response, headers):
        try:
            for key, val in headers:
                response[key] = val
        except:
            pass

    def ip_to_location(self, ip_address):
        try:
            location = IPData().find(ip_address)
            return '/'.join(location.strip().split())
        except:
            return ''


class SandboxModdleware(LogRequestMixin):
    FILENAME_PATTERN = re.compile(r'^/([0-9a-f\-]{36})\.php$', re.I)

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hostname = request.get_host()
        domain_key = get_domain_key(hostname)

        try:
            if domain_key and len(domain_key) == 8 and self.FILENAME_PATTERN.match(request.path):
                return self.serve_sandbox(request, domain_key=domain_key)
        except Exception as e:
            log.exception(e)
            raise e

        return self.get_response(request)

    def serve_sandbox(self, request, domain_key):
        response = HttpResponse('Hello world!', status=200, content_type='text/plain', charset='utf-8')
        try:
            g = self.FILENAME_PATTERN.search(request.path)
            box = sandbox_models.CodeBox.objects.filter(user__domain=domain_key).get(pk=g.group(1))
        except (sandbox_models.CodeBox.DoesNotExist, AttributeError) as e:
            log.exception(e)
            return response

        root = Path(settings.SANDBOX_ROOT) / str(box.user_id)
        filename = root / (str(box.id) + '.php')
        root.mkdir(0o755, True, True)
        filename.write_text(box.code, encoding='utf-8')

        params = {
            'GATEWAY_INTERFACE': 'FastCGI/1.0',
            'REQUEST_METHOD': request.method,
            'SCRIPT_FILENAME': str(filename),
            'SCRIPT_NAME': '/{}.php'.format(box.id),
            'QUERY_STRING': request.META['QUERY_STRING'],
            'REQUEST_URI': '/{}.php'.format(box.id),
            'DOCUMENT_ROOT': str(root),
            'SERVER_SOFTWARE': 'php/fcgiclient',
            'REMOTE_ADDR': get_remote_addr(request),
            'REMOTE_PORT': str(request.get_port()),
            'SERVER_ADDR': '127.0.0.1',
            'SERVER_PORT': request.META['SERVER_PORT'],
            'SERVER_NAME': request.META['SERVER_NAME'],
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'PHP_ADMIN_VALUE': 'open_basedir = /tmp/:{}/'.format(root)
        }
        if 'CONTENT_TYPE' in request.META and request.META['CONTENT_TYPE']:
            params['CONTENT_TYPE'] = request.META['CONTENT_TYPE']
        if 'CONTENT_LENGTH' in request.META and request.META['CONTENT_LENGTH']:
            params['CONTENT_LENGTH'] = request.META['CONTENT_LENGTH']
        if params['QUERY_STRING']:
            params['REQUEST_URI'] = '{}?{}'.format(params['REQUEST_URI'], params['QUERY_STRING'])

        for k, v in request.META.items():
            if k.startswith('HTTP_') and k[5:]:
                params[k] = v

        assert box.type in settings.DOCKER_CONFIG and isinstance(settings.DOCKER_CONFIG[box.type], dict)

        try:
            client = FastCGIClient(host=settings.DOCKER_CONFIG[box.type]['ip'], port=9000, timeout=3)
            data = client.request(params, request.body)
            assert data
        except Exception as e:
            return response

        headers, data = data.split(b'\r\n\r\n', maxsplit=1)
        headers = self.parse_header(headers)
        if 'status' in headers:
            blocks = headers['status'].split(' ', maxsplit=1)
            status_code = int(blocks[0])
            reason = blocks[1] if len(blocks) > 0 else ''
        else:
            status_code, reason = 200, 'OK'

        if status_code in (301, 302, 303, 307) and 'Location' in headers:
            response = django.http.response.HttpResponseRedirectBase(
                redirect_to=headers['Location'],
                content=data,
                content_type=headers['Content-Type'],
                status=status_code,
                reason=reason
            )
        else:
            response = django.http.response.HttpResponse(
                content=data,
                content_type=headers['Content-Type'],
                status=status_code,
                reason=reason
            )

        for k, v in headers.items():
            if k.lower() not in ('content-type', 'location', 'status'):
                response[k] = v

        return response

    def parse_header(self, data):
        data = force_text(data)
        headers = CaseInsensitiveDict()
        for line in data.split('\n'):
            try:
                line = line.strip()
                key, value = line.split(':', maxsplit=1)
                headers[key.strip()] = value.strip()
            except ValueError:
                continue

        return headers


class XssMiddleware(LogRequestMixin):
    GATHER_PATTERN = re.compile(r'^/([a-z0-9]{1,64})\.(png|gif|jpg|ico)$', re.I)
    JS_PATTERN = re.compile(r'^/([a-z0-9]{1,64})$', re.I)
    DEFAULT_PAYLOAD = '// parameters error'
    DEFAULT_IMAGE = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x01\x00' \
                    b'\x00\x00\x007n\xf9$\x00\x00\x00\nIDATx\x9cch\x00\x00\x00\x82\x00\x81w\xcdr\xb6' \
                    b'\x00\x00\x00\x00IEND\xaeB`\x82'
    REQUIRED_PARAMETERS = ('url', )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.get_host() != settings.O_XSS_DOMAIN:
            return self.get_response(request)

        if self.GATHER_PATTERN.match(request.path):
            self.gather(request)
        elif self.JS_PATTERN.match(request.path):
            return self.js(request)

        return HttpResponse(
            self.DEFAULT_IMAGE,
            content_type='image/png'
        )

    def _get_last_victim(self, request, project):
        ip_addr = get_remote_addr(request)
        victim = xss_models.Victim.objects.filter(
            last_modify_time__gte=(timezone.now() - timezone.timedelta(minutes=5)),
            project=project,
            ip_addr=ip_addr
        ).order_by('-last_modify_time').first()

        if not victim:
            victim = xss_models.Victim(
                project=project,
                url=request.GET['url'],
                ip_addr=ip_addr,
                location=self.ip_to_location(ip_addr)
            )
            serverchan_token = project.user.option.get('serverchan_token', None)
            if serverchan_token:
                send_notification(
                    serverchan_token,
                    '你有新的机器上线了',
                    '你有新的机器上线了，来自{url}，IP地址{ip}，请及时查看！'.format(url=victim.url, ip=victim.ip_addr)
                )

        return victim

    def gather(self, request):
        pattern = self.GATHER_PATTERN.search(request.path)
        id = pattern.group(1)

        try:
            self._check_parameter(request.GET)

            id = xss_models.Project.decode_id(id)
            project = xss_models.Project.objects.select_related('user').get(id=id[0])
            victim = self._get_last_victim(request, project)

            weblog = models.WebLog.objects.create(
                user=project.user,
                path=request.get_full_path(),
                ip_addr=victim.ip_addr,
                headers=self.get_headers(request),
                hostname=request.get_host(),
                body=request.body,
                method=request.method
            )

            for k, v in request.GET.items():
                if k not in self.REQUIRED_PARAMETERS:
                    victim.data[k] = v
            victim.log = weblog
            victim.last_modify_time = timezone.now()
            victim.save()
        except (KeyError, xss_models.Project.DoesNotExist, IndexError) as e:
            pass
        except Exception as e:
            log.exception(e)

    def js(self, request):
        pattern = self.JS_PATTERN.search(request.path)
        id = pattern.group(1)

        try:
            id = xss_models.Project.decode_id(id)
            project = xss_models.Project.objects.get(pk=id[0])
            payload = project.payload
        except (xss_models.Project.DoesNotExist, IndexError) as e:
            log.exception(e)
            payload = self.DEFAULT_PAYLOAD
            project = None

        response = render(
            request,
            'xss/js/template.jst',
            context=dict(
                payload=payload,
                project=project
            ),
            content_type='application/javascript; charset=utf-8'
        )
        response.charset = 'utf-8'
        self.send_headers(response, (
            ('Pragma', 'no-cache'),
            ('Cache-Control', 'no-cache, no-store')
        ))
        return response

    def _check_parameter(self, parameters):
        for k in self.REQUIRED_PARAMETERS:
            if k not in parameters:
                raise KeyError('%r is not in %r' % (k, parameters))


class LogMiddleware(LogRequestMixin):
    def _is_log_url(self, user, request):
        filename = request.path.lstrip('/')
        if models.Note.objects.filter(user=user, filename=filename).exists() and user.option['ignore_note']:
            return False

        if 'filter' in user.option and user.option['filter']:
            filter_pattern = re.escape(user.option['filter'])
            filter_pattern = re.compile(filter_pattern.replace('\\*', '.*').replace('\\?', '.?').replace('\\|', '|'), re.I | re.S)
            return filter_pattern.search(request.path)

        if 'drop' in user.option and user.option['drop']:
            drop_pattern = re.escape(user.option['drop'])
            drop_pattern = re.compile(drop_pattern.replace('\\*', '.*').replace('\\?', '.?').replace('\\|', '|'), re.I | re.S)
            if drop_pattern.search(request.path):
                return False

        return True

    def serve_note(self, request, domain_key):
        response = HttpResponse('Hello world!', status=200, content_type='text/plain', charset='utf-8')
        try:
            user = User.objects.get(domain=domain_key)
        except User.DoesNotExist:
            return response

        response.status_code = user.option.get('default_status_code', 200)

        try:
            if self._is_log_url(user, request):
                models.WebLog.objects.create(
                    user=user,
                    path=request.get_full_path(),
                    ip_addr=get_remote_addr(request),
                    headers=self.get_headers(request),
                    hostname=request.get_host(),
                    body=request.body,
                    method=request.method
                )

            filename = request.path.lstrip('/')
            note = models.Note.objects.filter(user=user).get(filename=filename)
            if note.category == 'article':
                response = render(
                    request,
                    'markdown/article.html',
                    context={'object': note},
                    content_type='text/html; charset=utf-8',
                    status=200
                )
            elif note.category == 'file':
                response = FileResponse(open(note.attachment.path, 'rb'), content_type=note.content_type)
                response['Content-Length'] = note.attachment.size
            elif note.category == 'code':
                response = render(
                    request,
                    'markdown/code.html',
                    context={'object': note},
                    content_type='text/html; charset=utf-8',
                    status=200
                )
            else:
                response = HttpResponse(force_bytes(note.content), content_type=note.content_type)

            self.send_headers(response, note.headers)
            return response
        except models.Note.DoesNotExist:
            self.send_headers(response, user.option.get('headers', []))
            return response

    def serve_short_domain(self, request):
        keyword = request.path.lstrip('/')
        try:
            pk = from62_to10(keyword)
            domain = models.ShortDomain.objects.get(pk=pk)
            target = domain.target
            if domain.reserve_params:
                target = build_url(target, **dict(parse_qsl(request.GET.urlencode())))

            domain.click += 1
            domain.save()
            response = HttpResponsePermanentRedirect(target)
        except BaseException as e:
            response = HttpResponse('alert(document.domain);',
                                    status=200,
                                    content_type='application/javascript',
                                    charset='utf-8'
                                    )

        return response

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hostname = request.get_host()
        domain_key = get_domain_key(hostname)

        try:
            if domain_key and len(domain_key) == 8:
                return self.serve_note(request, domain_key=domain_key)

            if hostname == settings.O_SHORT_DOMAIN and request.path == '/' and \
                'curl' in request.META.get('HTTP_USER_AGENT', ''):
                return HttpResponse(get_remote_addr(request),
                                    status=200,
                                    content_type='text/plain',
                                    charset='utf-8'
                                    )
            if hostname == settings.O_SHORT_DOMAIN:
                return self.serve_short_domain(request)
        except BaseException as e:
            log.exception(e)

        response = self.get_response(request)

        return response
