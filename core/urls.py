from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('restaurant.v1.urls')),

    # -------------------------- Swagger ---------------------------------
    path('v1/swagger_yml/', SpectacularAPIView.as_view(api_version='v1'), name='schema-v1'),
    path('swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger'),
    path('v1/swagger/', SpectacularSwaggerView.as_view(url_name='schema-v1'), name='swagger-v1'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('v1/redoc/', SpectacularRedocView.as_view(url_name='schema-v1'), name='redoc-v1'),
]
