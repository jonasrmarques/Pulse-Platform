from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone


class RegistroPontoView(LoginRequiredMixin, TemplateView):
    template_name = "registro_ponto/registro_ponto.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["data_hoje"] = timezone.now().date()
        context["hora_atual"] = timezone.now().time()
        return context

class DashboardRegistroPontoView(TemplateView):
    template_name = "registro_ponto/dashboard.html"