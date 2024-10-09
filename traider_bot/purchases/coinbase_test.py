from coinbase_commerce.client import Client

client = Client(api_key='1264cb22-9167-4409-ac39-81bfc0985a96')

charge_data = {
    "name": "Product Name",
    "description": "Product description",
    "pricing_type": "fixed_price",
    "local_price": {
        "amount": "100.00",
        "currency": "USDT"
    },
    "metadata": {
        "customer_id": "12345",
        "customer_name": "John Doe"
    }
}

charge = client.charge.create(**charge_data)
print(charge.hosted_url)

