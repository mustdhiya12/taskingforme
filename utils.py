import datetime

import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError

from accounting.models import UnsettledTransfer
from core.utils import create_ipaymu_header
from travel_agents.models import TravelAgents


def transfer_to_mitra(mitra: TravelAgents, nominal, transaction_id='-', notes='Transfer From On-journey'):
    account = mitra.ipaymu_account
    va = settings.IPAYMU_VA
    apikey = settings.IPAYMU_API_KEY
    url = settings.IPAYMU_URL
    body = {
        'sender': str(va),
        'receiver': str(account.va),
        'amount': str(nominal),
        'referenceId': str(transaction_id),
        'notes': str(notes)
    }
    data_body, headers = create_ipaymu_header(apikey, body, va)
    res = requests.post(url + '/api/v2/transferva', headers=headers, data=data_body)
    if not res.status_code == 200:
        if res.status_code == 400 and res.json()['Message'].lower() == 'transaction already exists':
            return {
                'message': 'transaksi {} sudah pernah dilakukan'.format(transaction_id)
            }
        try:
            unsettled = UnsettledTransfer.objects.get(transaction_ref_id=transaction_id)
            unsettled.timestamp = datetime.datetime.now()
            unsettled.save()
        except UnsettledTransfer.DoesNotExist:
            UnsettledTransfer.objects.create(
                transaction_ref_id=transaction_id,
                amount=nominal,
                va=account.va,
                reason=res.json()['Message'],
                settled=False,
                notes=notes
            )
        return {
            'message': res.json()['Message'] == 'Insufficient sender balance'
        }
    data = res.json()['Data']
    return data
