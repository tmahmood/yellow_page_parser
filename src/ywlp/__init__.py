import asyncio
import csv
import json
from asyncio import sleep

import click
import sqlite3

from playwright.async_api import async_playwright

import navigator
import playwright
import platformdirs

from config_dict import ConfigDict

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
    data = []
    async with async_playwright() as p:
        while url:
            doc = await navigator.get_doc(cfg, p, url, 'restaurants')
            headers = doc.xpath('//div[@class="search-results organic"]//div[@class="result"]//h2/a')
            for header in headers:
                rr = header.getparent().getparent().xpath('//div[@class="ratings"]')
                d = json.loads(rr[0].attrib['data-tripadvisor'])
                data.append({'name': header.text_content(), 'rating': d['rating'], 'count': d['count']})
            pages = doc.xpath('//a[@class="next ajax-page"]')
            print([k for k in pages])
            try:
                url = pages[0].attrib['href']
                print(f"going to next url: {url}")
                await sleep(5)
                parsed_pages += 1
                if parsed_pages > 5:
                    break
            except IndexError:
                url = None
    with open('output.csv', encoding='utf-8', mode='w') as f:
        writer = csv.DictWriter(f, ['name', 'rating', 'count'])
        for d in data:
            writer.writerow(d)


@click.command()
def find_restaurants_in_city():
    asyncio.run(finding_restaurants_in_city())
