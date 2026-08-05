from django.views.generic import TemplateView


class HomeView(TemplateView):
    """
    Homepage. Kept as a plain TemplateView for now since Phase 1 Step 1
    is scaffolding only — Home's real content blocks (highlights,
    testimonials, latest news preview) are added in the next step
    alongside the About/Admissions/Contact pages.
    """
    template_name = "pages/home.html"
