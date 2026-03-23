"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # path('admin/', admin.site.urls),
    path("", views.landing, name="landing"),
    path("home/", views.index, name="index"),
    path("shop-details/<int:id>/", views.shop_details, name="shop-details"),
    path("shop-grid/", views.shop_grid, name="shop-grid"),
    path("shoping-cart/", views.shoping_cart, name="shoping-cart"),
    path("add_to_cart/", views.add_to_cart, name="add_to_cart"),
    path("add_to_cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path(
        "update_cart/<int:item_id>/<str:action>/", views.update_cart, name="update_cart"
    ),
    path("remove_from_cart/", views.remove_from_cart, name="remove_from_cart"),
    path(
        "remove_from_cart/<int:item_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),
    # <int:id>
    path("main/", views.main, name="main"),
    path("contact/", views.contact, name="contact"),
    path("checkout/", views.checkout, name="checkout"),
    path("blog/", views.blog, name="blog"),
    path("blog-details/", views.blog_details, name="blog-details"),
    path("login/", views.login, name="login"),
    path("forgot/", views.forgot, name="forgot"),
    path("register/", views.register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("logout/", views.logout, name="logout"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path(
        "toggle_wishlist/<int:product_id>",
        views.toggle_wishlist,
        name="toggle_wishlist",
    ),
    path("place-order/", views.place_order, name="place_order"),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
