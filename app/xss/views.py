from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, AccessMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views import generic
from django.views.generic.edit import FormMixin

from pure_pagination.mixins import PaginationMixin
from conote.mixin import ReturnBackMixin, LogUrlMixin
from . import models, forms
from conote.const import VICTIM_SORT


User = get_user_model()


class ProjectList(AccessMixin, LogUrlMixin, ReturnBackMixin, FormMixin, generic.ListView):
    template_name = 'xss/project/list.html'
    form_class = forms.ProjectForm

    def get_queryset(self):
        return self.request.user.xss_projects.prefetch_related('victims').all()

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        pk = self.kwargs.get('pk', None)
        try:
            self.object = request.user.xss_projects.get(pk=pk)
        except models.Project.DoesNotExist as e:
            pass

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'object'):
            kwargs.update({'instance': self.object})
        return kwargs

    def form_valid(self, form):
        """
        If the form is valid, save the associated model.
        """
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        kwargs['template_payload'] = models.Payload.objects.all().order_by('created_time')
        return super().get_context_data(**kwargs)


class ProjectDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return self.request.user.xss_projects.all()


class VictimList(LoginRequiredMixin, LogUrlMixin, PaginationMixin, generic.ListView):
    template_name = 'xss/victim/list.html'
    paginate_by = 15

    def get(self, request, *args, **kwargs):
        if 'last_view_ids' in self.request.session and isinstance(self.request.session['last_view_ids'], list):
            models.Victim.objects.filter(
                project__user=self.request.user,
                id__in=self.request.session['last_view_ids']
            ).update(is_view=True)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return models.Victim.objects.filter(project__user=self.request.user).select_related('project', 'log').all()

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        self.request.session['last_view_ids'] = list(kwargs['object_list'].values_list('id', flat=True))
        return kwargs


class VictimDetail(LoginRequiredMixin, ReturnBackMixin, generic.DetailView):
    template_name = 'xss/victim/detail.html'

    def get_queryset(self):
        return models.Victim.objects.filter(project__user=self.request.user).select_related('project', 'log').all()

    def get_context_data(self, **kwargs):
        kwargs['victim_sort'] = dict(VICTIM_SORT)
        return super().get_context_data(**kwargs)


class VictimDelete(LoginRequiredMixin, ReturnBackMixin, generic.DeleteView):
    get = generic.DeleteView.http_method_not_allowed

    def get_queryset(self):
        return models.Victim.objects.filter(project__user=self.request.user).all()
