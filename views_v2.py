import json

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.http import HttpResponseBadRequest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

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
        try:
            invoice = OJInvoice.objects.get(pk=pk)
        except OJInvoice.DoesNotExist:
            raise NotFound

        # Ambil data respons dari Paylabs
        data = request.data

        # Ambil tanda tangan dari header
        x_signature = request.META.get("HTTP_X_SIGNATURE", "")

        # Validasi tanda tangan dengan kunci publik Paylabs
        if not verify_signature(data, x_signature, paylabs_public_key):
            return HttpResponseBadRequest("Invalid signature")

        # Simpan respons dari Paylabs ke model PaymentRequest atau sesuai kebutuhan aplikasi 
        payment_request = PaymentRequest(invoice=invoice, response_data=json.dumps(data))
        payment_request.save()

        # Perbarui invoice
        invoice.paid = True
        invoice.expired_at = invoice.calculate_new_expired_at() 
        invoice.save()
        invoice_serializer = OJInvoiceSerializer(invoice)
        return Response(invoice_serializer ,status=status.HTTP_405_METHOD_NOT_ALLOWED)

    
    # @action(detail=True, methods=['POST'])
    # def payment_notify_webhook(self, request, pk=None):
    #     # todo:
    #     # 1. terima response dari paylabs. dan simpan pada model payment request, gunakan pk untuk invoice id
    #     # 2. validasi signature dengan paylabs public key
    #     # 3. update field expired_at dan  paid  pada model OJInvoice dengan id = pk
    #     # 4. simpan invoice dan return
    #     pass
