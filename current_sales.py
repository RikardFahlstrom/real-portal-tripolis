import datetime
import hashlib
import random
import string
from dataclasses import dataclass
from typing import List
import time

import pandas as pd
import requests

from utils import load_config_file

TRIPOLIS_ADDRESSES = [
    'Väderkvarnsgatan 36',
    'Väderkvarnsgatan 38A',
    'Väderkvarnsgatan 38B',
    'Väderkvarnsgatan 38C',
    'Väderkvarnsgatan 40',
    'Frodegatan 10A',
    'Frodegatan 10B',
    'Frodegatan 10C',
    'Norrtäljegatan 9A',
    'Norrtäljegatan 9B',
    'Norrtäljegatan 9C',
]


@dataclass
class ListObject:
    address: str
    list_price: int
    rooms: int
    living_area: int
    published: datetime.date
    url: str


def main_current_sales():
    configs = load_config_file()
    api_url = create_request_url(configs['booli']['api_caller'], configs['booli']['api_key'], area_id='386690')
    r = request_listings(api_url)
    assert r.ok

    listings = r.json()['listings']

    matched_listings: List = []

    for listing in listings:
        address = listing.get('location', {}).get('address', {}).get('streetAddress')

        if check_if_tripolis_apartment(address):
            matched_listings.append(
                ListObject(
                    address=address,
                    list_price=int(listing.get('listPrice', 0)),
                    rooms=int(listing.get('rooms', 0)),
                    living_area=int(listing.get('livingArea', 0)),
                    published=datetime.datetime.strptime(listing.get('published'), "%Y-%m-%d %H:%M:%S").date(),
                    url=str(listing.get('url'))
                )
            )

    pd.DataFrame(matched_listings).to_excel('output_files/tripolis_for_sale.xlsx', index=False, freeze_panes=(1, 0))


def create_request_url(api_callerid: str, api_key: str, area_id: str) -> str:
    global time, output
    callerId = api_callerid
    key = api_key
    time = str(time.time())
    unique = str(''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16)))
    hashstr = hashlib.sha1((callerId + time + key + unique).encode('utf-8')).hexdigest()
    query_type = 'listings'
    areaId = area_id
    offset = '0'
    limit = str(500)
    object_type = "lägenhet"

    return str("https://api.booli.se/" +
                     query_type + "?q=" + areaId +
                     "&callerId=" + callerId +
                     "&time=" + time +
                     "&unique=" + unique +
                     "&hash=" + str(hashstr) +
                     "&limit=" + limit +
                     "&offset=" + offset +
                     "&objectType=" + object_type)


def request_listings(api_url: str):
    return requests.get(api_url)


def check_if_tripolis_apartment(adress: str):
    if adress in TRIPOLIS_ADDRESSES:
        return True


if __name__ == "__main__":
    main_current_sales()
