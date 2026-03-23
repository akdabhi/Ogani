from .models import App_user, Wishlist, Cart
from django.db.models import Sum


def user_session(request):
    user_id = request.session.get("user_id")
    user_name = request.session.get("user_name")

    return {
        "is_logged_in": bool(user_id),
        "user_name": user_name if user_name else "Welcome please login",
    }


def wishlist_cart_count(request):

    wishlist_count = 0
    cart_count = 0

    user_id = request.session.get("user_id")

    if user_id:
        try:
            user = App_user.objects.get(id=user_id)

            wishlist = Wishlist.objects.filter(user=user).first()
            if wishlist:
                wishlist_count = wishlist.items.count()

            cart = Cart.objects.filter(user=user).first()
            if cart:
                cart_count = cart.items.count()

        except App_user.DoesNotExist:
            pass

    return {
        "wishlist_count": wishlist_count,
        "cart_count": cart_count,
    }
