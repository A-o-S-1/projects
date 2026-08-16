from django.views.generic import TemplateView

from .models import AcademicsPage, Department


class AcademicsView(TemplateView):
    template_name = "academics/academics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["academics_page"] = AcademicsPage.load()
        # prefetch_related avoids a separate query per department when the
        # template loops through each department's subjects.
        context["departments"] = Department.objects.prefetch_related("subjects")
        return context
