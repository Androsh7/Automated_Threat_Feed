import urllib
import urllib.request
import lxml

url = "https://thehackernews.com/news-sitemap.xml"
response = urllib.request.urlopen(url)
html = response.read().decode("utf-8")
print(html)