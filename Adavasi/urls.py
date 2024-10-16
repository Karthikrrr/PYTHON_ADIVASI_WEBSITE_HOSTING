from django.urls import path

from . import views

urlpatterns = [
    path('' , views.homeView, name="home"),
    path('product/' , views.productView, name="product"),
    path('checkout/', views.checkoutView, name="checkout"),
    path('cart/', views.cartView, name="cart_view"),
    path('confirmed/', views.orderConfirmedView, name="confirmed"),
]