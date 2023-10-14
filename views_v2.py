from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from payments.models import OJInvoice, PaymentOption
from payments.serializers import OJInvoiceSerializer, PaymentOptionSerializer, PaymentOptionChoiceSerializer


class PaymentOptionViewSet(viewsets.ModelViewSet):
    queryset = PaymentOption.objects.all()
    serializer_class = PaymentOptionSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated]


class OJInvoiceViewsets(viewsets.ModelViewSet):
    queryset = OJInvoice.objects.order_by('pk')
    serializer_class = OJInvoiceSerializer
    parser_classes = (MultiPartParser, FormParser, JSONParser)
    permission_classes = [IsAuthenticated]
    filterset_fields = ('payee_name', 'paid')
    search_fields = ['invoice_number']

    @action(detail=True, methods=['POST'])
    def create_payment(self, request, pk=None):
        try:
            invoice = OJInvoice.objects.get(pk=pk)
        except OJInvoice.DoesNotExist:
            raise NotFound
        serializer = PaymentOptionChoiceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            option = PaymentOption.objects.get(pk=serializer.validated_data['payment_option_id'])
        except PaymentOption.DoesNotExist:
            raise NotFound
        invoice.payment_option = option
        invoice.save()

    @action(detail=True, methods=['POST'])
    def payment_notify_webhook(self, request, pk=None):
        # todo:
        # 1. terima response dari paylabs. dan simpan pada model payment request, gunakan pk untuk invoice id
        # 2. validasi signature dengan paylabs public key
        # 3. update field expired_at dan  paid  pada model OJInvoice dengan id = pk
        # 4. simpan invoice dan return
        pass
