from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('rest/', include('apps.subsonic.urls')),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/', include('apps.music.urls')),
    # Serve React for all other routes
    re_path(r'^(?!rest/|api/|django-admin/|media/|static/).*$',
            TemplateView.as_view(template_name='index.html')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
