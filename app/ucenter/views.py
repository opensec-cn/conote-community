from django.shortcuts import render, redirect, resolve_url
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

from requests_oauthlib import OAuth2Session
from . import forms
from conote.mixin import ReturnBackMixin


client_id = settings.OAUTH['client_id']
client_secret = settings.OAUTH['client_secret']
redirect_uri = settings.OAUTH['callback_url']
authorization_base_url = 'https://auth.tricking.io/o/authorize/'
token_url = 'https://auth.tricking.io/o/token/'
profile_url = 'https://auth.tricking.io/api/profile/'

User = get_user_model()


def jump_for_login(request):
    session = OAuth2Session(client_id, redirect_uri=redirect_uri)
    authorization_url, state = session.authorization_url(authorization_base_url)

    # State is used to prevent CSRF, keep this for later.
    request.session['oauth_state'] = state
    return redirect(authorization_url)


def callback(request):
    try:
        if 'oauth_state' not in request.session:
            raise PermissionDenied("state error")

        session = OAuth2Session(client_id, state=request.session['oauth_state'], redirect_uri=redirect_uri)
        token = session.fetch_token(token_url, client_secret=client_secret,
                                   authorization_response=request.build_absolute_uri())

        # At this point you can fetch protected resources but lets save
        # the token and show how this is done from a persisted token
        # in /profile.
        request.session['oauth_token'] = token
    except BaseException as e:
        return render(request, '500.html', context=dict(errors=str(e)))

    return redirect(resolve_url('auth:check'))


class RegisterView(generic.CreateView):
    model = User
    fields = [
        'username',
        'email'
    ]
    template_name = 'registration/register.html'

    def dispatch(self, request, *args, **kwargs):
        try:
            session = OAuth2Session(client_id, token=request.session['oauth_token'])
            self.user_data = session.get(profile_url).json()
        except BaseException as e:
            return render(request, '500.html', context=dict(errors=str(e)))

        user = User.objects.filter(auth_id=self.user_data['auth_id']).first()
        if user:
            self.login(user)
            return redirect(resolve_url(settings.LOGIN_REDIRECT_URL))
        else:
            return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        return dict(
            username=self.user_data['username'],
            email=self.user_data['email']
        )

    def login(self, user):
        auth_login(self.request, user)
        self.request.session.pop('oauth_token', None)
        self.request.session.pop('oauth_state', None)

    @transaction.atomic
    def form_valid(self, form):
        form.instance.set_unusable_password()
        form.instance.auth_id = self.user_data['auth_id']
        user = form.save()
        self.login(user)
        return redirect(resolve_url(settings.LOGIN_REDIRECT_URL))


class OptionView(LoginRequiredMixin, ReturnBackMixin, generic.FormView):
    template_name = 'registration/option.html'
    form_class = forms.OptionForm

    def get_initial(self):
        return self.request.user.option

    def form_valid(self, form):
        self.request.user.option = form.cleaned_data
        self.request.user.save()
        return HttpResponseRedirect(self.get_success_url())
