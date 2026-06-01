import random
from decimal import Decimal
from datetime import timedelta
from uuid import uuid4
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from marketplace.models import Customer, Order, OrderItem, Payment, Product


COUNTRIES = ["US", "GB", "DE", "FR", "BG", "NL", "ES", "IT", "CA", "AU"]

CATEGORIES = [
    "electronics",
    "home",
    "books",
    "beauty",
    "sports",
    "toys",
    "clothing",
    "grocery",
]

FIRST_NAMES = [
    "Alex", "Maria", "Ivan", "Sofia", "Daniel", "Emma", "Noah", "Mia",
    "Lucas", "Olivia", "Nikolai", "Elena", "Martin", "Anna",
]
LAST_NAMES = [
    "Smith", "Johnson", "Brown", "Taylor", "Ivanov", "Petrova",
    "Dimitrov", "Georgieva", "Miller", "Wilson", "Garcia", "Martinez",
]

PRODUCT_NAMES = [
    "Wireless Mouse", "Mechanical Keyboard", "Desk Lamp", "Coffee Mug",
    "Notebook", "Running Shoes", "Yoga Mat", "Water Bottle",
    "Face Cream", "Bluetooth Speaker", "Backpack", "Phone Stand",
    "Cookbook", "Board Game", "T-Shirt", "Protein Bar",
]

PAYMENT_METHODS = [
    Payment.Method.CARD,
    Payment.Method.PAYPAL,
    Payment.Method.BANK_TRANSFER,
]


class Command(BaseCommand):
    help = "Seed the marketplace database with fake customers, products, orders, order items, and payments."

    def add_arguments(self, parser):
        parser.add_argument("--customers", type=int, default=1000)
        parser.add_argument("--products", type=int, default=300)
        parser.add_argument("--orders", type=int, default=5000)
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing marketplace data before seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        customers_count = options["customers"]
        products_count = options["products"]
        orders_count = options["orders"]
        clear = options["clear"]

        if customers_count < 1 or products_count < 1 or orders_count < 1:
            raise CommandError("--customers, --products, and --orders must all be greater than 0.")

        if clear:
            self.stdout.write("Clearing existing marketplace data...")
            Payment.objects.all().delete()
            OrderItem.objects.all().delete()
            Order.objects.all().delete()
            Product.objects.all().delete()
            Customer.objects.all().delete()

        self.stdout.write("Creating customers...")
        customers = self.create_customers(customers_count)

        self.stdout.write("Creating products...")
        products = self.create_products(products_count)

        self.stdout.write("Creating orders, order items, and payments...")
        self.create_orders(orders_count, customers, products)

        self.stdout.write(self.style.SUCCESS("Marketplace seed complete."))

    def create_customers(self, count):
        customers = []

        for index in range(count):
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)

            customers.append(
                Customer(
                    email=f"{first_name.lower()}.{last_name.lower()}.{index}.{uuid4().hex[:8]}@example.com",
                    first_name=first_name,
                    last_name=last_name,
                    country=random.choice(COUNTRIES),
                )
            )

        return Customer.objects.bulk_create(customers, batch_size=1000)

    def create_products(self, count):
        products = []

        for index in range(count):
            category = random.choice(CATEGORIES)
            price = Decimal(random.randint(500, 25000)) / Decimal("100")
            cost_ratio = Decimal(random.randint(35, 75)) / Decimal("100")
            cost = (price * cost_ratio).quantize(Decimal("0.01"))

            products.append(
                Product(
                    sku=f"SKU-{index + 1:06d}",
                    name=f"{random.choice(PRODUCT_NAMES)} {index + 1}",
                    category=category,
                    price=price,
                    cost=cost,
                    is_active=random.random() > 0.05,
                )
            )

        return Product.objects.bulk_create(products, batch_size=1000)

    def create_orders(self, count, customers, products):
        now = timezone.now()

        orders = []
        order_items = []
        payments = []

        for _ in range(count):
            customer = random.choice(customers)
            order_timestamp = now - timedelta(
                days=random.randint(0, 180),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            order_status = random.choices(
                population=[
                    Order.Status.PAID,
                    Order.Status.PENDING,
                    Order.Status.CANCELLED,
                    Order.Status.REFUNDED,
                ],
                weights=[0.82, 0.08, 0.06, 0.04],
                k=1,
            )[0]

            orders.append(
                Order(
                    customer=customer,
                    status=order_status,
                    order_timestamp=order_timestamp,
                )
            )

        created_orders = Order.objects.bulk_create(orders, batch_size=1000)

        for order in created_orders:
            selected_products = random.sample(products, k=random.randint(1, min(4, len(products))))
            total_amount = Decimal("0.00")

            for product in selected_products:
                quantity = random.randint(1, 3)
                unit_price = product.price
                total_amount += unit_price * quantity

                order_items.append(
                    OrderItem(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=unit_price,
                    )
                )

            payment_status = self.get_payment_status(order.status)

            payments.append(
                Payment(
                    order=order,
                    status=payment_status,
                    method=random.choice(PAYMENT_METHODS),
                    amount=total_amount.quantize(Decimal("0.01")),
                    processed_at=order.order_timestamp if payment_status != Payment.Status.PENDING else None,
                )
            )

        OrderItem.objects.bulk_create(order_items, batch_size=1000)
        Payment.objects.bulk_create(payments, batch_size=1000)

        return created_orders

    def get_payment_status(self, order_status):
        if order_status == Order.Status.PAID:
            return Payment.Status.SUCCEEDED

        if order_status == Order.Status.REFUNDED:
            return Payment.Status.REFUNDED

        if order_status == Order.Status.CANCELLED:
            return Payment.Status.FAILED

        return Payment.Status.PENDING
