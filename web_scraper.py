import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
import pytz
import json
import re

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

def remove_html_tags(text):
    pattern = re.compile(r'<.*?>')
    return re.sub(pattern, '', text)

# this is a list of all urls to be searched along with the required XML locations
# format: url, news_block_location, news_title_location, news_link_location, news_pub_date_location, news_pub_date_format
urllist = [
    'https://thehackernews.com/news-sitemap.xml',
    'https://cyberscoop.com/post-sitemap7.xml',
]


news_cutoff = datetime.now() - timedelta(hours= 24)
tz = pytz.timezone('America/Los_Angeles')

# this iterates through the urllist and grabs all links for sites within the cuttoff time
link_list = []

for news_site in urllist:
    r = requests.get(news_site)
    xml = r.text
    soup = BeautifulSoup(xml, "lxml")
    
    try:
        xml_soup = soup.findAll('url')
    except:
        print("ERROR GRABBING SITE BLOCKS, ABORTING OPERATION")
        continue
    
    for link in xml_soup:
        # grab url
        try:
            linkstr = link.find('loc').getText('', True)
        except:
            print("ERROR ATTEMPTING TO GRAB URL FROM XML DATA")
            continue
        
        # grab last modified date
        try:
            linkdate = link.find('lastmod').getText('', True)
        except:
            print("ERROR ATTEMPTING TO GRAB LAST MODIFIED DATE FROM XML DATA")
            continue
            
        # grab the title
        try:
            linktitle = link.find('title').getText('', True)
        except:
            # Grab title from url
            linktitle = linkstr.rstrip("/ ").split("/")[-1]
            
        pub_date_std = datetime.strptime(linkdate, '%Y-%m-%dT%H:%M:%S%z') # converts date format to datetime object
        # quits if news is past cutoff date
        if (pub_date_std.astimezone(tz) < news_cutoff.astimezone(tz)):
            continue
        
        link_list.append([linkstr, linkdate, linktitle])
for line in link_list:
    print(line)

# this grabs the body of the article and adds it to the link list
for link in link_list:
    html = requests.get(link[0], allow_redirects=True)
    soup = BeautifulSoup(html.content, "html.parser")
    raw_data = soup.find_all("p")
    
    # remove html tags
    stripped_html = remove_html_tags(str(raw_data))

    payload = {
        "prompt" : stripped_html + ". Summary of the article that is a MAXIMUM of 3 sentences:",
        "temperature" : 0.2,
        "top_p" : 0.9,
        "max_content_length" : 2048,
        "max_length" : 256,
        "n" : 1,
    }
    #print(payload)
    r = requests.post('http://localhost:5001/api/v1/generate', data=json.dumps(payload))
    print('-' * 10, link[2], "-" , link[1])
    json_data = r.json()
    link.append(json_data["results"][0]["text"].lstrip(", ["))
    print(link[3], "\n")

# this will write the automated threat feed to a file