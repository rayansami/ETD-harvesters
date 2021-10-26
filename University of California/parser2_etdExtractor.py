"""
    This program will go through the url-<Num>.txt files and -
    1. download pdf 
    2. extract metadata from html
"""
import urllib.request
import urllib.response
import urllib.parse
import bs4
import re
from collections import defaultdict
import json
import os
import time
from socket import timeout


base = "https://escholarship.org/"

# Log stuffs
def print_logs(text):
    print(text)
    with open("log.txt",'w',encoding = 'utf-8') as f:
        f.write(text+"\n")
"""
    This module will help keep the op running just incase any URL error occurs
"""
def isETDUrlWorkable(url):
    isWorkable = True
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError as exception:
        print (exception)
        isWorkable = False
    except urllib.error.ContentTooShortError() as exception:
        print (exception)
        isWorkable = False
    except urllib.error.URLError as exception:
        print (exception)
        isWorkable = False
    except timeout: 
        print("==> Timeout")
        isWorkable = False
    
    return isWorkable

"""
    This module will help keep the op running just incase any URL error occurs
"""
def isPDFDownloadUrlWorkable(soup):
    downloadableUrl = getPDFdownloadUrl(soup)
    
    isWorkable = True
    try:
        response = urllib.request.urlopen(downloadableUrl)
    except urllib.error.HTTPError as exception:
        print (exception)
        isWorkable = False
    except urllib.error.ContentTooShortError() as exception:
        print (exception)
        isWorkable = False
    except urllib.error.URLError as exception:
        print (exception)
        isWorkable = False
    except ConnectionResetError as exception:
        print (exception)
        isWorkable = False
    
    return isWorkable

def ifPDFAvailable(soup):
    available = True
    hrefValue = soup.find('a', {"class":"o-download__button"})   
    if hrefValue is None:
        available = False
    
    return available

def getPDFdownloadUrl(soup):
    hrefValue = soup.find('a', {"class":"o-download__button"})['href']    
    downloadableUrl = urllib.parse.urljoin(base, hrefValue)
    return downloadableUrl

# Check if it is a thesis [from breadcrumb]
def isItemThesis(soup):
    isThesis = False
    breacrumbText = soup.find('a', class_="c-breadcrumb-link--active")
    if breacrumbText is None:
        return False # If breadcrumb not exists, return false already!
    
    breacrumbText = breacrumbText.get_text()
    searchDissertations = re.search(r"(Dissertations)", breacrumbText) 
    # print(searchDissertations.group(0))
    if searchDissertations is not None: #and searchDissertations.group(0) == "Dissertations"
        isThesis = True
    #print(isThesis)
    return isThesis

def extractPDF(url,soup):
    # Extract item-id from URL
    itemid = url.split("/")[-1] # Take the last element from the split. Only create folder if it's etd
    #print(url.split("/")[-1])

    # Get the PDF download-able URL
    downloadableUrl = getPDFdownloadUrl(soup)

    # Extract School name
    schoolUri = soup.find('nav', {"class":"c-breadcrumb"}).find_all('li')[1].find('a').get('href') # /uc/ucsb
    schoolName = schoolUri.split("/")[-1]
    #print(schoolName)

    """
        TODO: Download and store the PDF. [Make sure folder with ID exists]        
        etds -> <school_name> -> <itemID[D]> -> itemID.pdf | itemID.json
    """
    # Create directory based on item-id
    directory = 'etds/'+ schoolName +'/'+ itemid + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Download and store pdf to that directory
    fileName = itemid + '.pdf'
    filepath = os.path.join(directory, fileName)    
    urllib.request.urlretrieve(downloadableUrl,filepath) # urllib.request.urlretrieve(source,dest)
    
    print("Successful pdf parsing for:"+itemid)

def extractMetadata(url, soup):
    """    
    Extracting these - 
    title
    author
    advisor
    date
    etd-url
    abstract
    """

    uc_metainfo = defaultdict(dict)

    title = soup.find('h2', class_="c-tabcontent__main-heading")
    date = soup.find('div', class_="c-authorlist__year")
    
    """ Getting Author and Advisor name """
    authorList = soup.find_all('li', {"class":"c-authorlist__begin"})#.find('span').decompose() # First cleanup "Author" text from the dom. 
    if len(authorList): # Handling edge case: if author not present
        for author in authorList: # Cleanup the unwanted bold texts
            author.find('span').decompose()        
    #author = authorList[0].get_text().strip(' ')
    #advisor = authorList[1].get_text().strip(' ')
    
    etdUrl = getPDFdownloadUrl(soup)
    
    # Extracting abstract
    abstract = None
    elementSearchForAbstract = soup.find('div', {"class":"c-tabs__content"}).find_all('details')
    if len(elementSearchForAbstract) >= 1:
        abstract = elementSearchForAbstract[0]
    
    """
        Build dictionary with metadata
    """
    # Title
    if title is not None:
        uc_metainfo['title'] = title.getText().strip('\n')
    else:
        uc_metainfo['title'] = "NaN"
    # Date
    if date is not None:
        uc_metainfo['date'] = date.getText().strip('\n')
    else:
        uc_metainfo['date'] = "NaN"
    # Author
    if len(authorList) >= 1 and authorList[0] is not None:
        uc_metainfo['author'] = authorList[0].get_text().strip(' ')
    else:
        uc_metainfo['author'] = "NaN"
    # Advisor    
    if len(authorList) ==2 and  authorList[1] is not None:
        uc_metainfo['advisor'] = authorList[1].get_text().strip(' ')
    else:
        uc_metainfo['advisor'] = "NaN"
    # Abstract
    if abstract is not None:
        uc_metainfo['abstract'] = abstract.getText().strip('\n')
    else:
        uc_metainfo['abstract'] = "NaN"
    # Etd-url 
    if etdUrl is not None:
        uc_metainfo['etdUrl'] = etdUrl
    else:
        uc_metainfo['etdUrl'] = "NaN"

    #print(uc_metainfo)
    """ 
        Download and store the meta-information
    """
    # Extract item-id from URL
    itemid = url.split("/")[-1] # Take the last element from the split. Only create folder if it's etd
    # Extract School name from breadcrumb
    schoolUri = soup.find('nav', {"class":"c-breadcrumb"}).find_all('li')[1].find('a').get('href') # /uc/ucsb
    schoolName = schoolUri.split("/")[-1]

    # Create directory based on item-id
    directory = 'etds/'+ schoolName +'/'+ itemid + '/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Define filename with item-id
    fileName = itemid + '.txt'
    filepath = os.path.join(directory, fileName)    
    with open(filepath, 'w') as output_file:
        json.dump(uc_metainfo, output_file)        
    print("Successful meta parsing for:"+itemid)
    print("Directory:"+directory)

def extractContents(url):         
    response = urllib.request.urlopen(url)  # opens each link to be parsed
    response = response.read()
    time.sleep(2)  # delays the program
    soup = bs4.BeautifulSoup(response, "html.parser")
    
    # Check If item is thesis & PDF is download-able => then we'll do extraction
    print_logs("Now starting: "+ url)
    if isETDUrlWorkable(url) and isItemThesis(soup) and ifPDFAvailable(soup):
        print_logs("It's thesis")
        if isPDFDownloadUrlWorkable(soup):
            extractPDF(url, soup)
            extractMetadata(url, soup)

if __name__ == '__main__':
    url_directory = 'urls/'    
    #for urlfile in os.listdir(url_directory):
    urlfile = 'url-11.txt' # Change filename here
    print_logs('URL-File Currently Handling: '+ urlfile)
    filepath = os.path.join(url_directory, urlfile) # Make relative path
    text = open(filepath, 'r')
    data = text.readlines()
    for line in data:
        link = line.strip().split('\n') # remove '\n' from the url on each line
        extractContents(link[0])
        #print(link[0])
    
    # print(os.listdir(url_directory)[0])
    """
        Test Intances:
        # Downloadable: "https://escholarship.org/uc/item/2tk4g64t" 
        # Not downloadable: https://escholarship.org/uc/item/14n5g5hw
        # Not Thesis(Book): https://escholarship.org/uc/item/16p2r7wv
        # Index error: https://escholarship.org/uc/item/0003887p
        # Problematic URL: https://escholarship.org/uc/item/01665550 - Skip if gives 400/500

    
    testUrl = "https://escholarship.org/uc/item/01665550" 
    extractContents(testUrl)
    
    for line in list(["https://escholarship.org/uc/item/01665550","https://escholarship.org/uc/item/2tk4g64t"]):
        link = line.strip().split('\n') # remove '\n' from the url on each line
        extractContents(link[0])
    """