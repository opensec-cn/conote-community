from .settings import *


SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = False
ALLOWED_HOSTS = ['*']
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

IP_HEADER = 'HTTP_X_FORWARDED_FOR'

OAUTH = {
    'client_id': os.environ.get('CLIENT_ID'),
    'client_secret': os.environ.get('CLIENT_SECRET'),
    'callback_url': os.environ.get('CALLBACK_URL')
}

O_MAIN_DOMAIN = 'note.leavesongs.com'
O_SERVER_SCHEME = 'https'
O_SERVER_DOMAIN = 'o53.xyz'
O_NS1_DOMAIN = 'ns1.leavesongs.com'
O_NS2_DOMAIN = 'ns2.leavesongs.com'
O_SERVER_IP = '45.32.43.49'
O_XSS_DOMAIN = 'x.' + O_SERVER_DOMAIN
O_ADDITION_ZONE = f'''{O_SERVER_DOMAIN}.         IN      MX      5 {O_MAIN_DOMAIN}.
{O_XSS_DOMAIN}                            120 IN A   {O_SERVER_IP}
_acme-challenge.{O_SERVER_DOMAIN}.        120 IN TXT yodZC80OvmOEXqORA1K1O-FUmIC0R69mIEzKAYVJ_xI
_acme-challenge.{O_SERVER_DOMAIN}.        120 IN TXT LhUaoD1rbebH6T2O8UZ7EiWntcwtB4sfs5LOEtF4K20'''
O_REBIND_DOMAIN = 's.{}'.format(O_SERVER_DOMAIN)
O_SHORT_DOMAIN = 'mhz.pw'
O_MAIL_DOMAIN = O_SERVER_DOMAIN
O_RESERVE_DOMAINS = (O_SERVER_DOMAIN, O_SHORT_DOMAIN, O_REBIND_DOMAIN, O_XSS_DOMAIN, O_MAIL_DOMAIN)

STATIC_ROOT = os.environ.get('STATIC_ROOT')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT')

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'app.api.authentication.TokenAuthentication',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'app.api.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.JSONParser',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100,
}

HUEY['connection']['url'] = os.environ.get('REDIS_URL')
HUEY['always_eager'] = DEBUG

SANDBOX_ROOT = os.environ.get('SANDBOX_ROOT')
