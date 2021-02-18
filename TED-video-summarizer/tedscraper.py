import urllib
from urllib.request import urlopen
from bs4 import BeautifulSoup


def get_ted_summary(title):
    url = search_tedsummaries(title)
    html = urlopen(url).read()
    soup = BeautifulSoup(html, features="html.parser")

    # kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)

    l = text.splitlines()
    sum_text = l[l.index('Summary')+1:l.index('My Thoughts')]

    summary = ' '.join(sum_text)
    return summary
    
def search_tedsummaries(title):
    
    if '|' in title:
        title = title.split('|')[0]
        
    query = urllib.parse.quote(title)
    search_url = 'https://tedsummaries.com/?s=' + query
    html = urlopen(search_url).read()
    soup = BeautifulSoup(html, features="html.parser")
    
    links = []
    for link in soup.findAll('a', {"rel": "bookmark"}):
        links.append(link.get('href'))
        
    if len(links) == 0:
        print("Sorry, no summary could be found on tedsummaries.com")
    else:
        return(links[1])