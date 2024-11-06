import asyncio
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


class RSSCrawler:
    """
    A class to asynchronously crawl a website and find RSS or Atom feeds.
    Includes methods for analyzing common paths, sitemaps, and content negotiation.
    """

    def __init__(self, max_depth=2):
        """
        Initializes the RSSCrawler instance.

        Args:
            max_depth (int): Maximum depth to crawl the website.
        """
        # Keeps track of visited URLs to prevent duplicate visits.
        self.visited_urls = set()
        # Stores found RSS feeds as a dictionary with titles as keys and URLs as values.
        self.rss_feeds = {}
        self.max_depth = max_depth
        self.common_feed_paths = [
            "/rss",
            "/feed",
            "/feeds",
            "/atom.xml",
            "/rss.xml",
        ]
        # Common paths for sitemap.
        self.sitemap_paths = ["/sitemap.xml"]

    async def fetch(self, session, url, accept_header=None):
        """
        Fetches content from a given URL using aiohttp.

        Args:
            session (aiohttp.ClientSession): The current HTTP session.
            url (str): The URL to fetch.
            accept_header (str, optional): The Accept header to send with the request.

        Returns:
            tuple: A tuple containing the content type ('xml' or 'html') and the response content as a string.
        """
        headers = {"Accept": accept_header} if accept_header else {}
        try:
            async with session.get(url, headers=headers, timeout=20) as response:
                if response.status == 200:
                    content_type = response.headers.get("Content-Type", "")
                    if "xml" in content_type:
                        return "xml", await response.text()
                    else:
                        return "html", await response.text()
        except Exception as e:
            print(f"Failed to fetch {url} (Error: {e})")
        return None, None

    async def find_rss_links(self, html, base_url):
        """
        Extracts RSS/Atom feed links from the HTML content.

        Args:
            html (str): The HTML content to parse.
            base_url (str): The base URL to resolve relative URLs.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Find <link> tags with RSS/Atom types
        for link in soup.find_all(
            "link", type=["application/rss+xml", "application/atom+xml"]
        ):
            title = link.get("title", "RSS Feed")
            href = link.get("href")
            full_url = urljoin(base_url, href)
            if full_url not in self.rss_feeds:
                self.rss_feeds[title] = full_url

        # Find <a> tags with relevant keywords in href
        for a_tag in soup.find_all("a", href=True):
            if any(
                keyword in a_tag["href"].lower() for keyword in ["rss", "feed", "atom"]
            ):
                title = a_tag.get_text() or "RSS Feed Link"
                full_url = urljoin(base_url, a_tag["href"])
                if full_url not in self.rss_feeds:
                    self.rss_feeds[title] = full_url

        # Find meta tags indicating RSS feeds
        for meta in soup.find_all("meta", attrs={"name": "rss-feed"}):
            href = meta.get("content")
            full_url = urljoin(base_url, href)
            if full_url not in self.rss_feeds:
                self.rss_feeds["Meta RSS Feed"] = full_url

    async def check_common_feed_paths(self, session, base_url):
        """
        Checks common paths on the website for potential RSS feeds.

        Args:
            session (aiohttp.ClientSession): The current HTTP session.
            base_url (str): The base URL to resolve common paths.
        """
        tasks = []
        for path in self.common_feed_paths:
            feed_url = urljoin(base_url, path)
            tasks.append(self.check_feed_path(session, feed_url))
        await asyncio.gather(*tasks)

    async def check_feed_path(self, session, url):
        """
        Checks if a specific URL points to a valid RSS/Atom feed.

        Args:
            session (aiohttp.ClientSession): The current HTTP session.
            url (str): The URL to check.
        """
        _, content = await self.fetch(session, url)
        if content:
            try:
                # Validate XML format
                ET.fromstring(content)
                if url not in self.rss_feeds.values():
                    self.rss_feeds["Guessed RSS Feed"] = url
            except ET.ParseError:
                # Ignore non-XML content
                pass

    async def analyze_sitemap(self, session, base_url):
        """
        Analyzes the sitemap to find potential RSS feed URLs.

        Args:
            session (aiohttp.ClientSession): The current HTTP session.
            base_url (str): The base URL to resolve sitemap paths.
        """
        for path in self.sitemap_paths:
            sitemap_url = urljoin(base_url, path)
            content_type, content = await self.fetch(session, sitemap_url)
            if content_type == "xml" and content:
                try:
                    root = ET.fromstring(content)
                    for element in root.iter():
                        if element.tag.endswith("loc"):
                            link = element.text
                            if "rss" in link or "feed" in link:
                                if link not in self.rss_feeds.values():
                                    self.rss_feeds["Sitemap RSS Feed"] = link
                except ET.ParseError:
                    # Ignore malformed XML
                    pass

    async def negotiate_feed_content(self, session, base_url):
        """
        Tries content negotiation by requesting the base URL with an RSS-specific Accept header.

        Args:
            session (aiohttp.ClientSession): The current HTTP session.
            base_url (str): The base URL to send the request to.
        """
        _, content = await self.fetch(
            session, base_url, accept_header="application/rss+xml"
        )
        if content:
            try:
                ET.fromstring(content)  # Validate as RSS feed
                if base_url not in self.rss_feeds.values():
                    self.rss_feeds["Content Negotiated RSS Feed"] = base_url
            except ET.ParseError:
                # Ignore non-XML content
                pass

    async def crawl(self, url, depth=0):
        """
        Recursively crawls a website to find RSS feeds up to a specified depth.

        Args:
            url (str): The starting URL for the crawl.
            depth (int): The current depth of the crawl.
        """
        if url in self.visited_urls or depth > self.max_depth:
            return
        self.visited_urls.add(url)

        async with aiohttp.ClientSession() as session:
            content_type, html = await self.fetch(session, url)
            if html:
                if content_type == "html":
                    # Extract RSS links and search known paths
                    await self.find_rss_links(html, url)

                    # Check common paths and sitemap only at the initial depth
                    if depth == 0:
                        await self.check_common_feed_paths(session, url)
                        await self.analyze_sitemap(session, url)
                        await self.negotiate_feed_content(session, url)

                    # Crawl linked pages if not at max depth
                    if depth < self.max_depth:
                        soup = BeautifulSoup(html, "html.parser")
                        tasks = []
                        for a_tag in soup.find_all("a", href=True):
                            link = urljoin(url, a_tag["href"])
                            if (
                                urlparse(link).netloc == urlparse(url).netloc
                                and link not in self.visited_urls
                            ):
                                tasks.append(self.crawl(link, depth + 1))
                        await asyncio.gather(*tasks)

    def get_rss_feeds(self):
        """
        Returns the dictionary of found RSS feeds.

        Returns:
            dict: A dictionary of RSS feed titles and URLs.
        """
        return self.rss_feeds


async def main(start_url, max_depth=2):
    """
    Main function to initiate the RSS crawling process.

    Args:
        start_url (str): The URL to start crawling from.
        max_depth (int): The maximum depth for crawling.

    Returns:
        dict: A dictionary of RSS feeds found during the crawl.
    """
    crawler = RSSCrawler(max_depth=max_depth)
    await crawler.crawl(start_url)
    return crawler.get_rss_feeds()


if __name__ == "__main__":
    start_url = input("Enter the starting URL: ")
    depth = int(input("Enter the max depth for crawling: "))
    feeds = asyncio.run(main(start_url, max_depth=depth))
    print("Found RSS Feeds:")
    for title, url in feeds.items():
        print(f"{title}: {url}")
