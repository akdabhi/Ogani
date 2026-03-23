from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import *
from django.db.models import Count
from django.db.models import Q
from decimal import Decimal, InvalidOperation
from django.contrib.auth.hashers import make_password, check_password
from django.db.models.functions import Random
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
import random
import time
from django.utils import timezone
from decimal import Decimal


# Create your views here.


def landing(request):
    """
    Root landing view.
    - If user is logged in (session has user_id) -> go to main index page.
    - If not logged in -> go to login page.
    """
    if request.session.get("user_id"):
        return redirect("index")
    return redirect("login")


def index(request):
    depts = Department.objects.all()
    products = Product.objects.all()
    pid = Product.objects.all()
    contact = Contact.objects.first()

    dept_id = request.GET.get("department")

    # Department filter
    if dept_id:
        products = products.filter(department_id=dept_id)

    # for avoid duplicate products
    products = products.distinct()

    context = {
        "depts": depts,
        "pid": pid,
        "contact": contact,
        "selected_dept": dept_id,
        "products": products,
    }
    return render(request, "index.html", context)


def shop_details(request, id):
    depts = Department.objects.all()
    pid = Product.objects.get(id=id)
    contact = Contact.objects.first()

    # wishlist_ids, wishlist_count = _wishlist_ids_and_count(request)

    context = {
        "depts": depts,
        "pid": pid,
        "contact": contact,
        # "wishlist_ids": wishlist_ids,
        # "wishlist_count": wishlist_count
    }
    return render(request, "shop-details.html", context)


def shop_grid(request):
    products = Product.objects.all()
    departments = Department.objects.annotate(count=Count("Product"))
    depts = Department.objects.all()
    colors = Color.objects.annotate(count=Count("Product"))
    sizes = Size.objects.all()
    query = request.GET.get("search")
    contact = Contact.objects.first()

    # dept_id = request.GET.get("department")
    dept_id = request.GET.getlist("department")
    color_ids = request.GET.getlist("color")
    # size_id = request.GET.get("size")
    size_id = request.GET.getlist("size")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")

    wishlist_ids, wishlist_count = _wishlist_ids_and_count(request)

    # Department filter
    if dept_id:
        products = products.filter(department_id__in=dept_id)

    # Color filter
    if color_ids:
        products = products.filter(color_id__in=color_ids)

    # Size filter
    if size_id:
        products = products.filter(size_id__in=size_id)

    # Price filter
    if min_price:
        min_price = min_price.replace("₹", "").strip()
        if min_price.isdigit():
            products = products.filter(product_price__gte=int(min_price))

    if max_price:
        max_price = max_price.replace("₹", "").strip()
        if max_price.isdigit():
            products = products.filter(product_price__lte=int(max_price))

    # search filter
    if query:
        products = products.filter(
            Q(product_name__icontains=query)
            | Q(department__department_name__icontains=query)
            | Q(color__color_name__icontains=query)
        )

    # for avoid duplicate products
    products = products.distinct()

    ####=============================Paginator code==============================
    paginator = Paginator(products, 9)
    page_number = request.GET.get("page", 1)
    try:
        page_number = int(page_number)
    except ValueError:
        page_number = 1
    products = paginator.get_page(page_number)
    show_page = paginator.get_elided_page_range(page_number, on_each_side=1, on_ends=1)

    query_params = request.GET.copy()
    if "page" in query_params:
        query_params.pop("page")

    context = {
        "pid": products,
        "pdept": departments,
        "depts": depts,
        "pcolor": colors,
        "psize": sizes,
        "selected_dept": dept_id,
        "selected_colors": color_ids,
        "selected_sizes": size_id,
        "show_page": show_page,
        "query_params": query_params.urlencode(),
        "wishlist_ids": wishlist_ids,
        "wishlist_count": wishlist_count,
        "contact": contact,
    }

    return render(request, "shop-grid.html", context)


def add_to_cart(request, product_id=None):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    try:
        app_user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        request.session.pop("user_id", None)
        request.session.pop("user_name", None)
        return redirect("login")

    pid = product_id
    if pid is None:
        pid = (
            request.POST.get("product_id")
            or request.GET.get("product_id")
            or request.GET.get("product")
        )
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return redirect("shoping-cart")

    product = get_object_or_404(Product, id=pid_int)

    # Quantity (POST supported; links default to 1)
    quantity = 1
    if request.method == "POST":
        try:
            quantity = int(request.POST.get("quantity", 1))
        except ValueError:
            quantity = 1
        if quantity < 1:
            quantity = 1

    cart, _ = Cart.objects.get_or_create(user=app_user)
    item, created = Cart_Items.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={"quantity": quantity, "price": product.product_price},
    )
    if not created:
        item.quantity = item.quantity + quantity
        item.price = product.product_price
        item.save()

    return redirect("shoping-cart")


def update_cart(request, item_id, action):
    """Increase/decrease quantity for a cart item of logged-in AppUser."""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    try:
        app_user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        request.session.pop("user_id", None)
        request.session.pop("user_name", None)
        return redirect("login")

    cart_item = get_object_or_404(Cart_Items, id=item_id, cart__user=app_user)

    if action == "increase":
        cart_item.quantity += 1
        cart_item.save()
    elif action == "decrease":
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()

    return redirect("shoping-cart")


def remove_from_cart(request, item_id=None):
    """Remove a cart item for logged-in AppUser (supports POST form or URL param)."""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    try:
        app_user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        request.session.pop("user_id", None)
        request.session.pop("user_name", None)
        return redirect("login")

    iid = item_id
    if iid is None:
        iid = request.POST.get("item_id")
    try:
        iid_int = int(iid)
    except (TypeError, ValueError):
        return redirect("shoping-cart")

    Cart_Items.objects.filter(id=iid_int, cart__user=app_user).delete()
    return redirect("shoping-cart")


def _get_cart(request):
    """Get cart from session (list of dicts: name, model, price, quantity)."""
    if "cart" not in request.session:
        request.session["cart"] = []
    raw = request.session["cart"]
    # Ensure all items are dicts (filter out corrupted/old-format entries)
    valid = [x for x in raw if isinstance(x, dict)]
    if len(valid) != len(raw):
        request.session["cart"] = valid
        request.session.modified = True
    return request.session["cart"]

    # def shoping_cart(request):
    """Show logged-in AppUser cart."""
    user_id = request.session.get("user_id")
    contact = Contact.objects.first()
    coupons = Coupon.objects.filter(active=True)
    depts = Department.objects.all()

    if not user_id:
        return redirect("login")

    try:
        app_user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        request.session.pop("user_id", None)
        request.session.pop("user_name", None)
        return redirect("login")

    cart_obj = Cart.objects.filter(user=app_user).first()

    if not cart_obj:
        cart_items = []
        cart_total = 0
    else:
        cart_items = list(cart_obj.items.select_related("product").all())
        cart_total = sum((ci.total_price() for ci in cart_items), Decimal("0"))

    context = {
        "depts": depts,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "user_name": request.session.get("user_name") or app_user.name,
        "contact": contact,
        "coupons": coupons,
    }
    return render(request, "shoping-cart.html", context)


from django.utils import timezone
from decimal import Decimal


def shoping_cart(request):

    user_id = request.session.get("user_id")
    contact = Contact.objects.first()
    coupons = Coupon.objects.filter(active=True)
    cid = Department.objects.all()

    if not user_id:
        return redirect("login")

    app_user = App_user.objects.get(id=user_id)
    depts = Department.objects.all()

    cart_obj = Cart.objects.filter(user=app_user).first()

    if not cart_obj:
        cart_items = []
        cart_total = Decimal("0")
    else:
        cart_items = list(cart_obj.items.select_related("product"))
        cart_total = sum((ci.total_price() for ci in cart_items), Decimal("0"))

    discount_amount = Decimal("0")

    # Apply coupon
    if request.method == "POST":
        code = request.POST.get("coupon_code")

        try:
            coupon = Coupon.objects.get(code__iexact=code)

            if not coupon.is_valid():
                request.session["coupon_error"] = "Coupon expired or inactive"

            elif cart_total < coupon.min_amt:
                request.session["coupon_error"] = (
                    f"Minimum order ₹{coupon.min_amt} required"
                )

            else:
                request.session["coupon_id"] = coupon.id
                request.session["coupon_error"] = ""

        except Coupon.DoesNotExist:
            request.session["coupon_error"] = "Invalid Coupon"

    # If coupon already applied
    coupon_id = request.session.get("coupon_id")

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)

            if coupon.is_valid() and cart_total >= coupon.min_amt:
                discount_amount = (cart_total * coupon.discount) / 100

        except Coupon.DoesNotExist:
            request.session.pop("coupon_id", None)

    final_total = cart_total - discount_amount

    context = {
        "depts": depts,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "final_total": final_total,
        "discount_amount": discount_amount,
        "user_name": request.session.get("user_name") or app_user.name,
        "contact": contact,
        "coupons": coupons,
        "coupon_error": request.session.get("coupon_error"),
        "cid": cid,
    }

    return render(request, "shoping-cart.html", context)


def main(request):
    return render(request, "main.html")


def contact(request):
    depts = Department.objects.all()
    contact = Contact.objects.first()
    name = request.GET.get("name")
    mail = request.GET.get("mail")
    inquiry = request.GET.get("inquiry")

    if name and mail and inquiry:
        Inquiry.objects.create(name=name, mail=mail, msg=inquiry)
    context = {
        "depts": depts,
        "contact": contact,
    }
    return render(request, "contact.html", context)


def checkout(request):

    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    app_user = App_user.objects.get(id=user_id)

    cart_obj = Cart.objects.filter(user=app_user).first()

    if not cart_obj:
        return redirect("shoping-cart")

    cart_items = cart_obj.items.select_related("product")

    subtotal = sum((i.total_price() for i in cart_items), Decimal("0"))

    discount = Decimal("0")
    coupon_id = request.session.get("coupon_id")

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            discount = (subtotal * coupon.discount) / 100
        except:
            pass

    total = subtotal - discount
    # Convert to paise
    razorpay_amount = int(total * 100)

    context = {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "total": total,
        "razorpay_amount": razorpay_amount,
        "depts": Department.objects.all(),
        "contact": Contact.objects.first(),
        "user_id": user_id,
        "app_user": app_user,
    }

    return render(request, "checkout.html", context)


# def checkout(request):
#     depts = Department.objects.all()
#     contact = Contact.objects.first()
#     context = {
#         "depts": depts,
#         "contact": contact,
#     }
#     return render(request, "checkout.html", context)


def blog(request):
    depts = Department.objects.all()
    contact = Contact.objects.first()
    context = {
        "depts": depts,
        "contact": contact,
    }
    return render(request, "blog.html", context)


def blog_details(request):
    depts = Department.objects.all()
    contact = Contact.objects.first()
    context = {
        "depts": depts,
        "contact": contact,
    }
    return render(request, "blog-details.html", context)


def register(request):
    error = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phoneno = request.POST.get("phoneno", "").strip()
        password = request.POST.get("password", "")
        confirmpassword = request.POST.get("confirmpassword", "")
        if not name or not email or not password or not confirmpassword:
            error = "All fields are required."
        elif password != confirmpassword:
            error = "Password and Confirm Password do not match."
        elif App_user.objects.filter(email=email).exists():
            error = "Email already registered."
        elif App_user.objects.filter(phoneno=phoneno).exists():
            error = "Phone number already registered."
        else:
            App_user.objects.create(
                name=name,
                email=email,
                phoneno=phoneno,
                password=make_password(password),
            )
            return redirect("login")
    return render(request, "register.html", {"error": error})


def login(request):
    # 🔥 If already logged in → go to index
    if request.session.get("user_id"):
        return redirect("index")

    error = None

    if request.method == "POST":
        email_or_phone = request.POST.get("email_or_phone", "").strip()
        password = request.POST.get("password", "")

        user = App_user.objects.filter(
            Q(email=email_or_phone) | Q(phoneno=email_or_phone)
        ).first()

        if user and check_password(password, user.password):
            # request.session.flush()  # clear old session safely
            request.session["user_id"] = user.id
            request.session["user_name"] = user.name
            # return redirect("profile")
            return redirect("index")
        else:
            error = "Invalid Email/Phone or Password"

    return render(request, "login.html", {"error": error})


def forgot(request):
    context = {}

    if request.method == "POST":
        # SEND OTP
        if "send_otp" in request.POST:
            email = request.POST.get("email", "").strip()

            if not email:
                context["error"] = "Email is required"
                return render(request, "forgot.html", context)

            if not App_user.objects.filter(email=email).exists():
                context["error"] = "Email not registered"
                return render(request, "forgot.html", context)

            otp = random.randint(100000, 999999)

            request.session["reset_email"] = email
            request.session["reset_otp"] = str(otp)
            request.session["otp_time"] = time.time()

            try:
                send_mail(
                    "Password Reset OTP",
                    f"Your OTP is {otp}",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )
                context["message"] = "OTP sent to your email"
                context["otp_sent"] = True
            except Exception:
                context["error"] = "Could not send email. Please contact support."

            return render(request, "forgot.html", context)

        # VERIFY OTP
        if "verify_otp" in request.POST:
            entered_otp = request.POST.get("otp", "").strip()
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            session_otp = request.session.get("reset_otp")
            email = request.session.get("reset_email")
            otp_time = request.session.get("otp_time")

            if not (session_otp and email and otp_time):
                context["error"] = "OTP session expired. Please request a new OTP."
                return render(request, "forgot.html", context)

            # 5 minute expiry
            if time.time() - otp_time > 300:
                context["error"] = "OTP expired. Please request a new OTP."
                return render(request, "forgot.html", context)

            if entered_otp != session_otp:
                context["error"] = "Invalid OTP"
                context["otp_sent"] = True
                return render(request, "forgot.html", context)

            if not new_password or new_password != confirm_password:
                context["error"] = "Passwords do not match"
                context["otp_sent"] = True
                return render(request, "forgot.html", context)

            try:
                user = App_user.objects.get(email=email)
            except App_user.DoesNotExist:
                context["error"] = "User not found"
                return render(request, "forgot.html", context)

            user.password = make_password(new_password)
            user.save()

            # clear reset session keys
            for key in ("reset_email", "reset_otp", "otp_time"):
                if key in request.session:
                    del request.session[key]

            context["message"] = "Password reset successful. You can now login."
            return render(request, "forgot.html", context)

    return render(request, "forgot.html", context)


def logout(request):
    request.session.flush()
    return redirect("index")


def profile(request):
    user_id = request.session.get("user_id")
    contact = Contact.objects.first()
    if not user_id:
        return redirect("login")
    try:
        user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        request.session.pop("user_id", None)
        request.session.pop("user_name", None)
        return redirect("login")
    error = None
    success = None
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phoneno = request.POST.get("phoneno", "").strip()
        profile_image = request.FILES.get("profile_image")
        if not name or not email or not phoneno:
            error = "Name, email and phone are required."
        elif App_user.objects.filter(email=email).exclude(id=user.id).exists():
            error = "Email already in use."
        elif App_user.objects.filter(phoneno=phoneno).exclude(id=user.id).exists():
            error = "Phone number already in use."
        else:
            user.name = name
            user.email = email
            user.phoneno = phoneno
            if profile_image:
                user.profile_image = profile_image
            user.save()
            request.session["user_name"] = user.name
            success = "Profile updated successfully."
    return render(
        request,
        "profile.html",
        {
            "user": user,
            "error": error,
            "success": success,
            "contact": contact,
        },
    )


def toggle_wishlist(request, product_id):
    """Add/remove a product from the logged-in AppUser's wishlist."""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    try:
        app_user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        request.session.pop("user_id", None)
        request.session.pop("user_name", None)
        return redirect("login")

    product = get_object_or_404(Product, id=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=app_user)
    existing = WishlistItem.objects.filter(wishlist=wishlist, product=product)
    if existing.exists():
        existing.delete()
    else:
        WishlistItem.objects.create(wishlist=wishlist, product=product)

    # Go back where we came from, or to wishlist page
    return redirect(request.META.get("HTTP_REFERER") or "wishlist")


def wishlist(request):
    """Show all wishlisted items for the logged-in AppUser."""
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")
    try:
        app_user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        request.session.pop("user_id", None)
        request.session.pop("user_name", None)
        return redirect("login")

    # contacts = Contact.objects.first()
    depts = Department.objects.all()
    categories = Department.objects.annotate(count=Count("Product"))
    wishlist_obj = Wishlist.objects.filter(user=app_user).first()
    contact = Contact.objects.first()
    if wishlist_obj:
        items = wishlist_obj.items.select_related("product")
    else:
        items = []

    wishlist_ids, wishlist_count = _wishlist_ids_and_count(request)

    return render(
        request,
        "wishlist.html",
        {
            # "contacts": contacts,
            "categories": categories,
            "user_name": request.session.get("user_name") or app_user.name,
            "wishlist_items": items,
            "wishlist_ids": wishlist_ids,
            "wishlist_count": wishlist_count,
            "contact": contact,
            "depts": depts,
        },
    )


def _wishlist_ids_and_count(request):
    """Return (product_id_list, count) for the logged-in AppUser's wishlist."""
    user_id = request.session.get("user_id")
    if not user_id:
        return [], 0
    try:
        app_user = App_user.objects.get(id=user_id)
    except App_user.DoesNotExist:
        return [], 0
    wishlist = Wishlist.objects.filter(user=app_user).first()
    if not wishlist:
        return [], 0
    ids = list(wishlist.items.values_list("product_id", flat=True))
    return ids, len(ids)


def search(request):
    query = request.GET.get("search")

    if query:
        products = Product.objects.filter(Q(name__icontains=query))
    else:
        products = Product.objects.all()
    return render(request, "shop-grid.html", {"products": products})


def place_order(request):

    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    app_user = App_user.objects.get(id=user_id)

    cart = Cart.objects.filter(user=app_user).first()
    cart_items = cart.items.all()

    subtotal = sum(i.total_price() for i in cart_items)

    discount = Decimal("0")
    coupon_id = request.session.get("coupon_id")

    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            discount = (subtotal * coupon.discount) / 100
        except:
            pass

    total = subtotal - discount

    order = Order.objects.create(
        user=app_user,
        fname=request.POST.get("fname"),
        lname=request.POST.get("lname"),
        country=request.POST.get("country"),
        address=request.POST.get("address"),
        town_city=request.POST.get("town_city"),
        country_state=request.POST.get("country_state"),
        pincode=request.POST.get("pincode"),
        phoneno=request.POST.get("phone"),
        email=request.POST.get("email"),
        subtotal=subtotal,
        total=total,
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order, product=item.product, quantity=item.quantity, price=item.price
        )

    cart_items.delete()

    return redirect("index")
