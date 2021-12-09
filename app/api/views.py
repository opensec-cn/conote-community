from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import generics

from . import serializers


class WebLogList(generics.ListAPIView):
    serializer_class = serializers.WeblogListSerializer

    def get_queryset(self):
        query = self.request.user.weblog_set.all()
        keyword = self.request.query_params.get('k')
        if keyword:
            query = query.filter(hostname__startswith=keyword+".")
        return query


class WebLogDetailDestroy(generics.RetrieveDestroyAPIView):
    serializer_class = serializers.WeblogSerializer

    def get_queryset(self):
        return self.request.user.weblog_set.all()


class DNSLogList(generics.ListAPIView):
    serializer_class = serializers.DNSLogSerializer

    def get_queryset(self):
        query = self.request.user.dnslog_set.all()
        keyword = self.request.query_params.get('k')
        if keyword:
            query = query.filter(hostname__startswith=keyword+".")
        return query


class DNSLogDetailDestroy(generics.RetrieveDestroyAPIView):
    serializer_class = serializers.DNSLogSerializer

    def get_queryset(self):
        return self.request.user.dnslog_set.all()
