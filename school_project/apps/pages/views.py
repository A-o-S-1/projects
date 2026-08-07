from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView

from .forms import AdmissionInquiryForm
from .models import AboutPage, AdmissionsPage, AdmissionStep, CoreValue


class HomeView(TemplateView):
    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Homepage shows a short preview of About content rather than
        # duplicating it — one source of truth, per our earlier decision.
        context["about"] = AboutPage.load()
        return context


class AboutView(TemplateView):
    template_name = "pages/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["about"] = AboutPage.load()
        context["core_values"] = CoreValue.objects.all()
        return context


class AdmissionsView(CreateView):
    """
    Displays admissions info AND handles the inquiry form on the same page
    (GET shows the page+empty form, POST validates and saves an inquiry).
    This mirrors the original site's admissions flow but replaces its
    dead '#' Enroll Now link with a working submission pipeline.
    """
    template_name = "pages/admissions.html"
    form_class = AdmissionInquiryForm
    success_url = reverse_lazy("pages:admissions")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["admissions"] = AdmissionsPage.load()
        context["steps"] = AdmissionStep.objects.all()
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Thank you — your inquiry has been received. Our admissions office will contact you shortly.",
        )
        return response
