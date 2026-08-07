from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import ContactForm


class ContactView(CreateView):
    template_name = "contact/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("contact:contact")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your message has been sent. We'll get back to you soon.")
        return response
