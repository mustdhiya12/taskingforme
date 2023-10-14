from django.urls import path, include
from rest_framework.routers import SimpleRouter

# from payments.views import InvoiceViewsets
from payments.views_v2 import PaymentOptionViewSet, OJInvoiceViewsets

router = SimpleRouter()

# router.register(r'invoice', InvoiceViewsets)
router.register(r'payment-options', PaymentOptionViewSet)
router.register(r'oj-invoice', OJInvoiceViewsets)

urlpatterns = [
    path('', include(router.urls))
]
