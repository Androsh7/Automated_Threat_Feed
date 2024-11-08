import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime
from datetime import timedelta
import pytz
import json
import re

'''
https://github.com/Androsh7/Automated_Threat_Feed

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
urllist = [
    'https://thehackernews.com/news-sitemap.xml',
    'https://cyberscoop.com/post-sitemap7.xml',
]


news_cutoff = datetime.now() - timedelta(hours= 8) # Tweak this figure to adjust the recency of the threat feed
tz = pytz.timezone('America/Los_Angeles')

# this iterates through the urllist and grabs all links for sites within the cuttoff time
link_list = []

# collects all article links from urllist
for news_site in urllist:
    r = requests.get(news_site)
    xml = r.text
    soup = BeautifulSoup(xml, "lxml")
    
    try:
        xml_soup = soup.findAll('url')
    except:
        print("ERROR GRABBING SITE BLOCKS, ABORTING OPERATION")
        continue
    
    link_count = 0
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
        link_count += 1
    print("Found", link_count, "articles on", news_site)

# quit if no articles found
if len(link_list) == 0:
    print("No articles found, aborting")
    exit()

# this grabs the body of the article and adds it to the link list
link_count = 1
with open("current_threat_feed.txt", "w") as file:
    for link in link_list:
        print("Summarizing article {}/{}".format(link_count, len(link_list)))
        html = requests.get(link[0], allow_redirects=True)
        soup = BeautifulSoup(html.content, "html.parser") # this gives a warning that should be ignored
        raw_data = soup.find_all("p") # this grabs all of the html with the <p> </p> tag, essentially the meat and potatoes of the article
        
        # remove html tags
        stripped_html = remove_html_tags(str(raw_data))

        # NOTE: this uses the KoboldCpp to run model and Kobold API for summarization
        # see KoboldCpp at https://github.com/LostRuins/koboldcpp
        # see KoboldCpp web API at https://lite.koboldai.net/koboldcpp_api
        # uses the unsloth.Q4_K_M.gguf model from https://huggingface.co/raaec/llama3.1-8b-instruct-summarize-q4_k_m
        payload = {
            "prompt" : stripped_html + ". Summary of the article that is a MAXIMUM of 3 sentences:", # this is the actual AI prompt, adjust as needed
            "temperature" : 0.2,
            "top_p" : 0.9,
            "max_content_length" : 2048,
            "max_length" : 256,
            "n" : 1,
        }
        #print(payload)
        try:
            r = requests.post('http://localhost:5001/api/v1/generate', data=json.dumps(payload))
        except:
            print("CRITICAL ERROR REACHING LLM at http://localhost:5001/api/v1/generate")
            exit()
        json_data = r.json()
        link.append(json_data["results"][0]["text"].strip(", [].")) # mostly formatting here since the Kobold API returns a lot of json with response parameters
        
        # print the summaries live
        #print('-' * 10, link[2], "-" , link[1])
        #print(link[3], "\n")
        
        file.write("{} - {}\n\n{}\n{}\n".format(link[2], link[1], link[3], link[0]) + "-" * 20 + "\n") # formatting for output
        link_count += 1
print("Finished writing" + str(link_count) + "Summaries to" + "current_threat_feed.txt")
