from rest_framework.serializers import ModelSerializer
from rest_framework.fields import JSONField

from app.log import models as log_models


class WeblogSerializer(ModelSerializer):
    headers = JSONField()

    class Meta:
        model = log_models.WebLog
        fields = [
            'id',
            'hostname',
            'headers',
            'method',
            'path',
            'ip_addr',
            'body',
            'created_time'
        ]


class WeblogListSerializer(WeblogSerializer):
    class Meta:
        model = log_models.WebLog
        fields = [
            'id',
            'hostname',
            'method',
            'path',
            'ip_addr',
            'created_time'
        ]


class DNSLogSerializer(ModelSerializer):
    class Meta:
        model = log_models.DNSLog
        fields = [
            'id',
            'hostname',
            'dns_type'
        ]
