"""
XML sitemap configuration, used by search engines to discover and
prioritize pages. Uses Django's built-in sitemaps framework (no extra
dependency) — combines a static list of key pages with dynamically
generated entries for every published news post and event.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.news_events.models import Event, NewsPost


class StaticViewSitemap(Sitemap):
    priority = 0.6
    changefreq = "monthly"

    def items(self):
        return [
            "pages:home",
            "pages:about",
            "academics:academics",
            "pages:admissions",
            "staff:directory",
            "staff:management",
            "gallery:gallery",
            "news_events:news_list",
            "news_events:event_list",
            "contact:contact",
        ]

    def location(self, item):
        return reverse(item)

    def priority_for(self, item):
        return 1.0 if item == "pages:home" else 0.6


class NewsSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return NewsPost.published.all()

    def lastmod(self, obj):
        return obj.created_at


class EventSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Event.published.all()

    def lastmod(self, obj):
        return obj.created_at


sitemaps = {
    "static": StaticViewSitemap,
    "news": NewsSitemap,
    "events": EventSitemap,
}
