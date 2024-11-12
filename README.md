# Automated Threat Feed
This is a python project to automatically query cybernews sites for articles within the last 24 hours, summarize the data with a LLM, and present a single aggregated threat feed that can be then distributed as needed.

## How it works
### Step 0 installing and optimizing your LLM
To get started I installed [KoboldCpp](https://github.com/LostRuins/koboldcpp), the settings will vary however I used the default settings with CuBLAS for GPU Acceleration

For my model I used the 4-bit quantized GGUF model [unsloth.Q4_K_M.gguf](https://huggingface.co/raaec/llama3.1-8b-instruct-summarize-q4_k_m). This is a based on llama3.1 and works well for summarization. If you want you can use other models, however your mileage may vary.
### Step 1 grab links
The program first starts with reading the XML sitemap of various news sites, this is done using the requests library to grab the XML, then the BeautifulSoup library is used to parse the xml data using the lxml parser. This can be seen below:
```
r = requests.get(news_site)
xml = r.text
soup = BeautifulSoup(xml, "lxml")
```
### Step 2 parse site data
The next part is to sort the xml data to find the links, last modified date, and title.
```
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
```
### Step 3 remove old news
The program uses the datetime library to grab the current date and the pytz for timezone localization
```
news_cutoff = datetime.now() - timedelta(hours= 8) # Tweak this figure to adjust the recency of the threat feed
tz = pytz.timezone('America/Los_Angeles')
```
Then the news_cutoff is compared to the last modified date of each article to decide whether or not it can be added
```
  pub_date_std = datetime.strptime(linkdate, '%Y-%m-%dT%H:%M:%S%z') # converts date format to datetime object
  # quits if news is past cutoff date
  if (pub_date_std.astimezone(tz) < news_cutoff.astimezone(tz)):
      continue
```
### Step 4 grab the article text
Before the LLM model can begin to read the article it most get it in a simplified format (no HTML syntax). This is done by isolating only the html `<p>` tags. This is an imperfect solution, however it succeeds in grabbing more than enough data for the LLM to process.
```
html = requests.get(link[0], allow_redirects=True)
soup = BeautifulSoup(html.content, "html.parser") # this gives a warning that should be ignored
raw_data = soup.find_all("p") # this grabs all of the html with the <p> </p> tag, essentially the meat and potatoes of the article

# remove html tags
stripped_html = remove_html_tags(str(raw_data))
```
### Step 5 running the LLM prompt
This program uses [KoboldCpp](https://github.com/LostRuins/koboldcpp) to run the language model and uses the [KoboldCpp API](https://lite.koboldai.net/koboldcpp_api) for prompt submissions.

This is done via a html POST request (via the requests library) of the following JSON:
```
payload = {
    "prompt" : stripped_html + ". Summary of the article that is a MAXIMUM of 3 sentences:", # this is the actual AI prompt, adjust as needed
    "temperature" : 0.2,
    "top_p" : 0.9,
    "max_content_length" : 2048,
    "max_length" : 256,
    "n" : 1,
}

try:
    r = requests.post('http://localhost:5001/api/v1/generate', data=json.dumps(payload))
except:
    print("CRITICAL ERROR REACHING LLM at http://localhost:5001/api/v1/generate")
    exit()
```
### Step 6 the finished product
the program currently writes all of this information to a file "current_threat_feed.txt", however this can be adjusted to print the summary to the console or send the data via mail using [Gmail API](https://developers.google.com/gmail/api/guides) or one of the many other email APIs.
## Limitations
This program relies on a machine that can run an LLM locally, which generally means a graphics card with at least 4gb of VRAM. I personally ran this on a laptop NVIDIA GeForce RTX 3050 6GB. For reference this was able to summarize 6 articles in 3 minutes and 50 seconds. Your mileage may vary when it comes to other devices, as always a less-quantized model will assist in better summarization and allow for more complex instructions.

This program currently suffers from issues with duplicate articles since some of the cybernews sites will write articles on the same topic. This can be solved by running the whole summary through the LLM again to condense it further, though this may result in loss of content or other unintended issues.
