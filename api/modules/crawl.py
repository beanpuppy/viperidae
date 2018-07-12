#!/usr/bin/python3.6
import asyncio
import requests
import gc

from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

class Spider():
    """
    Spider class used for crawl a website based of a provided seed uri.
    Used when website is not in db.

    Example usage:
    >>> uri = 'https://blog.justinduch.com'
    >>> spider  = Spider(uri)
    >>> results = spider.crawl()
    >>> results
    [...]
    """

    cache = {}

    def __init__(self, uri):
        self.uri      = uri
        self.hostname = urlparse(self.uri).netloc

        self.loop = asyncio.get_event_loop()

        # initalise pages with seed link
        self.pages = [{
            'uri'     : self.uri,
            'links'   : self.get_links(self.uri),
            'content' : self.get_content(self.uri)
        }]

        self.crawled  = [self.uri] # uris that have been crawled

    def cache_html(fn):
        def inner(uri):
            cache_key = hash(uri)
            if Spider.cache.get(cache_key): return Spider.cache[cache_key]

            Spider.cache[cache_key] = fn(uri)
            return Spider.cache[cache_key]

        return inner

    @staticmethod
    @cache_html
    def request_page(uri):
        """Gets the html for a page"""
        page  = requests.get(uri)
        html  = BeautifulSoup(page.text, "html.parser")

        return html

    def check_url(self, uri):
        """Checks if the uri is a file or a webpage"""
        url   = urljoin(self.uri, uri) # join in case it's a relative link
        _file = False

        file_extentions = (
            '.jpg', '.png', '.gif', '.pdf', '.docx',
            '.odt', '.doc', '.pptx', '.csv', '.xlsx'
        )

        if '?' in url or '#' in url: return None
        if url.lower().endswith(file_extentions): _file = True
        if url.endswith('/'): url = url[:-1] # strip any trailing backslashes

        return { 'uri': url, 'file': _file }

    def get_content(self, uri):
        """Gets important text from a webpage"""
        html = self.request_page(uri)

        return {
            'title' : html.title.string,
            'text'  : html.get_text()
        }

    def get_links(self, uri):
        """Gets every link in a page"""
        html = self.request_page(uri)

        links = [self.check_url(a['href']) for a in html.find_all('a', href=True) if self.check_url(a['href'])]

        return links

    async def async_get_links(self, uri):
        """Gets every link in a page but asyncronously"""
        html = await self.loop.run_in_executor(ThreadPoolExecutor(), self.request_page, uri)

        links = [self.check_url(a['href']) for a in html.find_all('a', href=True) if self.check_url(a['href'])]

        return links

    async def handle_task(self, task_id, work_queue):
        """Handles the async work for crawling"""
        while not work_queue.empty():
            link = await work_queue.get()
            uri  = link['uri']

            if uri not in self.crawled and not len(self.crawled) > 200:
                self.crawled.append(uri)
                if self.hostname == urlparse(uri).netloc:

                    links = await self.async_get_links(uri)
                    for link in links:
                        if not link['file']: work_queue.put_nowait(link)

                    self.pages.append({
                        'uri'     : uri,
                        'links'   : links,
                        'content' : self.get_content(uri)
                    })
                    print(uri)

    async def crawl(self):
        """Sets the async queue, tasks, etc..."""
        queue = asyncio.Queue()

        [queue.put_nowait(link) for link in self.get_links(self.uri)]

        tasks = [self.handle_task(task_id, queue) for task_id in range(10)]

        await asyncio.wait(tasks)

        # I'm pretty sure Spider.cache causes a memory leak
        # so this just makes sure it is cleared, we don't need it anymore
        del(Spider.cache)
        gc.collect()
        Spider.cache = {}

        return self.pages

if __name__ == "__main__":
    import doctest
    doctest.testmod()