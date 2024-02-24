import datetime
from typing import Any
import time
import requests
from pprint import pprint
import asyncio

from src.parser.ParserStorage import ParserStorage

headers = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/catalog/98873141/detail.aspx",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "cross-site",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Linux\""
}

basket_numbers = ["01", "09", "10", "12", "14"]

# supplier_id = "98009"
# root = ""


def parse_good(article: str):
    """
        Время асинхронного парсинга - 32 секунды
    """
    storage = ParserStorage()

    start_time = time.time()

    asyncio.run(async_parsing(article, storage))
    asyncio.run(parse_other_goods(storage=storage))

    end_time = time.time()
    exec_time = end_time - start_time
    print(exec_time)


async def async_parsing(article: str, storage: ParserStorage):
    root, supplier_id, price, name = await parse_card_detail(article)
    storage.setPrice(price)
    storage.setGoodName(name)
    tasks = [
        parse_card_info(article),
        parse_feedback(root),
        parse_price_stats(article),
        parse_supplier_info(article, supplier_id),
        parse_supplier_detail_info(article)
    ]

    results = await asyncio.gather(*tasks)


async def parse_other_goods(storage: ParserStorage):
    price = storage.getPrice()
    good_name = storage.getGoodName()
    url = "https://search.wb.ru/exactmatch/ru/common/v4/search"  # Ссылка с товарами по запросу

    querystring = {"appType": "1", "curr": "rub", "dest": "-1257786", "fdlvr": "75", "priceU": f"{(int(price) * 0,85)};{int(price) * 1,15}",
                   "query": good_name, "resultset": "catalog", "sort": "rate", "spp": "30",
                   "suppressSpellcheck": "false"}

    response = requests.get(url, headers = headers, params=querystring)

    for good in response.json()["data"]["products"]:
        good_id = good["id"]
        storage.addNewId(good_id)
        await async_parsing(good_id)


async def parse_supplier_info(article: str, supplier_id: str):
    headers = {
        "authority": "suppliers - shipment.wildberries.ru",
        "method": "GET",
        "path": "/api/v1/suppliers/98009",
        "scheme": "https",
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru - RU, ru;q = 0.9, en - US;q = 0.8, en;q = 0.7",
        "Origin": "https://www.wildberries.ru",
        "Referer": f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
        "Sec-Ch-Ua": "Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Linux",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "X-Client-Name": "site"
    }
    supplier_detail_url = f"https://suppliers-shipment.wildberries.ru/api/v1/suppliers/{supplier_id}"  # Ссылка тоже с данными продавца, такими как количество продаж и тп(цифры - supplierId из карточки)
    response = requests.request("GET", supplier_detail_url, headers=headers)
    json = response.json()
    defectPercent = json["defectPercent"]
    feedbackCount = json["feedbacksCount"]
    isPremium = json["isPremium"]
    regDate = json["registrationDate"]
    saleItemAmount = json["saleItemQuantity"]
    rating = json["valuation"]

    with open("data/supplier_detail_info.txt", "w", encoding="utf-8") as file:
        data = f"Процент возвратов - {defectPercent}\nКоличество отзывов о продавце - {feedbackCount}\nЕсть премиум - {isPremium}\nДата регистрации - {regDate}\nКоличество проданных товаров - {saleItemAmount}\nРейтинг продавца - {rating}"
        file.write(data)
        file.close()


async def parse_supplier_detail_info(article: str):
    headers = {
        "Referer": f"https://www.wildberries.ru/catalog/{article}/detail.aspx",
        "Sec-Ch-Ua": "Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121",
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": "Linux",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }
    json: Any = ""
    for num in basket_numbers:
        supplier_info_url = f"https://basket-{num}.wbbasket.ru/vol{article[:4]}/part{article[:6]}/{article}/info/sellers.json"  # Ссылка с данными продавца
        response = requests.request("GET", supplier_info_url, headers=headers)
        if response.status_code == 200:
            json = response.json()
        supplier_info_url = f"https://basket-{num}.wbbasket.ru/vol{article[:2]}/part{article[:4]}/{article}/info/sellers.json"  # Ссылка с данными продавца
        response = requests.request("GET", supplier_info_url, headers=headers)
        if response.status_code == 200:
            json = response.json()
    else:
        for num in range(1, 15):
            current_num = str(num)  # подумать как оптимизировать выбор числа
            if int(current_num) < 1:
                current_num = "1"
            if int(current_num) < 10:
                current_num = f"0{current_num}"

            supplier_info_url = f"https://basket-{current_num}.wbbasket.ru/vol{article[:4]}/part{article[:6]}/{article}/info/sellers.json"  # Ссылка с данными продавца
            response = requests.request("GET", supplier_info_url, headers=headers)
            if response.status_code == 200:
                basket_numbers.append(current_num)
                json = response.json()
            supplier_info_url = f"https://basket-{current_num}.wbbasket.ru/vol{article[:2]}/part{article[:4]}/{article}/info/sellers.json"  # Ссылка с данными продавца
            response = requests.request("GET", supplier_info_url, headers=headers)
            if response.status_code == 200:
                json = response.json()

    inn = json["inn"]
    kpp = json["kpp"]
    address = json["legalAddress"]
    ogrn = json["ogrn"]
    rv = json["rv"]
    supplier_name = json["supplierFullName"]
    trademark = json["trademark"]

    with open("data/supplier_info.txt", "w", encoding="utf-8") as file:
        data = f"ИНН - {inn}\nКПП - {kpp}\nАдрес - {address}\nОГРН - {ogrn}\nРВ - {rv}\nИмя продавца - {supplier_name}\nТорговая марка - {trademark}"
        file.write(data)
        file.close()


async def parse_feedback(root: str):
    feedback_url = f"https://feedbacks2.wb.ru/feedbacks/v1/{root}"  # Ссылка с данными отзывов по карточке, запрос идет по цифрам из root параметра в карточке
    response = requests.request("GET", feedback_url, headers=headers)
    json = response.json()

    feedbacks_count = int(json["feedbackCount"])

    with open("data/feedbacks_text.txt", "w", encoding="utf-8") as file:
        for i in range(0, feedbacks_count - 1):
            try:
                feedbacks_body = json["feedbacks"][i]
                feedback = feedbacks_body["text"]
                if len(feedback) < 50:
                    continue
                feedback_created = feedbacks_body["createdDate"]
                feedback_updated = feedbacks_body["updatedDate"]
                try:
                    date_created = datetime.datetime.strptime(feedback_created, "%Y-%m-%dT%H:%M:%SZ")
                    date_updated = datetime.datetime.strptime(feedback_updated, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError as e:
                    continue
                date_now = datetime.date.today()
                if date_created.month < date_now.month - 6:
                    continue

                data = f"""\n
Feedback - {i}
Created - {date_created.date()}
Updated - {date_updated.date()}
Text - {feedback}\n"""
                file.write(data)
            except IndexError as ex:
                file.close()
                break
        file.close()


async def parse_price_stats(article: str):
    json = ""
    for num in basket_numbers:
        price_stats_url = f"https://basket-{num}.wbbasket.ru/vol{article[:4]}/part{article[:6]}/{article}/info/price-history.json"  # Ссылка со статистикой изменения цены
        response = requests.request("GET", price_stats_url, headers=headers)
        if response.status_code == 200:
            json = response.json()
        price_stats_url = f"https://basket-{num}.wbbasket.ru/vol{article[:2]}/part{article[:4]}/{article}/info/price-history.json"  # Ссылка со статистикой изменения цены
        response = requests.request("GET", price_stats_url, headers=headers)
        if response.status_code == 200:
            json = response.json()
    else:
        for num in range(1, 15):
            current_num = str(num)
            if int(current_num) < 10:
                current_num = f"0{current_num}"

            price_stats_url = f"https://basket-{current_num}.wbbasket.ru/vol{article[:4]}/part{article[:6]}/{article}/info/price-history.json"  # Ссылка со статистикой изменения цены
            response = requests.request("GET", price_stats_url, headers=headers)
            if response.status_code == 200:
                basket_numbers.append(current_num)
                json = response.json()

            price_stats_url = f"https://basket-{current_num}.wbbasket.ru/vol{article[:2]}/part{article[:4]}/{article}/info/price-history.json"  # Ссылка со статистикой изменения цены
            response = requests.request("GET", price_stats_url, headers=headers)
            if response.status_code == 200:
                basket_numbers.append(current_num)
                json = response.json()
    with open("data/prices.txt", "w", encoding="utf-8") as f:
        for price in list(json):
            price_amount = price["price"]["RUB"]
            f.write(f"{price_amount}\n")


async def parse_card_detail(article: str):
    querystring = {
        "appType": "1",
        "curr": "rub",
        "dest": "-1257786",
        "spp": "30",
        "nm": f'{article}'  # Артикул
    }
    card_detail_url = "https://card.wb.ru/cards/v1/detail"  # Сслыка с данными карточки
    card_detail = requests.request("GET", card_detail_url, headers=headers, params=querystring)

    json = card_detail.json()

    product_info = json["data"]["products"][0]

    brand = product_info["brand"]
    feedbacks_amount = product_info["feedbacks"]
    name = product_info["name"]
    return_cost = product_info["returnCost"]
    rating = product_info["reviewRating"]
    root = product_info["root"]
    price = product_info["salePriceU"]
    supplier = product_info["supplier"]
    supplier_id = product_info["supplierId"]
    supplier_rating = product_info["supplierRating"]
    volume = product_info["volume"]
    with open("data/card.txt", "w", encoding="utf-8") as file:
        data = (
            f"Бренд - {brand}\nКоличество отзывов - {feedbacks_amount}\nНазвание - {name}\nСтоимость возврата - {return_cost}\nРейтинг товара - {rating}\n"
            f"Цена - {price}\nПродавец - {supplier}\nРейтинг продавца - {supplier_rating}\nКоличество товаров на складе - {volume}")
        file.write(data)
        file.close()

    return root, supplier_id, price, name


async def parse_card_info(article: str):
    json: Any = ""
    for num in basket_numbers:
        card_info_url = f"https://basket-{num}.wbbasket.ru/vol{article[:4]}/part{article[:6]}/{article}/info/ru/card.json"
        response = requests.request("GET", card_info_url, headers=headers)
        if response.status_code == 200:
            json = response.json()
        card_info_url = f"https://basket-{num}.wbbasket.ru/vol{article[:2]}/part{article[:4]}/{article}/info/ru/card.json"
        response = requests.request("GET", card_info_url, headers=headers)
        if response.status_code == 200:
            json = response.json()
    else:
        for i in range(1, 15):
            current_num = str(i)  # подумать как оптимизировать выбор числа
            if int(current_num) < 10:
                current_num = f"0{current_num}"

            card_info_url = f"https://basket-{current_num}.wbbasket.ru/vol{article[:4]}/part{article[:6]}/{article}/info/ru/card.json"  # Ссылка с характеристиками товара по артикулу
            response = requests.request("GET", card_info_url, headers=headers)
            if response.status_code == 200:
                basket_numbers.append(current_num)
                json = response.json()
            card_info_url = f"https://basket-{num}.wbbasket.ru/vol{article[:2]}/part{article[:4]}/{article}/info/ru/card.json"
            response = requests.request("GET", card_info_url, headers=headers)
            if response.status_code == 200:
                json = response.json()

    with open("data/card_datail.txt", "w", encoding="utf-8") as fl:
        data = ""
        isCertificateVerified = json["certificate"]["verified"]
        contents = json["contents"]
        description = json["description"]
        data += f"Сертификат подтвержден - {isCertificateVerified}\n"
        data += f"Полное название - {contents}\n"
        data += f"Описание - {description}\n"
        for grouped_option in json["grouped_options"]:
            group_name = grouped_option["group_name"]
            for options in grouped_option["options"]:
                option_name = options["name"]
                option_value = options["value"]
                data += f"Название группы Характеристик - {group_name}\nНазвание характеристики - {option_name} и Значение - {option_value}\n"

        name = json["imt_name"]
        data += f"Короткое название - {name}\nДополнительные характеристики\n"
        for opt in json["options"]:
            opt_name = opt["name"]
            opt_value = opt["value"]
            data += f"Название - {opt_name} и Значние - {opt_value}\n"

        subj_name = json["subj_name"]
        subj_root_name = json["subj_root_name"]
        vendor_code = json["vendor_code"]
        data += f"Название предмета - {subj_name}\n"
        data += f"Название категории - {subj_root_name}\n"
        data += f"Код вендора - {vendor_code}"
        fl.write(data)
        fl.close()

# pprint(parse_card_detail("6170053"))
# with open("feedbacks.txt", "w") as file:
#     # Перенаправляем вывод функции в файл
#     pprint(parse_feedback("4923366"), stream=file)
# num = "01"
# article = "6170053"
# pprint(parse_price_stats(article))
parse_good("6170053")
