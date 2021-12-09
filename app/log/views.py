import os

from django.views import generic
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, Http404, FileResponse
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, resolve_url
from pure_pagination.mixins import PaginationMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from conote.mixin import ReturnBackMixin, LogUrlMixin
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from operator import or_
from functools import reduce

from . import forms
from . import models


User = get_user_model()


class IndexList(LoginRequiredMixin, LogUrlMixin, generic.TemplateView):
    template_name = 'index/list.html'

    def get_context_data(self, **kwargs):
        kwargs['weblog_list'] = self.request.user.weblog_set.all()[:5]
        kwargs['dnslog_list'] = self.request.user.dnslog_set.all()[:5]
        return super().get_context_data(**kwargs)


class WebLogList(LoginRequiredMixin, PaginationMixin, LogUrlMixin, generic.ListView):
    template_name = 'weblog/list.html'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        filter_ = Q(path__icontains=query) | Q(hostname__icontains=query) | Q(method__contains=query)
        return self.request.user.weblog_set.filter(filter_).all()


class WebLogDetail(LoginRequiredMixin, generic.DetailView):
    template_name = 'weblog/detail.html'

    def get_queryset(self):
        return self.request.user.weblog_set.all()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        response = FileResponse(ContentFile(self.object.body), content_type='application/octet-stream')
        response["Content-Disposition"] = "attachment; filename=raw.txt"
        return response


class WebLogDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return self.request.user.weblog_set.all()


class DNSLogList(LoginRequiredMixin, PaginationMixin, LogUrlMixin, generic.ListView):
    template_name = 'dnslog/list.html'
    paginate_by = 20

    def get_queryset(self):
        query = self.request.GET.get('query', '')
        return self.request.user.dnslog_set.filter(hostname__icontains=query).all()


class LogDelete(LoginRequiredMixin, ReturnBackMixin, generic.View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if request.POST.get('query') == 'all':
            request.user.dnslog_set.all().delete()
            request.user.weblog_set.all().delete()
        elif request.POST.get('query') == 'dns':
            request.user.dnslog_set.all().delete()
        elif request.POST.get('query') == 'web':
            request.user.weblog_set.all().delete()

        return redirect(self.get_success_url())


class NoteList(LoginRequiredMixin, PaginationMixin, LogUrlMixin, generic.ListView):
    paginate_by = 10
    template_name = 'note/list.html'

    def get_queryset(self):
        category = self.request.GET.get('category', 'text')
        query = self.request.GET.get('query', '')

        fieldlist = ['filename', 'content', 'title', 'headers', 'content_type']
        querylist = []

        for field in fieldlist:
            key = '{}__icontains'.format(field)
            param = {key: query}
            querylist.append(Q(**param))
        
        query_filter = reduce(or_, querylist)

        return self.request.user.note_set.filter(category=category).filter(query_filter).all()

    def get_context_data(self, *, object_list=None, **kwargs):
        queryset = self.request.user.note_set.all().values('category').annotate(cnt=Count('id')).order_by()
        kwargs['statistics'] = {d['category']:d['cnt'] for d in queryset}
        return super(NoteList, self).get_context_data(object_list=None, **kwargs)


class NotePreview(LoginRequiredMixin, generic.detail.BaseDetailView):
    def get_queryset(self):
        return self.request.user.note_set.all()

    def render_to_response(self, context):
        content = self.object.content
        if self.object.category == 'file':
            content = f'附件\n\n文件名：{self.object.filename}\n大小：{self.object.attachment.size}'

        return HttpResponse(content=content, content_type='text/plain', charset='utf-8')


class NoteCreate(LoginRequiredMixin, ReturnBackMixin, generic.CreateView):
    template_name = 'note/form.html'
    form_class = forms.NoteForm

    def get_initial(self):
        return {
            'content_type': '',
            'headers': self.request.user.option.get('headers', [])
        }

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        if self.kwargs['action'] == 'text':
            kwargs['init_fields'] = ['filename', 'content_type', 'content', 'headers']
        elif self.kwargs['action'] == 'file':
            kwargs['init_fields'] = ['filename', 'content_type', 'attachment', 'headers']
        elif self.kwargs['action'] == 'code':
            kwargs['init_fields'] = ['filename', 'title', 'language', 'content']
        elif self.kwargs['action'] == 'article':
            kwargs['init_fields'] = ['filename', 'title', 'content']

        return kwargs

    @transaction.atomic
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.category = self.kwargs['action']

        if self.kwargs['action'] == 'article':
            form.instance.content_type = 'text/html; charset=utf-8'
        elif self.kwargs['action'] == 'code':
            form.instance.content_type = 'text/html; charset=utf-8'

        if form.instance.content and isinstance(form.instance.content, str):
            form.instance.content = form.instance.content.replace('\r\n', '\n')

        return super().form_valid(form)

    def get_success_url(self):
        if 'sae' in self.request.POST:
            return resolve_url('log:note-update', pk=self.object.pk)

        return super().get_success_url()

    def get_context_data(self, **kwargs):
        kwargs['js_config'] = dict(
            action=self.kwargs['action']
        )
        return super().get_context_data(**kwargs)


class NoteDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return self.request.user.note_set.all()


class NoteUpdate(LoginRequiredMixin, ReturnBackMixin, generic.UpdateView):
    template_name = 'note/form.html'
    form_class = forms.NoteForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user

        if self.object.category == 'article':
            kwargs['init_fields'] = ['filename', 'title', 'content']
        elif self.object.category == 'code':
            kwargs['init_fields'] = ['filename', 'title', 'language', 'content']
        elif self.object.category == 'file':
            kwargs['init_fields'] = ['filename', 'content_type', 'attachment', 'headers']
        else:
            kwargs['init_fields'] = ['filename', 'content_type', 'content', 'headers']

        return kwargs

    def get_queryset(self):
        return self.request.user.note_set.all()

    @transaction.atomic
    def form_valid(self, form):
        if form.instance.content and isinstance(form.instance.content, str):
            form.instance.content = form.instance.content.replace('\r\n', '\n')

        return super().form_valid(form)

    def get_success_url(self):
        if 'sae' in self.request.POST:
            return self.request.build_absolute_uri()

        return super().get_success_url()

    def get_context_data(self, **kwargs):
        kwargs['js_config'] = dict(
            action=self.object.category
        )
        return super().get_context_data(**kwargs)


class ShortDomainList(LoginRequiredMixin, PaginationMixin, LogUrlMixin, generic.ListView):
    paginate_by = 15
    template_name = 'shortdomain/list.html'

    def get_queryset(self):
        return self.request.user.shortdomain_set.all()


class ShortDomainCreate(LoginRequiredMixin, ReturnBackMixin, generic.CreateView):
    template_name = 'shortdomain/form.html'
    form_class = forms.ShortDomainForm

    def get_initial(self):
        target = self.request.GET.get('target')
        return dict(target=target)

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ShortDomainUpdate(LoginRequiredMixin, ReturnBackMixin, generic.UpdateView):
    template_name = 'shortdomain/form.html'
    form_class = forms.ShortDomainForm

    def get_queryset(self):
        return self.request.user.shortdomain_set.all()


class ShortDomainDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return self.request.user.shortdomain_set.all()


class DNSRecordUpdate(LoginRequiredMixin, generic.DetailView):
    template_name = 'dnsrecord/form.html'

    def get_object(self, queryset=None):
        try:
            return self.request.user.dnsrecord
        except ObjectDoesNotExist:
            return models.DNSRecord.objects.create(
                user=self.request.user,
                last_visited=timezone.now()
            )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        ips = request.POST.getlist('ip', [])
        record = self.get_object()
        record.ips = ips
        record.save()
        messages.success(request, '已成功修改！')
        return HttpResponseRedirect(resolve_url('log:dns-record'))


class RefreshApiKey(LoginRequiredMixin, ReturnBackMixin, generic.View):
    def post(self, request, *args, **kwargs):
        request.user.refresh_apikey()
        return HttpResponseRedirect(self.get_success_url())
