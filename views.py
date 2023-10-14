import decimal
from django.shortcuts import get_object_or_404
from .models import Payable, Receivable
from django.utils import timezone
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, AndroidNotification, AndroidConfig
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounting.models import create_ledger
from core.firebase_utils import message_type
from core.firebase_utils.firestore import write_notification
from payments.models import OJInvoice

# Create your views here.
from payments.serializers import InvoiceSerializer
from tp_bookings.serializers import TravelPackageBookingSerializer


def notify_customer(customer, message, title, body, sound, icon):
    try:
        devices = FCMDevice.objects.filter(user=customer)
        order_data = message
        for device in devices:
            msg = Message(data=order_data, token=device.device_id,
                          android=AndroidConfig(collapse_key='new_order',
                                                priority='high', ttl=900,
                                                notification=AndroidNotification(title=title, body=body, sound=sound, icon=icon)
                                                )
                          )
            device.send_message(message=msg)
    except FCMDevice.DoesNotExist:
        pass


# todo : for accounting
def create_payables(instance):
    # Mengambil data instansiasi
    payee = instance.customer
    amount = instance.total_amount
    due_date = instance.due_date

    # menyimpan data
    payable = Payable(payee=payee, amount=amount, due_date=due_date)
    payable.save()

def create_receivables(instance):
    payer = instance.customer
    amount = instance.total_amount
    due_date = instance.due_date

    receivable = Receivable(payer=payer, amount=amount, due_date=due_date)
    receivable.save()

# class InvoiceViewsets(ModelViewSet):
#     queryset = Invoice.objects.order_by('pk')
#     serializer_class = InvoiceSerializer
#     parser_classes = (MultiPartParser, FormParser, JSONParser)
#     permission_classes = [IsAuthenticated]

#     def create(self, request, *args, **kwargs):
#         return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

#     def update(self, request, *args, **kwargs):
#         return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

#     def destroy(self, request, *args, **kwargs):
#         return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

#     @action(methods=['post'], detail=True, permission_classes=[IsAuthenticated])
#     def request_payments(self, request, *args, **kwargs):
#         invoice = self.get_object()
#         if invoice.customer != request.user:
#             return Response('you are not allowed to do this', status=status.HTTP_401_UNAUTHORIZED)
#         cash = False
#         if 'cash' in request.GET:
#             cash = request.GET['cash']
#         if invoice.paid:
#             return Response('invoice already paid', status=status.HTTP_400_BAD_REQUEST)
#         if invoice.payment_url and invoice.signature:
#             return Response('payment already requested', status=status.HTTP_400_BAD_REQUEST)
#         invoice.create_payments(cash)
#         invoice.save()
#         serializer = InvoiceSerializer(invoice)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     @action(methods=['GET'], detail=False, permission_classes=[IsAuthenticated])
#     def my_invoices(self, request, *args, **kwargs):
#         queryset = Invoice.objects.filter(customer=request.user, paid=False)
#         serializer = InvoiceSerializer(queryset, many=True)
#         return Response(serializer.data, status=status.HTTP_200_OK)

#     @action(methods=['POST'], detail=True, permission_classes=[AllowAny], name='notify_webhook')
#     def notify_webhook(self, request, *args, **kwargs):
#         try:
#             invoice = self.get_object()
#         except Invoice.DoesNotExist:
#             return Response('invoice not found', status=status.HTTP_404_NOT_FOUND)
#         if not request.GET.get('signature') == invoice.signature:
#             return Response('invalid signature', status=status.HTTP_400_BAD_REQUEST)
#         try:
#             if request.data['status'] == 'berhasil':
#                 invoice.paid = 1
#                 invoice.updated_at = timezone.now()
#                 invoice.trx_id = request.data['trx_id']
#                 invoice.transaction_fee = request.data['fee']
#                 invoice.via = request.data['via']
#                 invoice.save()
#         except KeyError:
#             raise ValidationError(str(request.data))
#         if invoice.transaction_type == 'travel_package':
#             order_id = invoice.travel_package_booking.pk
#             transaction_type = 'travel_package'
#             if request.data['status'] == 'berhasil':
#                 invoice.travel_package_booking.status = 2
#                 invoice.travel_package_booking.save()
#                 write_notification(order_id,
#                                    'booking {} has been paid'.format(invoice.travel_package_booking.code),
#                                    company_id=invoice.travel_package_booking.travel_agent.id,
#                                    msg_type=message_type.PAID_ORDER, title='Paid Order',
#                                    msg_obj=invoice.travel_package_booking)
#         elif invoice.transaction_type == 'local_transports':
#             order_id = invoice.local_transport_order.pk
#             transaction_type = 'local_transports'
#         else:
#             order_id = 'not implemented'
#             transaction_type = 'not implemented'
#         notify_customer(invoice.customer, {'message': 'payment for invoice {} {}'.format(str(invoice.invoice_no),
#                                                                                          str(request.data['status'])),
#                                            'order_id': str(order_id), 'transaction_type': str(transaction_type)},
#                         'payment success', 'payment success', 'oj_success.mp3', 'oj.ico')
#         if request.data['status'] == 'berhasil':
#             create_ledger(decimal.Decimal(invoice.total_amount), 1, 1, invoice.trx_id)
#             create_ledger(decimal.Decimal(invoice.transaction_fee), 2, 1, invoice.trx_id)
#         return Response({'message': 'succeeded'}, status=status.HTTP_200_OK)

#     def confirm_cash_payment(self, request, pk, *args, **kwargs):
#         pass

#     @action(methods=['GET'], name='test_transfer_to_mitra', detail=False)
#     def test_transfer_to_mitra(self, request, *args, **kwargs):
#         mitra = TravelAgents.objects.get(pk=8)
#         data = transfer_to_mitra(mitra, 50000000, '1231', 'test transfer')
#         res = {
#             'transaction_id': data['TransactionId'],
#             'reference_id': data['ReferenceId'],
#             'amount': data['Amount'],
#             'fee': data['Fee'],
#             'sender': data['Sender'],
#             'receiver': data['Receiver'],
#             'notes': data['Notes']
#         }
#         return Response(res, status=status.HTTP_200_OK)
