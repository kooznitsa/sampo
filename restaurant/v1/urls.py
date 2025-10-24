from django.urls import include, path

from rest_framework import routers

import restaurant.v1.views as views

router = routers.DefaultRouter()
router.register('restaurant', views.RestaurantViewSet, 'restaurant')
router.register('dish', views.DishViewSet, 'dish')

urlpatterns = [
    path('', include(router.urls)),
]
