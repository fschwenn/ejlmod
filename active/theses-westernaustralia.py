# -*- coding: utf-8 -*-
# Harvest theses from Western Australia
# JH: 2022-03-19

from time import sleep
from selenium import webdriver
from datetime import datetime
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import os
import codecs
import ejlmod2
import re

driver_options = Options()
driver_options.headless = True
driver = webdriver.Chrome(options=driver_options)


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"+'_special'

pages = 1+5

now = datetime.now()
stamp_of_today = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Western Australia U.'
jnlfilename = 'THESES-WESTERN-AUSTRALIA-%s' % stamp_of_today


recs = []


def get_sub_site(url):
    rec = {'link': url, 'tc': 'T', 'jnl': 'BOOK'}

    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'lxml')
    
    # Get the thesis title
    title_section = soup.find_all('h1')
    if len(title_section) == 1:
        rec['tit'] = title_section[0].text

    #keywords
    for meta in soup.head.find_all('meta', attrs = {'name' : 'citation_keywords'}):
        rec['keyw'] = re.split('; ', meta['content'])

    # Get the author's name
    for meta in soup.head.find_all('meta', attrs = {'name' : 'citation_author'}):
        rec['autaff'] = [[ meta['content'], publisher ]]
    #author_link = soup.find_all('a', attrs={'class': 'link person', 'rel': 'Person'})
    #if len(author_link) == 1:
    #    author_name = author_link[0].text
    #    rec['autaff'] = [[author_name]]

    # Get the abstract
    abstract_section = soup.find_all('div', attrs={'class': 'rendering_researchoutput_abstractportal'})
    if len(abstract_section) == 1:
        abstract = abstract_section[0].text
        rec['abs'] = abstract

    # Get properties
    properties_section = soup.find_all('table', attrs={'class': 'properties'})
    if len(properties_section) == 1:
        for prop in properties_section[0].find_all('tr'):
            title = prop.find_all('th')[0].text
            data = prop.find_all('td')[0]

            # Get the paper's language
            #if title.find('Original language') != -1:
            #    rec['language'] = data.text

            # Check if the theses is a P.h.D
            if title.find('Qualification') != -1:
                if data.text.find('Doctor of Philosophy') == -1:
                    return

            # Get the supervisors
            if title.find('Supervisors/Advisors') != -1:
                raw_supervisors = data.find_all('strong', attrs={'class': 'title'})
                supervisors = []
                for supervisor in raw_supervisors:
                    supervisors.append([supervisor.text])

                rec['supervisor'] = supervisors

            # Get the award date
            if title.find('Award date') != -1:
                month_words = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                date = data.text

                # Reformat the date
                day, month, year = date.split(' ')
                for i in range(len(month_words)):
                    if month_words[i] == month:
                        month = i+1
                        break
                try:
                    rec['date'] = '%s-%02i-%02i' % (year, month, int(day))
                except:
                    pass
    if not 'date' in rec.keys():
        for meta in soup.head.find_all('meta', attrs = {'name' : 'citation_publication_date'}):
            rec['date'] = meta['content']
        if not 'date' in rec.keys():
            try:
                rec['date'] = year
            except:
                print url

    # Get the DOI
    doi_section = soup.find_all('div', attrs={'doi'})
    if len(doi_section) == 1:
        doi_sub_section = doi_section[0].find_all('span')
        if len(doi_sub_section) == 1:
            doi = doi_sub_section[0].text
            rec['doi'] = doi
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/WesternAustralia/'+re.sub('.*\/', '', url)

    # Get the pdf link
    pdf_link_section = soup.find_all('a', attrs={'class': 'link document-link'})
    if len(pdf_link_section) == 1:
        if pdf_link_section[0].get('href') is not None:
            pdf_link = "https://research-repository.uwa.edu.au%s" % pdf_link_section[0].get('href')

            rec['hidden'] = pdf_link

    print(rec.keys())

    recs.append(rec)


for page in range(pages):
    to_curl = 'https://research-repository.uwa.edu.au/en/publications/?type=%2Fdk%2Fatira%2Fpure%2Fresearchoutput' \
              '%2Fresearchoutputtypes%2Fthesis%2Fdoc&nofollow=true&organisationIds=3bece221-0399-4ae7-a111' \
              '-eecc4a1d60e1&organisationIds=a6413e77-1fd9-4a6e-beac-53cff1299a0f&organisationIds=564bce6b-6946-40f3' \
              '-a9c9-10c6ad7a1122&format=&page=' + str(page)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, to_curl)
    driver.get(to_curl)
    for h3 in BeautifulSoup(driver.page_source, 'lxml').find_all('h3', attrs={'class': 'title'}):
        article_link_box = h3.find_all('a', attrs={'class': 'link', 'rel': 'Thesis'})
        if len(article_link_box) == 1:
            if article_link_box[0].get('href') is not None:
                get_sub_site(article_link_box[0].get('href'))
        sleep(5)
    sleep(5)


#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
