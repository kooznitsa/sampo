from django.urls import include, path

from rest_framework import routers

import restaurant.v1.views as views

router = routers.DefaultRouter()
router.register('dish', views.DishViewSet, 'dish')
router.register('restaurant', views.RestaurantViewSet, 'restaurant')

urlpatterns = [
    path('', include(router.urls)),
]
