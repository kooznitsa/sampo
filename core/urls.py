from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('restaurant.v1.urls')),

    # -------------------------- Swagger ---------------------------------
    path('api/v1/swagger_yml/', SpectacularAPIView.as_view(api_version='v1'), name='schema-v1'),
    path('api/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
    path('api/v1/swagger/', SpectacularSwaggerView.as_view(url_name='schema-v1'), name='swagger-v1'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema-v1'), name='redoc-v1'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
