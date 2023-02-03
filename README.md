# Spider

This Spider is a web-crawler uses techniques similar to OWASP ZAP. It has the ability to crawl a website in-depth and find all the URL(s)/Path(s) with the help of BeautifulSoup. This tool is under development right now and might crash while processing, print unexpected errors etc. Any contribute and improvement is welcome and appreciated.


Install (way 1)
===============
If you are lazy and do not want to run several commands on your terminal, or you do not want to download some unnecessary files, this one command alone will do everything necessary for you:
```sh
curl https://raw.githubusercontent.com/bera-neser/Spider/master/setup.py | python3
```

Install (way 2)
===============
If you have no problem with cloning the whole project and want to know what's happening behind the scenes:
```sh
git clone https://github.com/bera-neser/Spider.git
cd Spider
python3 -m venv venv - [Optional but Recommended]
source venv/bin/activate - [Optional but Recommended]
```

if you did run the last two commands (which is recommended):
```sh
pip install -r requirements.txt
```

if you did not run the last two commands, or your <code>pip</code> command reference to <code>pip2</code>:
```sh
pip3 install -r requirements.txt
```

Use [Docker](https://docs.docker.com/get-docker/) (way 3)
===============
```sh
git clone https://github.com/bera-neser/Spider.git
cd Spider
docker build -t spider .

# usage ->  docker run --rm spider [-h] -U URL [-O FILE] [-T TIMEOUT] [-S] [-C]

docker run --rm spider --help
docker run --rm spider -U example.com

```


Usage
=====
First, you should activate the virtual environment (if you did not make one and installed the packages globally on your system, or did it already in the installing stage, skip this step):
```sh
source venv/bin/activate
```

And then you can use the tool according to its usage manual:
```
usage: spider.py [-h] -u URL [-o FILE] [-t TIMEOUT] [-s] [-c] [-x] [-r]

Scrape websites to find every URL in it recursively.

options:
  -h, --help  show this help message and exit
  -u URL      The main URL that will be crawled
  -o FILE     The output file of the found URLs. default=<URL>.txt
  -t TIMEOUT  Set timeout for a request. default=3
  -s          Enables the scraping of inline text of tags like; "<p>", "<h1>", "<li>" etc.
  -c          Enables the scraping of HTML Comments
  -x          Enables the scraping of sitemap.xml
  -r          Enables the scraping of robots.txt

Examples:
[+] python3 spider.py -u example.com
[+] python3 spider.py -u example.com -s -c -x -r
[+] python3 spider.py -u example.com -t 5
[+] python3 spider.py -u example.com -o example
```

Note: if you want to scrape the <code>sitemap.xml</code>, you must download the <code>lxml parser</code>:
```sh
pip install lxml
```

Known Issues
==========================
* If you see <b>SyntaxError</b> similar to the one below when you run the script, you are probably using <code>python2</code> instead of <code>python3</code> or did not activate the virtual environment. Please make sure you have installed and using <code>python3</code>.
```
File "spider.py", line 15
  def add_http(url: str) -> str:
                  ^
SyntaxError: invalid syntax
```

* If you see <b>ModuleNotFoundError</b> similar to the one below when you run the script, you probably did not activate the virtual environment on your terminal. Please make sure you run <code>source venv/bin/activate</code> before running the script.
```
Traceback (most recent call last):
  File "/Users/John/spider.py", line 6, in <module>
    import tld
ModuleNotFoundError: No module named 'tld'
```

Warning(s) for Development
==========================
* If you have Pylance installed on your VS Code, you should set the "typeCheckingMode" feature to "off". Otherwise it will throw non-sense type issues errors assuming some variables have the value "None" when they are not. (Like: '"UnicodeDammit" is unknown import symbol.' or, '"parsed_url" is not a known member of "None".')
