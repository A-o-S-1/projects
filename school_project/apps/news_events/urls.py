from django.urls import path

from . import views

app_name = "news_events"

urlpatterns = [
    path("news/", views.NewsListView.as_view(), name="news_list"),
    path("news/<slug:slug>/", views.NewsDetailView.as_view(), name="news_detail"),
    path("events/", views.EventListView.as_view(), name="event_list"),
    path("events/<slug:slug>/", views.EventDetailView.as_view(), name="event_detail"),
]
