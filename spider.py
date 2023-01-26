# TODO: Analyze and crawl the links/paths are set in "robots.txt" if it's in place.
# TODO: Analyze the "sitemap.xml" to see if there are any new resources.

import sys
import tld
import requests
import argparse
from threading import Thread
from urlextract import URLExtract
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Comment, UnicodeDammit


examples = """
Examples:
[+] python3 spider.py -U example.com
[+] python3 spider.py -U example.com -S -C
[+] python3 spider.py -U example.com -T 5
[+] python3 spider.py -U example.com -O example
"""

parser = argparse.ArgumentParser(
    description="Scrape websites to find every URL in it recursively.",
    epilog=examples,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

parser.add_argument(
    "-U", dest="url", type=str, required=True, help="The main URL that will be crawled"
)
parser.add_argument(
    "-O",
    dest="file",
    type=str,
    help="The output file of the found URLs. default=<URL>.txt",
)
parser.add_argument(
    "-T",
    dest="timeout",
    type=int,
    help="Set timeout for a request. default=3",
)
parser.add_argument(
    "-S",
    action="store_const",
    const=True,
    help='Enables the scraping of inline text of tags like; "<p>", "<h1>", "<li>" etc.',
)
parser.add_argument(
    "-C", action="store_const", const=True, help="Enables the scraping of HTML Comments"
)


# Adding the corresponding scheme to beginning of the URL if not so already
def add_http(url: str) -> str:
    if not url.startswith("http"):
        return (
            tld.get_tld(url, as_object=True, fix_protocol=True).parsed_url.scheme
            + "://"
            + url
        )
    return url


def write_to_file(file, mode: str, message: str, urls: list):
    with open(file, mode) as f:
        f.write(message)
        f.writelines("\n".join(urls))
        f.write("\n")


def crawl_page(url: str, session: requests.Session):
    try:
        print(f"Crawling {url}")
        # Sending a GET request to our target inside the session we created previously
        with session.get(url, headers=HEADERS, timeout=timeout) as r:
            # Extracting the scheme, domain and the path from the URL
            scheme = r.url.split(":")[0]
            netloc = urlparse(url).netloc
            path = urlparse(url).path

            # Perform all the task only if the response is "200 OK"
            if r.status_code == requests.codes.ok:
                # Creating the BeautifulSoup object using the response we got from the target
                soup = BeautifulSoup(
                    UnicodeDammit(
                        r.content, ["UTF-8", "latin-1", "iso-8859-1", "windows-1251"]
                    ).unicode_markup,
                    "html.parser",
                )

                Threads = list()

                # Iterating over the tags in "href" list to fetch the "href" attributes' values
                thread_href = Thread(
                    target=scrape, args=[soup, scheme, netloc, path, href, "href"]
                )
                thread_href.start()
                Threads.append(thread_href)
                # Iterating over the tags in "src" list to fetch the "src" attributes' values
                thread_src = Thread(
                    target=scrape, args=[soup, scheme, netloc, path, src, "src"]
                )
                thread_src.start()
                Threads.append(thread_src)
                # Iterating over the "blockquote" tags to fetch the "cite" attributes' values
                thread_blockquote = Thread(
                    target=scrape,
                    args=[soup, scheme, netloc, path, "blockquote", "cite"],
                )
                thread_blockquote.start()
                Threads.append(thread_blockquote)
                # Iterating over the "form" tags to fetch the "action" attributes' values
                thread_form = Thread(
                    target=scrape, args=[soup, scheme, netloc, path, "form", "action"]
                )
                thread_form.start()
                Threads.append(thread_form)

                # Search for URLs in tags has inline text
                if args.S:
                    thread_text = Thread(target=scrape_inline_text, args=[soup, inline])
                    thread_text.start()
                    Threads.append(thread_text)

                # Iterating over the comments to find any URL
                if args.C:
                    thread_comments = Thread(target=scrape_comments, args=[soup])
                    thread_comments.start()
                    Threads.append(thread_comments)

                for thread in Threads:
                    thread.join()

                # Remove the URL from list "PAGES_TO_CRAWL" and add it to "CRAWLED_PAGES" after finishing scraping
                PAGES_TO_CRAWL.remove(url)
                CRAWLED_PAGES.append(url)
            else:
                # Remove the URL from list "PAGES_TO_CRAWL" if it does not return "200" as a response code
                PAGES_TO_CRAWL.remove(url)
    except ConnectionError:
        # Remove the URL from list "PAGES_TO_CRAWL" if it does not reply to the request
        PAGES_TO_CRAWL.remove(url)
        print(f"Could not connect to '{url}'")
    except requests.exceptions.ReadTimeout:
        # Remove the URL from list "PAGES_TO_CRAWL" if timed out
        PAGES_TO_CRAWL.remove(url)
        print(f"Timed out.")
    except Exception as e:
        # Remove the URL from list "PAGES_TO_CRAWL" if it raises an Exception
        PAGES_TO_CRAWL.remove(url)
        # Print the possible error to the console to inform the user (beta)
        print(f"Exception: {e}")


def scrape(
    soup: BeautifulSoup,
    scheme: str,
    netloc: str,
    path: str,
    tags: "str | list",
    attribute: str,
):
    for tag in soup.find_all(tags):
        link: str = tag.get(attribute)
        if (
            link is None
            or link == ""
            or any(
                x in link
                for x in [
                    "#",
                    "?",
                    "+",
                    "../",
                    "about:",
                    "mailto:",
                    "callto:",
                    "javascript:",
                    "wp-json",
                    "xmlrpc.php",
                ]
            )
        ):
            continue
        elif tld.get_fld(link, fail_silently=True) is None:
            if link.startswith("/"):
                page = f"{scheme}://{netloc}{link}"
            elif path.endswith("/"):
                page = f"{scheme}://{netloc}{path}{link}"
            else:
                page = f"{scheme}://{netloc}{path}/{link}"
            if page.endswith(EXTENSIONS):
                if page not in FOUND_PAGES:
                    FOUND_PAGES.append(page)
                continue
        elif tld.get_fld(link) != domain:
            if link.startswith("//"):
                page = f"{scheme}:{link}"
            else:
                page = link
            if page not in OTHER_URLS:
                OTHER_URLS.append(page)
            continue
        elif link.startswith("//"):
            page = f"{scheme}:{link}"
            if page.endswith(EXTENSIONS):
                if page not in FOUND_PAGES:
                    FOUND_PAGES.append(page)
                continue
        else:
            if not link.startswith("http"):
                page = f"{scheme}://{netloc}{link}"
            else:
                page = link
            if page.endswith(EXTENSIONS):
                if page not in FOUND_PAGES:
                    FOUND_PAGES.append(page)
                continue

        if page not in FOUND_PAGES:
            FOUND_PAGES.append(page)

        if "www." in page and (
            (page in CRAWLED_PAGES or page in PAGES_TO_CRAWL)
            or (page[:-1] in CRAWLED_PAGES or page[:-1] in PAGES_TO_CRAWL)
            or (f"{page}/" in CRAWLED_PAGES or f"{page}/" in PAGES_TO_CRAWL)
            or (
                f'{page.split("www.")[0]}{page.split("www.")[1]}' in CRAWLED_PAGES
                or f'{page.split("www.")[0]}{page.split("www.")[1]}' in PAGES_TO_CRAWL
            )
            or (
                f'{page.split("www.")[0]}{page.split("www.")[1]}/' in CRAWLED_PAGES
                or f'{page.split("www.")[0]}{page.split("www.")[1]}/' in PAGES_TO_CRAWL
            )
            or (
                f'{page.split("www.")[0]}{(page.split("www.")[1])[:-1]}'
                in CRAWLED_PAGES
                or f'{page.split("www.")[0]}{(page.split("www.")[1])[:-1]}'
                in PAGES_TO_CRAWL
            )
        ):
            continue
        elif not "www." in page and (
            (page in CRAWLED_PAGES or page in PAGES_TO_CRAWL)
            or (page[:-1] in CRAWLED_PAGES or page[:-1] in PAGES_TO_CRAWL)
            or (f"{page}/" in CRAWLED_PAGES or f"{page}/" in PAGES_TO_CRAWL)
            or (
                f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}'
                in CRAWLED_PAGES
                or f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}'
                in PAGES_TO_CRAWL
            )
            or (
                f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}/'
                in CRAWLED_PAGES
                or f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}/'
                in PAGES_TO_CRAWL
            )
            or (
                f'{"".join(page.partition("//")[0:2])}www.{("".join(page.partition("//")[2:]))[:-1]}'
                in CRAWLED_PAGES
                or f'{"".join(page.partition("//")[0:2])}www.{("".join(page.partition("//")[2:]))[:-1]}'
                in PAGES_TO_CRAWL
            )
        ):
            continue

        PAGES_TO_CRAWL.append(page)


def scrape_inline_text(soup: BeautifulSoup, tags: list):
    extractor = URLExtract()

    for tag in soup.find_all(tags):
        if not tag.string is None:
            for url in extractor.find_urls(tag.string):
                if tld.get_fld(url, fail_silently=True) == domain:
                    if url not in FOUND_PAGES:
                        FOUND_PAGES.append(url)
                else:
                    if url not in OTHER_URLS:
                        OTHER_URLS.append(url)


def scrape_comments(soup: BeautifulSoup):
    extractor = URLExtract()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        for url in extractor.find_urls(comment):
            if tld.get_fld(url, fail_silently=True) == domain:
                if url not in FOUND_PAGES:
                    FOUND_PAGES.append(url)
            else:
                if url not in OTHER_URLS:
                    OTHER_URLS.append(url)


def main():
    try:
        # Create a Session and iterate over the list until none left
        with requests.Session() as session:
            while len(PAGES_TO_CRAWL) != 0:
                crawl_page(PAGES_TO_CRAWL[0], session)

        print("\nCrawling Done.")

        # Write the found pages to the output file
        if len(FOUND_PAGES) != 0:
            write_to_file(
                output_file, "w", f"{len(FOUND_PAGES)} URL(s) found:\n", FOUND_PAGES
            )

        if len(OTHER_URLS) != 0:
            write_to_file(
                output_file,
                "a",
                f"{len(OTHER_URLS)} URL(s) found from other domains:\n",
                OTHER_URLS,
            )

        print(
            f"{len(FOUND_PAGES) + len(OTHER_URLS)} found URL has been written to {output_file}"
        )
    except KeyboardInterrupt:
        # If the user decided to stop the program, write the found pages until that point to the output file
        if len(FOUND_PAGES) != 0 or len(OTHER_URLS) != 0:
            print(f"\nWriting to {output_file} and exitting...")

        if len(FOUND_PAGES) != 0:
            write_to_file(
                output_file, "w", f"{len(FOUND_PAGES)} URL(s) found:\n", FOUND_PAGES
            )

        if len(OTHER_URLS) != 0:
            write_to_file(
                output_file,
                "a",
                f"{len(OTHER_URLS)} URL(s) found from other domains:\n",
                OTHER_URLS,
            )
        sys.exit("\nGoodbye..")


# List for the new pages
PAGES_TO_CRAWL = list()

# List of the crawled pages
CRAWLED_PAGES = list()

# List of found pages
FOUND_PAGES = list()

# URLs those are from different host
OTHER_URLS = list()

# Tags to find in a page
href = ["a", "base", "link"]
src = ["audio", "embed", "frame", "iframe", "input", "script", "img", "video"]
inline = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]

# Extensions that we do not want to scrape, just adding to the "FOUND_PAGES" list
EXTENSIONS = (
    ".apng",
    ".avi",
    ".avif",
    ".bmp",
    ".cur",
    ".css",
    ".gif",
    ".ico",
    ".jfif",
    ".jpg",
    ".jpeg",
    ".js",
    ".mov",
    ".mpeg-1",
    ".mpeg-2",
    ".mpeg-4",
    ".mp3",
    ".mp4",
    ".pdf",
    ".pjpeg",
    ".pjp",
    ".png",
    ".svg",
    ".tif",
    ".tiff",
    ".wav",
    ".webp",
    ".xml",
)

# Setting some headers so the request looks more like coming from a browser
HEADERS = {
    "Accept": "text/html",
    "Accept-Language": "en-GB,en",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "3600",
    "DNT": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:99.0) Gecko/20100101 Firefox/99.0",
}

if __name__ == "__main__":
    args = parser.parse_args()

    url = add_http(args.url)
    domain = tld.get_fld(url)
    output_file = f"{domain}.txt"
    timeout = 3

    if args.file:
        output_file = f"{args.file}.txt"

    if args.timeout:
        timeout = args.timeout

    # Add the URL taken from user to the list of links will be crawled
    PAGES_TO_CRAWL.append(url)

    main()
