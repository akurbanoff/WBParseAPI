from pprint import pprint

import requests

num = "01"
article = "6170053"

headers = {
    "Referer": f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
    "Sec-Ch-Ua": "Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121",
    "Sec-Ch-Ua-Mobile" : "?0",
    "Sec-Ch-Ua-Platform" : "Linux",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
}

vol = article[:4]
part = article[:6]

supplier_info_url = f"https://basket-{num}.wbbasket.ru/vol{article[:2]}/part{article[:4]}/{article}/info/sellers.json"  # Ссылка с данными продавца
response = requests.request("GET", supplier_info_url, headers=headers)
pprint(response.json())
