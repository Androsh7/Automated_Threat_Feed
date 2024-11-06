import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
import pytz

from llama_cpp import Llama

llm = Llama.from_pretrained(
	repo_id="dabr1/Llama-3.1-8B-Lexi-Uncensored_V2-Q4_0_4_8.gguf",
	filename="Llama-3.1-8B-Lexi-Uncensored_V2-Q4_0_4_8.gguf",
)

'''
https://github.com/Androsh7/python_web_scraper

MIT License

Copyright (c) 2024 Androsh7

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

# this is a list of all urls to be searched along with the required XML locations
# format: url, news_block_location, news_title_location, news_link_location, news_pub_date_location, news_pub_date_format
urllist = [
    ['https://thehackernews.com/news-sitemap.xml', '{http://www.sitemaps.org/schemas/sitemap/0.9}url', '{http://www.google.com/schemas/sitemap-news/0.9}news/{http://www.google.com/schemas/sitemap-news/0.9}title' , '{http://www.sitemaps.org/schemas/sitemap/0.9}loc', '{http://www.google.com/schemas/sitemap-news/0.9}news/{http://www.google.com/schemas/sitemap-news/0.9}publication_date', '%Y-%m-%dT%H:%M:%S%z']
    #,['https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q=cyber', 'channel/item', 'title' ,'link', 'pubDate', '%a, %d %b %Y %H:%M:%S %Z']
]

news_cutoff = datetime.now() - timedelta(hours= 24)
tz = pytz.timezone('America/Los_Angeles')

# this iterates through the urllist and grabs all links for sites within the cuttoff time
link_list = []
for news_site in urllist:
    response = requests.get(news_site[0])
    xml = response.text
    root = ET.fromstring(xml)
    for child in root.findall(news_site[1]):
        pub_date = child.find(news_site[4]).text # gets the publication date for the article
        pub_date_std = datetime.strptime(pub_date, news_site[5]) # converts date format to datetime object
        
        # quits if news is past cutoff date
        if (pub_date_std.astimezone(tz) < news_cutoff.astimezone(tz)):
            continue
        title = child.find(news_site[2]).text # gets the title for the article
        url = child.find(news_site[3]).text # gets the url for the article
        link_list.append([url, title, pub_date_std]) # adds the url, title, pubdate to the link_list

# this grabs the body of the article and adds it to the link list
for link in link_list:
    html = requests.get(link[0], allow_redirects=True)
    soup = BeautifulSoup(html.content, "html.parser")
    link.append(soup.find_all("p"))
    print(link[0], link[1], link[2], link[3])
    print("-" * 20)