import os
import re
import string
import logging
from flanker.addresslib import address as address_parser

from django.views import generic
from django.views.generic.detail import BaseDetailView
from django.db import transaction
from django.http import HttpResponseRedirect, HttpResponse, Http404, FileResponse, HttpRequest
from django.conf import settings
from django.utils.crypto import get_random_string
from django.shortcuts import get_object_or_404, redirect, resolve_url
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.views.generic.edit import FormMixin

from conote.emailparser.parser import MailParser
from conote.mixin import ReturnBackMixin, LogUrlMixin
from . import models
from . import forms


User = get_user_model()
logger = logging.getLogger('conote')


def generate_random_email(length=8):
    email = '{}@{}'.format(
        get_random_string(length, allowed_chars=string.ascii_lowercase + string.digits),
        settings.O_MAIL_DOMAIN
    )
    return email


class EmailList(LoginRequiredMixin, LogUrlMixin, ReturnBackMixin, FormMixin, generic.ListView):
    template_name = 'email/list.html'
    form_class = forms.DomainForm

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            self.object_list = self.get_queryset()
            return self.form_invalid(form)

    def get_queryset(self):
        return self.request.user.envelope_set.all()

    def get_context_data(self, **kwargs):
        kwargs['box'] = self.request.user.mail_boxes.order_by('-created_time').first()
        if not kwargs['box']:
            kwargs['box'] = models.MailBox.objects.create(
                email=generate_random_email(),
                user=self.request.user
            )

        kwargs['box_list'] = self.request.user.mail_boxes.all()
        kwargs['server_name'] = settings.O_MAIN_DOMAIN
        return super().get_context_data(**kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return dict(**kwargs, user=self.request.user)

    def form_valid(self, form):
        models.Domain.objects.get_or_create(name=form.cleaned_data['name'], defaults=dict(
            user=self.request.user
        ))
        models.MailBox.objects.create(email=form.cleaned_data['email'], user=self.request.user)
        return HttpResponseRedirect(self.get_success_url())


class EmailGenerate(LoginRequiredMixin, ReturnBackMixin, generic.View):
    def post(self, request, *args, **kwargs):
        if request.user.mail_boxes.all().count() <= 10:
            models.MailBox.objects.create(
                email=generate_random_email(),
                user=self.request.user
            )
        else:
            messages.add_message(request,
                                 messages.WARNING,
                                 '匿名邮箱数量已达上限，请删除没用的邮箱后再添加新的，或绑定自定义域名邮箱'
                                 )

        return HttpResponseRedirect(self.get_success_url())


class BoxDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return self.request.user.mail_boxes.all()


class EmailDetail(LoginRequiredMixin, generic.DetailView):
    template_name = 'email/detail.html'
    CID_PATTERN = re.compile(r'cid:([\w.-]+)', re.I | re.S)

    def get_queryset(self):
        return self.request.user.envelope_set.all()

    def get_context_data(self, **kwargs):
        path = self.object.get_path()

        try:
            email = MailParser.from_file(str(path))
            kwargs['email'] = dict(
                subject=email.subject,
                from_name=address_parser.parse(email.get_header('from')),
                to_list=address_parser.parse_list(email.get_header('to')),
                cc_list=address_parser.parse_list(email.get_header('cc')),
                content=self._get_html(email)
            )
        except Exception as e:
            logger.exception(e)
            raise Http404('Email object not found.')

        return super().get_context_data(**kwargs)

    def _get_html(self, email: MailParser):
        if not email.body:
            return email.body

        html = email.body
        for cid in self.CID_PATTERN.findall(html):
            try:
                html = self.CID_PATTERN.sub(email.attachments[cid].get_data_uri(), html)
            except KeyError:
                continue

        return html


class EmailDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return self.request.user.envelope_set.all()


class EmailDownload(LoginRequiredMixin, BaseDetailView):
    def get_queryset(self):
        return self.request.user.envelope_set.all()

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()

        response = FileResponse(self.object.get_path().open('rb'), content_type='text/plain')
        return response


class EmailFlush(LoginRequiredMixin, generic.RedirectView):
    pattern_name = 'disposable_email:list'

    def post(self, request, *args, **kwargs):
        request.user.envelope_set.all().delete()

        return super().post(request)
