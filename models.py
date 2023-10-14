import random
import time

from django.db import models
import random
import time

from django.db import models


# from core.utils import create_ipaymu_header


class PaymentOption(models.Model):
    CATEGORY = (
        ('va', 'virtual account'),
        ('emoney', 'e-money'),
        ('cc', 'credit card'),
        ('qris', 'qris'),
        ('otc', 'over the counter')
    )
    name = models.CharField(max_length=100)
    payment_code = models.CharField(max_length=20)
    category = models.CharField(max_length=12, choices=CATEGORY)
    minimum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    maximum_amount = models.DecimalField(max_digits=12, decimal_places=2)
    settlement = models.IntegerField(default=1, )
    transaction_fee = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.payment_code


# Define the Invoice model with payee and products information
def generate_invoice_number():
    # Generate 4 random digits
    random_digits = str(random.randint(1000, 9999))

    # Generate timestamp
    timestamp = str(int(time.time()))

    # Combine random digits and timestamp
    invoice_number = random_digits + timestamp

    return invoice_number


class OJInvoice(models.Model):
    SETTLEMENT_STATUS = (
        ('unsettled', 'unsettled'),
        ('paylabs_settled', 'settled in paylabs'),
        ('redeemed', 'redeemed')
    )
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    payee_name = models.CharField(max_length=100)
    payee_address = models.TextField(default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_option = models.ForeignKey(PaymentOption, on_delete=models.CASCADE, null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    paid = models.BooleanField(default=False)
    settlement = models.CharField(max_length=100, default='unsettled')
    transaction_model = models.CharField(max_length=30)
    transaction_ref_id = models.CharField(max_length=200)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = generate_invoice_number()
        super(OJInvoice, self).save(*args, **kwargs)

    def __str__(self):
        return self.invoice_number


# Define the InvoiceItem model to link products to invoices
class OJInvoiceItem(models.Model):
    invoice = models.ForeignKey(OJInvoice, on_delete=models.CASCADE, related_name='items')
    product = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    product_type = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField(default=1)
    product_detail = models.JSONField(null=True, blank=True)

    @property
    def sub_total(self):
        return self.price * self.quantity

    def __str__(self):
        return f"{self.product} - {self.quantity}"


class PaymentRequests(models.Model):
    invoice_id = models.CharField(max_length=100)
    endpoint = models.CharField(max_length=100)
    requests_header = models.JSONField(null=True, blank=True)
    requests_body = models.JSONField(null=True, blank=True)
    response_header = models.JSONField(null=True, blank=True)
    resonse_body = models.JSONField(null=True, blank=True)
