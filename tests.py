from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import PaymentOption
from .serializers import PaymentOptionSerializer


class PaymentOptionTests(APITestCase):
    def setUp(self):
        self.payment_option_data = {
            'name': 'Virtual Account 1',
            'payment_code': 'VA1',
            'category': 'va',
            'minimum_amount': '100.00',
            'maximum_amount': '1000.00',
            'settlement': 1,
            'transaction_fee': {"fee_type": "percentage", "value": 2.5}
        }
        self.payment_option = PaymentOption.objects.create(**self.payment_option_data)
        self.url = reverse('paymentoption-list')

    def test_create_payment_option(self):
        response = self.client.post(self.url, self.payment_option_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PaymentOption.objects.count(), 2)  # Jumlah objek PaymentOption dalam database

    def test_retrieve_payment_option(self):
        response = self.client.get(reverse('paymentoption-detail', args=[self.payment_option.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, PaymentOptionSerializer(self.payment_option).data)

    def test_update_payment_option(self):
        updated_data = {
            'name': 'Updated VA',
            'minimum_amount': '200.00',
            'transaction_fee': {"fee_type": "fixed", "value": 5.0}
        }
        response = self.client.put(reverse('paymentoption-detail', args=[self.payment_option.pk]), updated_data,
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.payment_option.refresh_from_db()
        self.assertEqual(self.payment_option.name, updated_data['name'])
        self.assertEqual(str(self.payment_option.minimum_amount), updated_data['minimum_amount'])
        self.assertEqual(self.payment_option.transaction_fee, updated_data['transaction_fee'])

    def test_delete_payment_option(self):
        response = self.client.delete(reverse('paymentoption-detail', args=[self.payment_option.pk]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PaymentOption.objects.count(), 0)  # Objek PaymentOption harus terhapus

    def test_list_payment_options(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PaymentOption.objects.count(), len(response.data))
