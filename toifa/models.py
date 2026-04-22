from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    order = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "Toifa"
        verbose_name_plural = "Toifalar"

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_PCS = "dona"
    UNIT_KG = "kg"
    UNIT_LITER = "litr"
    UNIT_CHOICES = (
        (UNIT_PCS, "Dona"),
        (UNIT_KG, "Kilogram"),
        (UNIT_LITER, "Litr"),
    )

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=150)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default=UNIT_PCS)
    sale_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    min_stock_limit = models.DecimalField(max_digits=14, decimal_places=3, default=0)
    image_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("category", "name")
        ordering = ["category__order", "name"]
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class ProductPriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_changes")
    old_price = models.DecimalField(max_digits=14, decimal_places=2)
    new_price = models.DecimalField(max_digits=14, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-changed_at"]
        verbose_name = "Narx tarixi"
        verbose_name_plural = "Narxlar tarixi"

    def __str__(self):
        return f"{self.product.name}: {self.old_price} -> {self.new_price}"

# Create your models here.
