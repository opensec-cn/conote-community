from django.shortcuts import render
from django.contrib.auth.mixins import AccessMixin


class LogUrlMixin(object):
    def get(self, request, *args, **kwargs):
        request.session['back_url'] = request.build_absolute_uri()
        return super().get(request, *args, **kwargs)


class ReturnBackMixin(object):
    def get_success_url(self):
        if hasattr(self, 'success_url') and self.success_url:
            url = self.success_url
        elif 'back_url' in self.request.session:
            url = self.request.session['back_url']
        else:
            try:
                url = self.object.get_absolute_url()
            except AttributeError:
                url = '/'

        return url


class VipRequiredMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if not request.user.is_superuser and not request.user.is_vip:
            return render(request, '500.html', context=dict(errors='你不是内测用户，暂不能访问该模块！'))
        return super().dispatch(request, *args, **kwargs)
