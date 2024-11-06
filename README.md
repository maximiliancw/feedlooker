# Feedlooker

FeedLooker is a Python package that helps you find RSS and Atom feeds on any given website. The package asynchronously crawls web pages, extracts feed links, and returns them in an easy-to-use format. Whether you're building a content aggregator, feed reader, or just want to discover feeds, FeedLooker is your go-to tool.

The name "FeedLooker" is a wordplay on "Foot Locker," reflecting the package's ability to "look for feeds" on the web.

[![Build Status](https://img.shields.io/github/actions/workflow/status/maximiliancw/feedlooker/python-package.yml)](https://github.com/maximiliancw/feedlooker/actions)  
[![PyPI version](https://badge.fury.io/py/feedlooker.svg)](https://badge.fury.io/py/feedlooker)

## Features

- **RSS and Atom Feed Detection**: Automatically find RSS and Atom feeds from any webpage.
- **Asynchronous Crawling**: Efficient asynchronous crawling using `asyncio` and `aiohttp`.
- **Sync and Async API**: Supports both synchronous and asynchronous methods to fetch RSS feeds.
- **Depth Control**: Limit the depth to which the crawler explores a site.
- **Handles Common Feed Paths**: Checks common paths like `/rss`, `/feed`, `/atom.xml`, etc.
- **Easy-to-use API**: Simple API to fetch and extract RSS feeds.
- **Excludes Invalid Links**: Skips irrelevant URLs like `mailto:` links, file downloads, and unnecessary query parameters.

## Installation

Feedlooker is available on PyPI. You can install it using `pip`:

```bash
pip install feedlooker
```

## Usage

Feedlooker provides a simple API to find RSS and Atom feeds. Here's how you can use it:

### Synchronous 

```python
from feedlooker import FeedLooker

fl = FeedLooker(max_depth=2)
feeds = fl.get_feeds("https://example.com")
print("Found RSS Feeds:", feeds)
```

### Asynchronous

```python
import asyncio
from feedlooker import FeedLooker

async def main():
    fl = FeedLooker(max_depth=2)
    feeds = await fl.get_feeds_async("https://example.com")
    print("Found RSS Feeds:", feeds)

asyncio.run(main())
```

## How It Works

Feedlooker uses an asynchronous approach to fetch web pages and identify feed links. It looks for the following:

### Included URLs

- `<link>` tags with `type="application/rss+xml"` or `type="application/atom+xml"`.
- `<a>` tags containing keywords like `rss`, `feed`, or `atom` in their `href` attributes.
- `<meta>` tags with `name="rss-feed"`.

The crawler also checks common RSS paths like `/rss`, `/feed`, `/atom.xml` and examines the site's sitemap for additional feed URLs.

### Excluded URLs

Feedlooker automatically skips:

- Links with the `mailto:` scheme.
- File links (e.g., PDFs, images).
- URLs with unnecessary query parameters or fragments (e.g., `?id=123` or `#section`).

## License

Feedlooker is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Contributions to Feedlooker are welcome! Here's how you can contribute:

1. Fork the repository.
2. Create a new branch.
3. Make your changes.
4. Run tests and ensure everything works.
5. Submit a pull request with a description of your changes.

## Acknowledgements

Feedlooker uses the following open-source libraries:

- `aiohttp` – Asynchronous HTTP requests.
- `beautifulsoup4` – Parsing HTML to extract feed links.
- `asyncio` – Asynchronous tasks for concurrent crawling.
