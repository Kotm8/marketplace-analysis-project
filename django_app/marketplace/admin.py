from django.contrib import admin

from .models import Customer, Order, OrderItem, Payment, Product


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "first_name", "last_name", "country", "created_at")
    search_fields = ("email", "first_name", "last_name")
    list_filter = ("country",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "name", "category", "price", "cost", "is_active")
    search_fields = ("sku", "name")
    list_filter = ("category", "is_active")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "order_timestamp", "created_at")
    search_fields = ("customer__email",)
    list_filter = ("status", "order_timestamp")
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "method", "amount", "processed_at")
    list_filter = ("status", "method")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "product", "quantity", "unit_price")
    search_fields = ("order__id", "product__sku", "product__name")
