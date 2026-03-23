from django.shortcuts import render
from django.core.paginator import Paginator
from .models import *


# Create your views here.
def home(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    # CATEGORY FILTER
    category_id = request.GET.get("category")
    if category_id and category_id != "all":
        products = products.filter(category_id=category_id)

    # PRICE FILTER
    price = request.GET.get("pricerange")
    if price:
        products = products.filter(price__lte=price)

    # PAGINATION
    paginator = Paginator(products, 6)
    page_no = request.GET.get("page")
    page_obj = paginator.get_page(page_no)

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "price": price,
        "selected_category": category_id,
    }
    return render(request, "index.html", context)
