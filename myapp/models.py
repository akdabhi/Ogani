from django.db import models

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    image = models.ImageField(upload_to="image")
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, related_name="Product"
    )

    def __str__(self):
        return self.name
