import asyncio
import csv
import json
from asyncio import sleep
from typing import List

import click

from lxml.html import HtmlElement
from playwright.async_api import async_playwright

import navigator

from config_dict import ConfigDict
from navigator import get_logger

CATEGORIES = [
    'restaurants',
]


def load_state_links():
    state_dict = {}
    with open('states', 'r', encoding='utf-8') as fp:
        for line in fp:
            k, v = line.split(' ')
            state_dict[k] = v.strip()
    return state_dict


async def finding_restaurants_in_city():
    # state_dict = load_state_links()
    cfg = ConfigDict()
    url = 'https://www.yellowpages.com/new-york-ny/restaurants?s=average_rating'
    parsed_pages = 0
    hotel_data = []
    logger = get_logger('yellow', 'DEBUG')
    async with async_playwright() as p:
        while url:
            doc = await navigator.get_doc(cfg, p, url, 'restaurants')
            headers = doc.xpath('//div[@class="search-results organic"]//div[@class="result"]//h2/a')
            for header in headers:
                trip_adviser_data: List[HtmlElement] = header.getparent().getparent().xpath('./div[@class="ratings"]')
                logger.info([kk.attrib for kk in trip_adviser_data])
                if 'data-tripadvisor' not in trip_adviser_data[0].attrib:
                    continue
                loaded_json_data = json.loads(trip_adviser_data[0].attrib['data-tripadvisor'])
                logger.info(f"found hotel: {loaded_json_data}")
                hotel_data.append({'name': header.text_content(), 'rating': loaded_json_data['rating'], 'count': loaded_json_data['count']})
            pages = doc.xpath('//a[@class="next ajax-page"]')
            try:
                url = pages[0].attrib['href']
                logger.info(f"going to next url: {url}")
                await sleep(5)
                parsed_pages += 1
                if parsed_pages > 5:
                    break
            except IndexError:
                url = None
    with open('output.csv', encoding='utf-8', mode='w') as f:
        writer = csv.DictWriter(f, ['name', 'rating', 'count'])
        for loaded_json_data in hotel_data:
            writer.writerow(loaded_json_data)


@click.command()
def find_restaurants_in_city():
    asyncio.run(finding_restaurants_in_city())
