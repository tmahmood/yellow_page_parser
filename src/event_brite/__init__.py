import asyncio
import csv
import json
import typing
from asyncio import sleep
from typing import List

import click
import playwright.async_api

from lxml.html import HtmlElement
from playwright.async_api import async_playwright

import navigator

from config_dict import ConfigDict
from navigator import get_logger

LOCATION = [
    'PHILADELPHIA',
]

BASE_URL = 'https://www.eventbrite.com/d/united-states/all-events/#search'


def load_state_links():
    state_dict = {}
    with open('states', 'r', encoding='utf-8') as fp:
        for line in fp:
            k, v = line.split(' ')
            state_dict[k] = v.strip()
    return state_dict


async def finding_events():
    # state_dict = load_state_links()
    cfg = ConfigDict()
    url = BASE_URL
    parsed_pages = 0
    hotel_data = []
    logger = get_logger('eventbrite', 'DEBUG')
    async with async_playwright() as p:
        nav:navigator.Navigator = navigator.Navigator(p, headless=False)
        await nav.goto(BASE_URL)
        input_location: playwright.async_api.ElementHandle = await nav.wait_for('#location-autocomplete')
        await input_location.click()
        await input_location.fill(LOCATION[0])
        await sleep(1)
        await input_location.press("enter")
        elements: typing.List[playwright.async_api.ElementHandle] = await nav.wait_for("//section[@class='event-card-details']", strict=False)
        for element in elements:
            print(await element.inner_text())
    with open('output.csv', encoding='utf-8', mode='w') as f:
        writer = csv.DictWriter(f, ['name', 'rating', 'count'])
        for loaded_json_data in hotel_data:
            writer.writerow(loaded_json_data)


@click.command()
def find_events_in_city():
    asyncio.run(finding_events())
