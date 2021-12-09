from defusedxml.xmlrpc import monkey_patch, unmonkey_patch
monkey_patch()

from pathlib import Path
import xmlrpc.client

from django.views import generic
from django.core.exceptions import PermissionDenied
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404, redirect, resolve_url, render
from pure_pagination.mixins import PaginationMixin
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from conote.mixin import ReturnBackMixin, LogUrlMixin, VipRequiredMixin
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import Http404


from . import models
User = get_user_model()


RPC_SERVER = f"http://{settings.RPC_SETTING['HOST']}:{settings.RPC_SETTING['PORT']}"


class RPCMixin(object):
    def dispatch(self, request, *args, **kwargs):
        try:
            with xmlrpc.client.ServerProxy(RPC_SERVER, use_builtin_types=True, allow_none=True) as self.client:
                response = super().dispatch(request, *args, **kwargs)
        except ConnectionRefusedError:
            return render(request, '500.html', context=dict(errors='守护进程未启动'))

        return response


class ClientList(VipRequiredMixin, RPCMixin, generic.TemplateView):
    template_name = 'rat/list.html'

    def get_context_data(self, **kwargs):
        data = self.client.get_listener(self.request.user.id)

        kwargs['object_list'] = data['connections'] if data else []
        kwargs['address'] = settings.O_SERVER_IP
        kwargs['port'] = data['port'] if data else None

        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        start = request.POST.get('start', None)
        stop = request.POST.get('stop', None)

        if start:
            self.client.create_listener(request.user.id)
        elif stop:
            self.client.stop_listener(request.user.id)

        return redirect('rat:rat-list')


class ClientManager(VipRequiredMixin, RPCMixin, generic.TemplateView):
    template_name = 'rat/detail.html'

    def get_context_data(self, **kwargs):
        kwargs['object'] = self.client.get_connection(self.request.user.id, self.kwargs['pk'])
        if kwargs['object'] is None:
            raise Http404()

        return super().get_context_data(**kwargs)


class CommandExecute(VipRequiredMixin, RPCMixin, generic.View):
    def post(self, request, *args, **kwargs):
        serid = request.POST.get('serid')
        command = request.POST.get('command')

        self.client.execute(request.user.id, serid, command.encode())
        return JsonResponse(dict(status='success'))

    def get(self, request, *args, **kwargs):
        serid = request.GET.get('serid')
        connection = self.client.get_connection(self.request.user.id, serid)

        if connection is None:
            raise Http404()

        output = connection['output'].decode(encoding='utf-8', errors='ignore')
        return JsonResponse(dict(status='success', output=output))
