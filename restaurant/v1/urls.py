from rest_framework import routers

import restaurant.v1.views as views

router = routers.DefaultRouter()
router.register('restaurant', views.RestaurantViewSet, 'restaurant')
router.register('dish', views.DishViewSet, 'dish')

urlpatterns = router.urls
