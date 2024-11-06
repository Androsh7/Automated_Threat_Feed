Three methods:
```
import urllib.request

url = "http://example.com"
response = urllib.request.urlopen(url)
html = response.read().decode("utf-8")
print(html)
```

```
import requests

url = "http://example.com"
response = requests.get(url)
html = response.text
print(html)
```

```
from bs4 import BeautifulSoup

html = ...  # retrieve HTML content using urllib or requests
soup = BeautifulSoup(html, "html.parser")

# Find all <a> tags with href attribute
links = soup.find_all("a", href=True)
for link in links:
    print(link.get("href"))
```