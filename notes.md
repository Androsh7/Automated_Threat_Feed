# Step 0 Data sources:
## Google
- Google News allows for an RSS version which gives a simplified view:
- google.news.com/rss
- you can add queries like this: `?q=cyber`
## hackernews
- https://thehackernews.com/news-sitemap.xml
# Step 1 Getting Website Data
## Three methods (yeah I used AI for these, sue me):
### urllib library
```
import urllib.request

url = "http://example.com"
response = urllib.request.urlopen(url)
html = response.read().decode("utf-8")
print(html)
```
### requests library
```
import requests

url = "http://example.com"
response = requests.get(url)
html = response.text
print(html)
```
### Beautiful Soup library (bs4) [DOCS](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- works alongside of a HTML or XML parser
- Converts a HTML document into a tree with the following objects: Tag, NavigableString, BeautifulSoup, and Comment
```
from bs4 import BeautifulSoup

html = ...  # retrieve HTML content using urllib or requests
soup = BeautifulSoup(html, "html.parser")

# Find all <a> tags with href attribute
links = soup.find_all("a", href=True)
for link in links:
    print(link.get("href"))
```
## Method for grabbing data
- use urllib library to grab data
- use lxml to parse data