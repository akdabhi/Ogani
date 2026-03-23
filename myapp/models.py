from django.db import models
from django.utils import timezone

# Create your models here.


class Department(models.Model):
    department_name = models.CharField(max_length=100)

    def __str__(self):
        return self.department_name


class Color(models.Model):
    color_name = models.CharField(max_length=50)

    def __str__(self):
        return self.color_name


class Sale(models.Model):
    pass


class Size(models.Model):
    sizes = models.CharField(max_length=50)

    def __str__(self):
        return self.sizes


class Product(models.Model):
    product_name = models.CharField(max_length=50)
    product_price = models.IntegerField()
    product_image = models.ImageField(
        upload_to="image", height_field=None, width_field=None, max_length=None
    )
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="Product"
    )
    color = models.ForeignKey(
        Color, on_delete=models.CASCADE, related_name="Product", null=True, blank=True
    )
    size = models.ForeignKey(
        Size, on_delete=models.CASCADE, related_name="Product", null=True, blank=True
    )
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.product_name


class App_user(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField(max_length=254, unique=True)
    phoneno = models.CharField(max_length=50, null=True, blank=True, unique=True)
    password = models.CharField(max_length=50)
    profile_image = models.ImageField(upload_to="profile_pics", null=True, blank=True)

    def __str__(self):
        return self.name


class Cart(models.Model):
    user = models.ForeignKey(App_user, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    update_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.user.name if self.user else "Guest Cart"


class Cart_Items(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    added_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def total_price(self):
        return self.quantity * self.price

    def _str_(self):
        return f"{self.product.product_name} ({self.quantity})"


class Wishlist(models.Model):
    user = models.ForeignKey(
        App_user, on_delete=models.CASCADE, related_name="wishlists"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist of {self.user.name}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(
        Wishlist, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("wishlist", "product")

    def __str__(self):
        return f"{self.product.product_name} in {self.wishlist}"


class Contact(models.Model):
    code = models.IntegerField()
    phone_no = models.IntegerField()
    mailid = models.EmailField(max_length=254)
    address = models.CharField(max_length=50)

    def __str__(self):
        return self.mailid


class Inquiry(models.Model):
    name = models.CharField(max_length=50)
    mail = models.EmailField(max_length=254)
    msg = models.TextField()

    def __str__(self):
        return self.name


class Coupon(models.Model):
    code = models.CharField(max_length=50)
    discription = models.TextField()
    discount = models.IntegerField(help_text="Discount percentage")
    active = models.BooleanField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    min_amt = models.IntegerField()

    def is_valid(self):
        now = timezone.now()
        return self.active and self.valid_from <= now <= self.valid_to

    def __str__(self):
        return self.code


class Order(models.Model):
    user = models.ForeignKey(App_user, on_delete=models.CASCADE)

    fname = models.CharField(max_length=50)
    lname = models.CharField(max_length=50)
    country = models.CharField(max_length=50)
    address = models.TextField()
    town_city = models.CharField(max_length=50)
    country_state = models.CharField(max_length=50)
    pincode = models.IntegerField()
    phoneno = models.CharField(max_length=15)
    email = models.EmailField()

    order_notes = models.TextField(blank=True, null=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.user.name}"


class OrderItem(models.Model):

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def total_price(self):
        return self.quantity * self.price


# class Checkout(models.Model):
#     user = models.ForeignKey(App_user, on_delete=models.CASCADE, null=True, blank=True)
#     fname = models.CharField(max_length=50)
#     lname = models.CharField(max_length=50)
#     country = models.CharField(max_length=50)
#     address = models.TextField()
#     town_city = models.CharField(max_length=50)
#     country_state = models.CharField(max_length=50)
#     pincode = models.IntegerField()
#     phoneno = models.PhoneNumberField()
#     email = models.EmailField(max_length=254)
#     # checkbox fields
#     create_account = models.BooleanField(default=False)
#     ship_different_address = models.BooleanField(default=False)

#     # extra fields from form
#     password = models.CharField(max_length=100, blank=True, null=True)
#     order_notes = models.TextField(blank=True, null=True)

#     def __str__(self):
#         return self.fname
