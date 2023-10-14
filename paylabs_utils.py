import base64
import json
from datetime import datetime
from hashlib import sha256

import pytz
import requests

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
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

# Fungsi untuk membuat tanda tangan digital
def sign_and_base64_encode(data, private_key_str):
    private_key = serialization.load_pem_private_key(private_key_str.encode('utf-8'), password=None, backend=default_backend())
    data_bytes = data.encode('utf-8')
    
    signature = private_key.sign(data_bytes, padding.PKCS1v15(), hashes.SHA256())
    base64_signature = base64.b64encode(signature).decode('utf-8')
    
    return base64_signature

# Fungsi untuk melakukan verifikasi tanda tangan digital
def verify_signature(data, signature, public_key_str):
    public_key = serialization.load_pem_public_key(public_key_str.encode('utf-8'), backend=default_backend())
    data_bytes = data.encode('utf-8')
    signature_bytes = base64.b64decode(signature.encode('utf-8'))
    
    try:
        public_key.verify(signature_bytes, data_bytes, padding.PKCS1v15(), hashes.SHA256())
        return True  # Tanda tangan valid
    except Exception as e:
        return False  # Tanda tangan tidak valid

# Contoh penggunaan
private_key_str = """..."""  # Isi dengan kunci pribadi
public_key_str = """..."""   # Isi dengan kunci publik

# Buat data contoh
data_to_sign = "POST:/payment/v2/va/create:d4730fc9cf4907e36db6dd9baf3e75d3560bf790409f9999e83407f2da474ce0:2023-09-22T15:07:32.745185"

# Create tanda tangan digital
signature = sign_and_base64_encode(data_to_sign, private_key_str)

# Verifikasi tanda tangan digital
is_valid = verify_signature(data_to_sign, signature, public_key_str)

if is_valid:
    print("Tanda tangan valid.")
else:
    print("Tanda tangan tidak valid.")





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

# Fungsi untuk membuat tanda tangan digital
def sign_and_base64_encode(data, private_key_str):
    private_key = serialization.load_pem_private_key(private_key_str.encode('utf-8'), password=None, backend=default_backend())
    data_bytes = data.encode('utf-8')
    
    signature = private_key.sign(data_bytes, padding.PKCS1v15(), hashes.SHA256())
    base64_signature = signature

    return base64_signature

# Fungsi untuk membuat permintaan unduh file rekonsiliasi
def download_reconciliation_file(merchant_id, request_id, transaction_type, pay_date, private_key_str):
    root_url = "https://paylabs.co.id"  # Ganti dengan URL basis Paylabs yang sesuai
    endpoint_url = "/xxx/xxx"  # Ganti dengan endpoint yang sesuai
    
    # Format timestamp
    your_timezone = pytz.timezone('Asia/Bangkok')
    timestamp = datetime.datetime.now(your_timezone)
    formatted_timestamp = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
    formatted_timestamp = formatted_timestamp[:-2] + ":" + formatted_timestamp[-2:]

    # Buat data JSON untuk permintaan
    request_data = {
        "requestId": request_id,
        "merchantId": merchant_id,
        "transactionType": transaction_type,
        "payDate": pay_date
    }
    
    # Konversi data JSON ke string
    request_json = json.dumps(request_data, separators=(',', ':'), ensure_ascii=False)

    # Hitung hash dari data JSON
    digest = sha256.sha256(request_json.encode('utf-8')).hexdigest()

    # Buat string konten untuk tanda tangan digital
    content_string = f"POST:{endpoint_url}:{digest}:{formatted_timestamp}"

    # Buat tanda tangan digital
    signature = sign_and_base64_encode(content_string, private_key_str)

    # Header untuk permintaan
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        "X-TIMESTAMP": formatted_timestamp,
        "X-SIGNATURE": signature,
        "X-PARTNER-ID": merchant_id,
        "X-REQUEST-ID": request_id
    }

    # Kirim permintaan
    response = requests.post(f"{root_url}{endpoint_url}", json=request_data, headers=headers)

    # Tangani tanggapan
    if response.status_code == 200:
        response_data = response.json()
        if response_data["status"] == "2":
            # File siap untuk diunduh
            file_url = response_data.get("fileUrl")
            if file_url:
                # Lakukan pengunduhan file
                download_file(file_url)
            else:
                print("Tidak ada URL unduhan file dalam tanggapan.")
        else:
            print("Permintaan sedang diproses. Cek lagi nanti.")
    else:
        print("Gagal melakukan permintaan:", response.status_code)

# Fungsi untuk mengunduh file
def download_file(file_url):
    # Implementasikan logika pengunduhan file di sini
    pass

# Contoh penggunaan
merchant_id = "0010001"
request_id = "PY9f05af9d-4275-49e2-b972-a2427232c268"
transaction_type = "10"
pay_date = "2022-08-01"
private_key_str = """..."""  # Isi dengan kunci pribadi Anda

download_reconciliation_file(merchant_id, request_id, transaction_type, pay_date, private_key_str)