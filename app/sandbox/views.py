from pathlib import Path

from django.views import generic
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect, resolve_url
from pure_pagination.mixins import PaginationMixin
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from conote.mixin import ReturnBackMixin, LogUrlMixin
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Count, Q

from . import models
User = get_user_model()


class SandboxList(LoginRequiredMixin, PaginationMixin, ReturnBackMixin, LogUrlMixin, generic.ListView):
    paginate_by = 15
    template_name = 'sandbox/list.html'

    def get_queryset(self):
        queryset = self.request.user.codebox_set.all()
        if 'type' in self.request.GET:
            queryset = queryset.filter(type=self.request.GET['type'])

        if 'query' in self.request.GET:
            query = self.request.GET.get('query', '')
            queryset = queryset.filter(Q(title__icontains=query) | Q(code__icontains=query))

        return queryset

    def get_context_data(self, *, object_list=None, **kwargs):
        statistics = {'all': 0}
        for d in self.request.user.codebox_set.all().values('type').annotate(cnt=Count('id')).order_by():
            if d['type'] == 'php-5.6':
                statistics['php56'] = d['cnt']
            elif d['type'] == 'php-7.2':
                statistics['php72'] = d['cnt']
            statistics['all'] += d['cnt']

        if 'php56' not in statistics:
            statistics['php56'] = 0
        if 'php72' not in statistics:
            statistics['php72'] = 0

        kwargs['statistics'] = statistics
        return super(SandboxList, self).get_context_data(object_list=object_list, **kwargs)


class SandboxCreate(LoginRequiredMixin, ReturnBackMixin, generic.CreateView):
    template_name = 'sandbox/form.html'
    model = models.CodeBox
    fields = [
        'title',
        'type',
        'code'
    ]

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        if 'sae' in self.request.POST:
            return resolve_url('sandbox:sandbox-update', pk=self.object.pk)

        return super().get_success_url()


class SandboxUpdate(LoginRequiredMixin, ReturnBackMixin, generic.UpdateView):
    template_name = 'sandbox/form.html'
    fields = [
        'title',
        'type',
        'code'
    ]

    def get_queryset(self):
        return self.request.user.codebox_set.all()

    def get_success_url(self):
        if 'sae' in self.request.POST:
            return resolve_url('sandbox:sandbox-update', pk=self.object.pk)

        return super().get_success_url()


class SandboxDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return self.request.user.codebox_set.all()
