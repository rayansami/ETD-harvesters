"""
    This script goes over database and edit existing records
"""
import mysql.connector
import json
import requests
from bs4 import BeautifulSoup
from io import StringIO
"""
        Change on ETD table:
        Add 
            department -> from xml [Not Available]
            discipline -> from xml [Not Available]
            degree -> from xml [Not Available]
            year -> from xml
            advisor -> from xml

        Modify:
            url -> landing page

        Change on PDFS table:
        Add
            etdid
            url -> pdf url [currently on etds table]
            localrelpath -> calculated from etdid

        Change on Subjects table:
            etdid
            subject -> from xml
"""
    
config = {
    'user': 'rpates',
    'password': 'FriAug2:1316pm',
    'host': 'hawking.cs.odu.edu',
    'database': 'pates_etds'
}
def getEtdIdListFromDB(university):
    # query = "update etds set year= %s, URI= %s, advisor= %s where id= %s"
    # val = (year,landingPageUrl, advisor, etdid)
    # #print(query)
    # mycursor.execute(query, val)

    db_connection = mysql.connector.connect(**config)

    mycursor = db_connection.cursor()
    query = """SELECT id,uri FROM etds where university = '%s'""" % (university)
    #val = (university)
    mycursor.execute(query)
    myresult = mycursor.fetchall()

    db_connection.close()

    return myresult

def extractMetaData(metaEtdId):
    url = "https://escholarship.org/oai?verb=GetRecord&metadataPrefix=oai_dc&identifier="+metaEtdId
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    
    # Subjects
    subjectXml = soup.find_all('dc:subject')
    subjects = []
    if subjectXml:
        for item in subjectXml:
            subjects.append(item.get_text())
            #print(item.get_text())
    
    if not subjects:
        subjects = None

    # Year
    date = soup.find('dc:date')
    year = None
    if date:
        year = date.get_text().split('-')[0]

    # Landing page URL
    url = "https://escholarship.org/uc/item/"+ metaEtdId.replace('qt','')

    # Advisor
    contributors = soup.findAll('dc:contributor')
    advisor = ""
    if contributors:
        for contributor in contributors:
            advisor += contributor.get_text()
            advisor += ';'

    if not advisor:
        advisor = None

    return subjects, year, url, advisor

def updateETDsTable(etdid, year, landingPageUrl, advisor):
    db_connection = mysql.connector.connect(**config)
    mycursor = db_connection.cursor()

    query = "update etds set year= %s, URI= %s, advisor= %s where id= %s"
    val = (year,landingPageUrl, advisor, etdid)
    #print(query)
    mycursor.execute(query, val)
    db_connection.commit()

    mycursor.close()
    db_connection.close()

def calculateRelativePath(etdid):
    firstLevelDir = ''
    number = int(etdid)//10000    
    totalDigits = len(str(number))
    if totalDigits == 1:
        firstLevelDir = '00' + str(number)
    elif totalDigits == 2:
        firstLevelDir = '0' + str(number)
    else:
        firstLevelDir = str(number)

    secondLevelDir = ''
    number = int(etdid)%10000    
    totalDigits = len(str(number))
    if totalDigits == 1:
        secondLevelDir = '000' + str(number)
    elif totalDigits == 2:
        secondLevelDir = '00' + str(number)
    elif totalDigits == 3:
        secondLevelDir = '0' + str(number)
    else:
        secondLevelDir = str(number)

    return firstLevelDir+ '/' + secondLevelDir

def insertIntoPDFsTable(etdid, pdf_download_uri):
    # etdid
    # url -> pdf url [currently on etds table]
    # localrelpath -> calculated from etdid
    localrelpath = calculateRelativePath(etdid)
    db_connection = mysql.connector.connect(**config)
    mycursor = db_connection.cursor()

    sql = "INSERT INTO pdfs (etdid, url, localrelpath) VALUES (%s, %s,%s)"
    val = (etdid, pdf_download_uri, str(localrelpath))
    mycursor.execute(sql, val)
    db_connection.commit()

    mycursor.close()
    db_connection.close()

    # print(etdid)
    # print(pdf_download_uri)
    # print(localrelpath)

def insertIntoSubjectsTable(etdid, subjects):
    # Change on Subjects table:
    # etdid
    # subject -> from xml
    if subjects:
        for subject in subjects:
            db_connection = mysql.connector.connect(**config)
            mycursor = db_connection.cursor()

            sql = "INSERT INTO subjects (etdid, subject) VALUES (%s, %s)"
            val = (etdid, subject)
            mycursor.execute(sql, val)
            db_connection.commit()

            mycursor.close()
            db_connection.close()

if __name__ == '__main__':
    """
        Step 1: Connect to DB and get data from ETDs table
            id
            url
            
            Done:
            ucd 
            
    """
    university = 'ucb' #TODO: Change here
    etd_ids_uris = getEtdIdListFromDB(university)   
    #print(len(etd_ids_uris)) 
    for etdTuple in etd_ids_uris:        
        etdid,pdf_download_uri = etdTuple
        
        if etdid <= 3945:
            continue
        
        print("Now working on: "+ str(etdid))        
        print(pdf_download_uri)
        """
            Step 2: Extract data from xml using etdid
        """
        etdMetaId = pdf_download_uri.split('/')[4]    
        subjects, year, landingPage, advisor = extractMetaData(etdMetaId)
        # print(landingPage)
        # print(etdMetaId)
        # print(advisor)
        # print(subjects)
        # print(year)

        # """
        #     Step 3: Populate tables
        # """
        updateETDsTable(etdid, year, landingPage, advisor)
        insertIntoPDFsTable(etdid, pdf_download_uri)
        insertIntoSubjectsTable(etdid, subjects)
        
    #(9688, 'https://escholarship.org/content/qt19m7v3jr/qt19m7v3jr.pdf?t=qmmffl')
    #etdid = 9688
    #pdf_download_uri = 'https://escholarship.org/content/qt19m7v3jr/qt19m7v3jr.pdf?t=qmmffl'



