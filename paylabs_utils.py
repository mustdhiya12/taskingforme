import base64
import json
from datetime import datetime
from hashlib import sha256

import pytz
import requests

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding, ec, utils
from django.conf import settings
from rest_framework import status
from rest_framework.exceptions import APIException
from cryptography.exceptions import InvalidSignature

from payments.models import OJInvoice


def remove_nulls(obj):
    if isinstance(obj, dict):
        return {key: remove_nulls(value) for key, value in obj.items() if value is not None}
    elif isinstance(obj, list):
        return [remove_nulls(item) for item in obj if item is not None]
    else:
        return obj


def minify_json(json_string):
    try:
        # Load the JSON string into a Python object
        json_obj = json.loads(json_string)
        # Convert the Python object back to a minified JSON string
        minified_json = json.dumps(json_obj, separators=(',', ':'))
        return minified_json
    except ValueError as e:
        # Handle invalid JSON input
        return None


def sign_and_base64_encode(string_content, private_key_str):
    # Load the private key from a string
    private_key = serialization.load_pem_private_key(
        private_key_str.encode('utf-8'),
        password=None,
        backend=default_backend()
    )

    hash_value = string_content.encode('utf-8')

    # Sign the SHA-256 hash using RSA private key
    signature = private_key.sign(
        hash_value,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    base64_signature = base64.b64encode(signature).decode('utf-8')

    return base64_signature


def generate_request_id(merchant_id):
    return f'{merchant_id}{int(round(datetime.now().timestamp()))}'


def send_paylabs_request(method, merchant_id, request_id, endpoint_url, request_body):
    json_body = minify_json(json.dumps(remove_nulls(request_body)))
    root_url = settings.PAYLABS_ROOT_URL
    private_key_str = settings.PAYLABS_PRIVATE_KEYS
    # print(f'before hash: {json_body}')
    digest = sha256(json_body.encode('utf-8')).hexdigest()
    your_timezone = pytz.timezone('Asia/Bangkok')
    timestamp = datetime.now(your_timezone)
    formatted_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    formatted_timestamp = formatted_timestamp[:-2] + ":" + formatted_timestamp[-2:]
    timestamp = formatted_timestamp
    string_content = f'{method}:{endpoint_url}:{digest}:{timestamp}'
    x_signature = sign_and_base64_encode(string_content, private_key_str)

    post_url = f'{root_url}{endpoint_url}'
    header = {
        'X-TIMESTAMP': timestamp,
        'X-SIGNATURE': str(x_signature),
        'X-PARTNER-ID': str(merchant_id),
        'X-REQUEST-ID': request_id,
        'Content-Type': 'application/json',
    }
    data = json_body
    response = requests.post(post_url, data=data, headers=header)
    return response


# todo: copy dan refaktor fungsi untuk validasi signature dari google collab, setiap request dari paylab harus di verify terlebih dahulu
def verify_google_colab_signature(data, signature, public_key_pem):
    # Load the public key from a PEM-encoded string
    public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))

    try:
        # Decode the base64 signature
        signature_bytes = base64.b64decode(signature)

        # Verify the signature
        public_key.verify(
            signature_bytes,
            data.encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )

        return True  # Signature is valid
    except InvalidSignature:
        return False  # Signature is invalid

# Data yang akan diverifikasi
data_to_verify = "Data yang akan diverifikasi"

# Signature yang akan diverifikasi
signature_to_verify = "Signature dari Google Colab dalam bentuk base64"

# Kunci publik Google Colab dalam format PEM
google_colab_public_key_pem = """
-----BEGIN PUBLIC KEY-----
MIGbMBAGByqGSM49AgEGBSuBBAAjA4GGAAQBouCUp4Iexm1vIw2R0FlFYDc+3SVR
KpMPO1I/N5Kkx9lvf/NQI7vXmSGW6N3pTGLm59XFk7fOgZ0HbUvqWY2jC6F8Xuf0
TVYOaX7XYlZMBkHslBp6c6RGuu/XVOmL8COClpdwBhBjygyPnPhGO2MWgDABH6lS
GcnCHp1E5RdFTrmJDE/e+DdqrhtgD6lmHvnDL3IKisEbK7ED96vPS9kIefrN9ZgF
ttILz4/37Mv4y43nT/4A94rH9eJ9SP1BYRZs58L6THgGFDtrMX2fuMF73/MQGebS
Qs6YRwOiNZ1RQAMil0P3l1WGzo6hYqJ4qDLtzBb6ImtqH0QqV17JnlU=
-----END PUBLIC KEY-----
"""

# Memverifikasi tanda tangan
is_valid = verify_google_colab_signature(data_to_verify, signature_to_verify, google_colab_public_key_pem)

if is_valid:
    print("Tanda tangan valid")
else:
    print("Tanda tangan tidak valid")





def create_paylabs_emoney_request_body(invoice: OJInvoice):
    if not invoice.payment_option.category == 'emoney':
        raise APIException(detail="payment method error, it should be e-money", code=status.HTTP_400_BAD_REQUEST)

    merchant_id = settings.PAYLABS_MERCHANT_ID
    request_id = generate_request_id(merchant_id)

    product_infos = []

    for info in invoice.items.all():
        data = {
            "id": info.code,
            "name": info.product,
            "price": info.price,
            "type": info.product_type,
            "quantity": info.quantity
        }
        product_infos.append(data)

    base_url = settings.WEBHOOK_BASE_URL

    # todo : Verifikasi invoice.amount == total product_infos
    if invoice.amount != sum(item['price'] * item['quantity'] for item in product_infos):
        raise APIException(detail="Invoice amount does not match the total price of products", code=status.HTTP_400_BAD_REQUEST)

    return {
        "requestId": request_id,
        "merchantId": merchant_id,
        "paymentType": invoice.payment_option.payment_code,
        "amount": invoice.amount,
        "merchantTradeNo": invoice.invoice_number,
        "notifyUrl": f'{base_url}/payment/oj-invoice/{invoice.id}/payment_notify_webhook',
        "productName": invoice.transaction_model,
        "productInfo": product_infos
    }

# todo: buat untuk create body untuk virtual account, credit card, OTC, yang status inquiry semua, Order reconciliation file download link interface, sumber: https://paylabs.co.id/api-reference.html

