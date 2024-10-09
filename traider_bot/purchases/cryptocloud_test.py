from decimal import Decimal

import requests

url = 'https://api.cryptocloud.plus/v2/invoice/create'

data = {
    'shop_id': 'RcwKDcGjGzqJHRgv',
    'amount': '5',
    'currency': 'USD',
    'email': 'r.s.ricce@gmail.com',
}

headers = {
    'Authorization': 'Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1dWlkIjoiTWpZek5qTT0iLCJ0eXBlIjoicHJvamVjdCIsInYiOiI4OTNmYjYzOWU5OWM5OTM4MDMyOWVlNGMwZjYwMDcyMmVmZTIzY2U5NzgyYjczMzU0MWE1ZjIzZDFlYjU3YmFhIiwiZXhwIjo4ODEyODE0NDYxN30.vTgQxiEywQL4mzeO5qK-LMVBG3B_sqSGEWATzNMkJAY',
    'Content-Type': 'application/json'
}

response = requests.post(url, json=data, headers=headers)

print("Статус-код ответа:", response.status_code)
print("Тело ответа:", response.text)
