"""
Root URL configuration.

Each app owns its own urls.py; this file only wires apps together under
their url prefixes. Keeping routing decisions inside each app (rather
than one giant list here) is what lets Phase 1 apps be added one at a
time without this file becoming unmanageable.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.pages.urls")),
]

# Serve user-uploaded media locally in development only. In production,
# Nginx (or the hosting platform) serves /media/ directly — Django never
# should in prod, for performance and security reasons.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
