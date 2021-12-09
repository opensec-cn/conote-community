from rest_framework import renderers


class JSONRenderer(renderers.JSONRenderer):
    charset = 'utf-8'
