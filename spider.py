import os
import sys
import tld
import requests
import argparse
from threading import Thread
from urlextract import URLExtract
from urllib.parse import urlparse
from bs4 import BeautifulSoup, Comment, UnicodeDammit


# Constants

# List for the new pages
PAGES_TO_CRAWL = list()

# List of the crawled pages
CRAWLED_PAGES = list()

# List of found pages
FOUND_PAGES = list()

# URLs those are from different host
OTHER_URLS = list()

# XML sites
XML_SITES = list()

# List of crawled XML sites
CRAWLED_XMLS = list()

# Tags to find in a page
href = ["a", "base", "link"]
src = ["audio", "embed", "frame", "iframe", "input", "script", "img", "video"]
inline = ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote"]

# Ignore the link if any of the below is in place
IGNORE = [
    "#",
    "?",
    "../",
    "data:",
    "about:",
    "mailto:",
    "callto:",
    "javascript:",
    "wp-json",
    "xmlrpc.php",
    "sitemap.xml",
    ".webmanifest",
    "ios-app://",
    "android-app://",
]

# Extensions that we do not want to scrape, but only adding to the "FOUND_PAGES" list
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
    ".json",
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


def parse_args():
    examples = """
    Examples:
    [+] python3 spider.py -u example.com
    [+] python3 spider.py -u example.com -o example
    [+] python3 spider.py -u example.com -t 5
    [+] python3 spider.py -u example.com -scxr
    """

    parser = argparse.ArgumentParser(
        description="Scrape websites to find every URL in it recursively.",
        epilog=examples,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("-u", dest="url", type=str, required=True, help="The main URL that will be crawled")
    parser.add_argument(
        "-o",
        dest="file",
        type=str,
        help="The output file of the found URLs. default=<URL>.txt",
    )
    parser.add_argument(
        "-t",
        dest="timeout",
        type=int,
        help="Set timeout for a request. default=3",
    )
    parser.add_argument(
        "-s",
        action="store_const",
        const=True,
        help='Enables the scraping of inline text of tags like; "<p>", "<h1>", "<li>" etc.',
    )
    parser.add_argument("-c", action="store_const", const=True, help="Enables the scraping of HTML Comments")
    parser.add_argument("-x", action="store_const", const=True, help="Enables the scraping of sitemap.xml")
    parser.add_argument("-r", action="store_const", const=True, help="Enables the scraping of robots.txt")

    return parser.parse_args()


# Adding the corresponding scheme to beginning of the URL if not so already
def add_http(url: str) -> str:
    if not url.startswith("http"):
        return f"{tld.get_tld(url, as_object=True, fix_protocol=True).parsed_url.scheme}://{url}"
    return url


# Write the found URLs to the output file
def write_to_file(file, mode: str, message: str, urls: list):
    with open(file, mode, encoding="UTF-8") as f:
        f.write(message)
        f.writelines("\n".join(urls))
        f.write("\n")


# Returns a BeautifulSoup object of the given content
def get_soup(content, parser: str):
    return BeautifulSoup(UnicodeDammit(content, ["UTF-8", "latin-1", "iso-8859-1", "windows-1251"]).unicode_markup,parser)


def crawl_page(url: str, session: requests.Session, inline_text, comments, timeout: int = 3):
    try:
        # Sending a GET request to our target inside the session we created previously
        with session.get(url, headers=HEADERS, timeout=timeout) as r:
            # Extracting the scheme, domain and the path from the URL
            scheme = r.url.split(":")[0]
            fld = tld.get_fld(url)
            netloc = urlparse(url).netloc
            path = urlparse(url).path

            # Perform all the task only if the response is "200 OK"
            if r.status_code == requests.codes.ok:
                # Inform the user which page is being crawled
                print(f"Crawling {url}")

                # Creating the BeautifulSoup object using the response we got from the target
                soup = get_soup(r.content, "html.parser")

                Threads = list()

                # Iterating over the tags in "href" list to fetch the "href" attributes' values
                thread_href = Thread(target=scrape, args=[fld, soup, scheme, netloc, path, href, "href"])
                thread_href.start()
                Threads.append(thread_href)

                # Iterating over the tags in "src" list to fetch the "src" attributes' values
                thread_src = Thread(target=scrape, args=[fld, soup, scheme, netloc, path, src, "src"])
                thread_src.start()
                Threads.append(thread_src)

                # Iterating over the "blockquote" tags to fetch the "cite" attributes' values
                thread_blockquote = Thread(target=scrape, args=[fld, soup, scheme, netloc, path, "blockquote", "cite"])
                thread_blockquote.start()
                Threads.append(thread_blockquote)

                # Iterating over the "form" tags to fetch the "action" attributes' values
                thread_form = Thread(target=scrape, args=[fld, soup, scheme, netloc, path, "form", "action"])
                thread_form.start()
                Threads.append(thread_form)

                # Search for URLs in tags has inline text
                if inline_text:
                    thread_text = Thread(target=scrape_inline_text, args=[soup, inline])
                    thread_text.start()
                    Threads.append(thread_text)

                # Iterating over the comments to find any URL
                if comments:
                    thread_comments = Thread(target=scrape_comments, args=[soup])
                    thread_comments.start()
                    Threads.append(thread_comments)

                # Wait other threads to finish
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
        print(f"Timed out on {url}")
    except Exception as e:
        # Remove the URL from list "PAGES_TO_CRAWL" if it raises an Exception
        PAGES_TO_CRAWL.remove(url)
        # Print the possible error to the console to inform the user (beta)
        print(f"Exception: {e}")


def scrape(domain: str, soup: BeautifulSoup, scheme: str, netloc: str, path: str, tags: "str | list", attribute: str):
    for tag in soup.find_all(tags):
        link: str = tag.get(attribute)

        if link is None or link == "" or any(x in link for x in IGNORE):
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

        if not crawled(page):
            PAGES_TO_CRAWL.append(page)


def scrape_inline_text(domain: str, soup: BeautifulSoup, tags: list):
    extractor = URLExtract()

    for tag in soup.find_all(tags):
        if not tag.string is None:
            for url in extractor.find_urls(tag.string):
                if tld.get_fld(url, fail_silently=True) == domain:
                    if not crawled(url):
                        PAGES_TO_CRAWL.append(url)
                elif url not in OTHER_URLS:
                    OTHER_URLS.append(url)


def scrape_comments(domain: str, soup: BeautifulSoup):
    extractor = URLExtract()

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        for url in extractor.find_urls(comment):
            if tld.get_fld(url, fail_silently=True) == domain:
                if not crawled(url):
                    PAGES_TO_CRAWL.append(url)
            elif url not in OTHER_URLS:
                OTHER_URLS.append(url)


def scrape_sitemap(soup: BeautifulSoup):
    for loc in soup.find_all("loc"):
        link: str = loc.string

        if link is None or link == "":
            continue
        if link.endswith(".xml"):
            if not link in CRAWLED_XMLS:
                XML_SITES.append(link)
        elif link.endswith(EXTENSIONS):
            if link not in FOUND_PAGES:
                FOUND_PAGES.append(link)
            continue
        elif not crawled(link):
            PAGES_TO_CRAWL.append(link)


def scrape_robots(url: str, r: requests.Response):
    for path in r.iter_lines():
        if "Disallow:" in path.decode() or "Allow:" in path.decode():
            page = f"{url}{path.decode().split(':')[1].strip()}"
            if not crawled(page):
                PAGES_TO_CRAWL.append(page)


# Returns True if the given page has been crawled before
def crawled(page: str):
    if "www." in page and (
        (page in CRAWLED_PAGES or page in PAGES_TO_CRAWL)
        or (page[:-1] in CRAWLED_PAGES or page[:-1] in PAGES_TO_CRAWL)
        or (f"{page}/" in CRAWLED_PAGES or f"{page}/" in PAGES_TO_CRAWL)
        or (
            f'{page.split("www.")[0]}{page.split("www.")[1]}' in CRAWLED_PAGES
            or
            f'{page.split("www.")[0]}{page.split("www.")[1]}' in PAGES_TO_CRAWL
        )
        or (
            f'{page.split("www.")[0]}{page.split("www.")[1]}/' in CRAWLED_PAGES
            or
            f'{page.split("www.")[0]}{page.split("www.")[1]}/' in PAGES_TO_CRAWL
        )
        or (
            f'{page.split("www.")[0]}{(page.split("www.")[1])[:-1]}' in CRAWLED_PAGES
            or
            f'{page.split("www.")[0]}{(page.split("www.")[1])[:-1]}' in PAGES_TO_CRAWL
        )
    ):
        return True
    elif not "www." in page and (
        (page in CRAWLED_PAGES or page in PAGES_TO_CRAWL)
        or (page[:-1] in CRAWLED_PAGES or page[:-1] in PAGES_TO_CRAWL)
        or (f"{page}/" in CRAWLED_PAGES or f"{page}/" in PAGES_TO_CRAWL)
        or (
            f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}' in CRAWLED_PAGES
            or
            f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}' in PAGES_TO_CRAWL
        )
        or (
            f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}/' in CRAWLED_PAGES
            or
            f'{"".join(page.partition("//")[0:2])}www.{"".join(page.partition("//")[2:])}/' in PAGES_TO_CRAWL
        )
        or (
            f'{"".join(page.partition("//")[0:2])}www.{("".join(page.partition("//")[2:]))[:-1]}' in CRAWLED_PAGES
            or
            f'{"".join(page.partition("//")[0:2])}www.{("".join(page.partition("//")[2:]))[:-1]}' in PAGES_TO_CRAWL
        )
    ):
        return True
    return False


def main():
    if not os.access(os.getcwd(), os.W_OK):
        print("You must have write permission in the directory where you run the script!")
        sys.exit("Exitting.")

    os.makedirs(f'{os.path.dirname(__file__)}/results', exist_ok=True)

    args = parse_args()

    url = add_http(args.url)
    scheme = urlparse(url).scheme
    domain = tld.get_fld(url)
    output_file = f"{os.path.dirname(__file__)}/results/{domain}.txt"
    inline_text = args.s
    comments = args.c
    timeout = 3

    if args.file:
        output_file = f"{args.file}"

    if args.timeout:
        timeout = args.timeout

    try:
        # Create a Session and iterate over the list until none left
        with requests.Session() as session:
            # Crawl the "sitemap.xml" if the user specified switch -x
            if args.x:
                XML_SITES.append(f"{scheme}://{domain}/sitemap.xml")

                while len(XML_SITES) != 0:
                    with session.get(sitemap := XML_SITES[0], headers=HEADERS, timeout=timeout) as r:
                        if r.status_code == requests.codes.ok:
                            print(f"Crawling {sitemap}")
                            soup = get_soup(r.content, "xml")
                            scrape_sitemap(soup)
                        CRAWLED_XMLS.append(sitemap)
                        XML_SITES.remove(sitemap)
            # Crawl the "robots.txt" if the user specified switch -r
            if args.r:
                with session.get(f"{scheme}://{domain}/robots.txt", headers=HEADERS, timeout=timeout) as r:
                    if r.status_code == requests.codes.ok:
                        print(f"Crawling {scheme}://{domain}/robots.txt")
                        scrape_robots(url, r)

            # Add the main URL to the list if not found neither in "sitemap.xml" nor in "robots.txt".
            if not crawled(url):
                PAGES_TO_CRAWL.append(url)

            # Crawl all the pages
            while len(PAGES_TO_CRAWL) != 0:
                crawl_page(PAGES_TO_CRAWL[0], session, inline_text, comments)

        print("\nCrawling Done.")

        if len(FOUND_PAGES) != 0 or len(OTHER_URLS) != 0:
            # Write the found pages to the output file
            if len(FOUND_PAGES) != 0:
                write_to_file(output_file, "w", f"{len(FOUND_PAGES)} URL(s) found:\n", FOUND_PAGES)

            if len(OTHER_URLS) != 0:
                if len(FOUND_PAGES) != 0:
                    write_to_file(output_file, "a", f"\n{len(OTHER_URLS)} URL(s) found from other domains:\n", OTHER_URLS)
                else:
                    write_to_file(output_file, "w", f"{len(OTHER_URLS)} URL(s) found from other domains:\n", OTHER_URLS)

            print(f"{len(FOUND_PAGES) + len(OTHER_URLS)} found URL has been written to {os.path.abspath(output_file)}")
        else:
            print("\nNot found any URL.")
    except KeyboardInterrupt:
        # If the user decided to stop the program, write the found pages until that point to the output file
        if len(FOUND_PAGES) != 0 or len(OTHER_URLS) != 0:
            print(f"\nWriting {len(FOUND_PAGES) + len(OTHER_URLS)} URL(s) into {os.path.abspath(output_file)} and exitting...")

            if len(FOUND_PAGES) != 0:
                write_to_file(output_file, "w", f"{len(FOUND_PAGES)} URL(s) found:\n", FOUND_PAGES)

            if len(OTHER_URLS) != 0:
                if len(FOUND_PAGES) != 0:
                    write_to_file(output_file, "a", f"\n{len(OTHER_URLS)} URL(s) found from other domains:\n", OTHER_URLS)
                else:
                    write_to_file(output_file, "w", f"{len(OTHER_URLS)} URL(s) found from other domains:\n", OTHER_URLS)
        else:
            print("\nNot found any URL.")
        sys.exit("\nGoodbye..")


if __name__ == "__main__":
    main()
