from rest_framework import serializers

from payments.models import PaymentOption, OJInvoiceItem, OJInvoice
from users.serializers.Profile import UserProfileSerializer


# class InvoiceItemSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = InvoiceItems
#         fields = '__all__'
#
#
# class InvoiceSerializer(serializers.ModelSerializer):
#     customer = UserProfileSerializer(read_only=True)
#     invoice_items_set = InvoiceItemSerializer(many=True, read_only=True)
#
#     class Meta:
#         model = Invoice
#         fields = ['id', 'name', 'invoice_no', 'customer', 'valid_until', 'transaction_type',
#                   'payment_url', 'invoice_items_set', 'sub_total_amount', 'total_amount']


class PaymentOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentOption
        fields = '__all__'


class PaymentOptionChoiceSerializer(serializers.Serializer):
    payment_option_id = serializers.IntegerField()


class OJInvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OJInvoiceItem
        fields = '__all__'


class OJInvoiceSerializer(serializers.ModelSerializer):
    items = OJInvoiceItemSerializer(many=True, required=False)

    class Meta:
        model = OJInvoice
        fields = '__all__'

    def to_representation(self, instance):
        representation = super(OJInvoiceSerializer, self).to_representation(instance)
        items_data = OJInvoiceItemSerializer(instance.items.all(), many=True).data
        representation['items'] = items_data
        return representation


# todo: buat respose serializer dari paylabs, sumber: https://paylabs.co.id/api-reference.html#itemStaticVAAPI cari yang response body. masukkan semua fieldnya.

class PaymentActionSerializer(serializers.Serializer):
    pcUrl = serializers.CharField(max_length=200, required=False)
    webUrl = serializers.CharField(max_length=200, required=False)


# yang inicontoh untuk va
class ProductInfoSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=10)
    name = serializers.CharField(max_length=32)
    price = serializers.DecimalField(max_digits=12, decimal_places=2)
    type = serializers.CharField(max_length=20)
    url = serializers.CharField(max_length=200, required=False)
    quantity = serializers.IntegerField(min_value=1)

class VAResponseSerializer(serializers.Serializer):
    requestId = serializers.CharField(max_length=64, required=True)
    errCode = serializers.CharField(max_length=32, required=False)
    errCodeDes = serializers.CharField(max_length=128, required=False)
    merchantId = serializers.CharField(max_length=20, required=False)
    storeId = serializers.CharField(max_length=30, required=False)
    paymentType = serializers.CharField(max_length=20, required=True)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=True)
    merchantTradeNo = serializers.CharField(max_length=32, required=True)
    createTime = serializers.CharField(max_length=16, required=True)
    vaCode = serializers.CharField(max_length=32, required=False)
    platformTradeNo = serializers.CharField(max_length=32, required=False)
    successTime = serializers.CharField(max_length=16, required=False)
    expiredTime = serializers.CharField(max_length=16, required=False)
    status = serializers.CharField(max_length=32, required=False)
    productName = serializers.CharField(max_length=100, required=True)
    productInfo = ProductInfoSerializer(many=True, required=False)
    paymentActions = PaymentActionSerializer(required=False)
