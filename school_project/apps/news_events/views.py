from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import Event, NewsPost


class NewsListView(ListView):
    template_name = "news_events/news_list.html"
    context_object_name = "posts"
    paginate_by = 9

    def get_queryset(self):
        return NewsPost.published.all()


class NewsDetailView(DetailView):
    template_name = "news_events/news_detail.html"
    context_object_name = "post"

    def get_object(self):
        return get_object_or_404(NewsPost.published, slug=self.kwargs["slug"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recent_posts"] = NewsPost.published.exclude(pk=self.object.pk)[:4]
        return context


class EventListView(ListView):
    """
    Splits events into upcoming/past rather than one flat list — a parent
    checking "what's coming up" shouldn't have to scroll past last term's
    events to find it.
    """
    template_name = "news_events/event_list.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.published.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        all_events = self.get_queryset()
        context["upcoming_events"] = [e for e in all_events if e.start_datetime >= now]
        context["past_events"] = sorted(
            [e for e in all_events if e.start_datetime < now],
            key=lambda e: e.start_datetime,
            reverse=True,
        )
        return context


class EventDetailView(DetailView):
    template_name = "news_events/event_detail.html"
    context_object_name = "event"

    def get_object(self):
        return get_object_or_404(Event.published, slug=self.kwargs["slug"])
