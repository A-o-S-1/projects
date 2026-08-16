from django.urls import path

from . import views

app_name = "gallery"

urlpatterns = [
    path("gallery/", views.GalleryView.as_view(), name="gallery"),
]
