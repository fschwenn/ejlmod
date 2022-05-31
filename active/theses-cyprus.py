# -*- coding: utf-8 -*-
#harvest theses from Cyprus
#JH: 2022-19-05


import getopt
import sys
import os
import re
import codecs
import datetime
import ejlmod2
from selenium import webdriver
from bs4 import BeautifulSoup
from base64 import b64encode
from time import sleep

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Cyprus U.'
rpp = 10
pages = 1

publisher = 'Cyprus U.'
jnlfilename = 'THESES-CYPRUS-%s' % (stampoftoday)

# Initialize Webdriver
driver = webdriver.PhantomJS()


recs = []

regorcid = re.compile('(.*) \[(\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-\d\d\d.)\]')
regpages = re.compile('.*?(\d\d+) p\..*')
def get_sub_site(url, fc):
    orcids = {}
    
    print "[%s] --> Harvesting data" % url
    driver.get(url)

    rec = {
        'tc': 'T',
        'jnl': 'BOOK',
        'link' : url,
        'doi': '20.2000/Cyprus/%s' % (re.sub('.*handle\/(.*\d).*', r'\1', url))
    }

    if len(fc) != 0:
        rec['fc'] = fc

    page = BeautifulSoup(driver.page_source, 'lxml')
        
    rows = page.find_all('tr', attrs={'class': 'ds-table-row'})
    for row in rows:
        columns = row.find_all('td')
        name = columns[0]
        data = columns[1]
        language = columns[2]

        # Get the author
        if name.text == 'dc.contributor.author':
            if "autaff" in rec.keys():
                rec['autaff'].append([data.text])
            else:
                rec['autaff'] = [[data.text]]

        # Get the date
        elif name.text == 'dc.date.issued':
            rec['date'] = data.text

        # Get the abstract
        elif name.text == 'dc.description.abstract' and language.text == 'en':
            rec['abs'] = data.text

        # Get the language
        elif name.text == 'dc.language.iso':
            language = data.text.upper()
            if language == 'GRE':
                rec['language'] = 'Greek'
            elif language != 'ENG':
                rec['language'] = language

        # Get the title
        elif name.text == 'dc.title':
            rec['tit'] = data.text
        elif  name.text == 'dc.title.alternative':
            rec['transtit'] = data.text

        # Get the supervisors
        elif name.text == 'dc.contributor.advisor':
            if 'supervisor' in rec.keys():
                rec['supervisor'].append([data.text])
            else:
                rec['supervisor'] = [[data.text]]

        # Get the keywords
        elif name.text in ['dc.subject.uncontrolledterm', 'dc.subject.lcsh'] and language.text == 'en':
            if 'keyw' in rec.keys():
                rec['keyw'].append(data.text)
            else:
                rec['keyw'] = [data.text]

        # check if is a PhD theses
        elif name.text == 'dc.type.uhtype':
            if data.text != 'Doctoral Thesis':
                print data.text
                return

        # Get the license
        elif name.text == 'dc.rights.uri':
            if data.text.find('creativecommons') != -1:
                rec['license'] = {'url': data.text }

        #ORCIDs
        elif name.text == 'dc.contributor.orcid':
            if regorcid.search(data.text):
                name = regorcid.sub(r'\1', data.text.strip())
                orcid = regorcid.sub(r'ORCID:\2', data.text.strip())
                orcids[name] = orcid

        #pages
        elif name.text == 'dc.format.extent':
            if regpages.search(data.text):
                rec['pages'] = regpages.sub(r'\1', data.text)


    #ORCIDs
    for key in ['autaff', 'supervisor']:
        if key in rec.keys():
            for person in rec[key]:
                if person[0] in orcids.keys():
                    person.append(orcids[person[0]])
    rec['autaff'][0].append(publisher)
            

    # Get the pdf link
    for meta in page.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
        if 'license' in rec.keys():
            rec['FFT'] = meta['content']
        else:
            rec['hidden'] = meta['content']
    #pdf_link = BeautifulSoup(driver.page_source, 'lxml').find_all('img', attrs={'alt': 'Thumbnail'})
    #if len(pdf_link) == 1:
    #    pdf = pdf_link[0].get('src')
    #    rec['hidden'] = 'https://gnosis.library.ucy.ac.cy%s' % pdf
    print '  ', rec.keys()
    recs.append(rec)


for (fc, dep) in [('m', '25074'), ('c', '25075'), ('', '39072')]:
    for page in range(pages):
        tocurl = 'https://gnosis.library.ucy.ac.cy/handle/7/' + dep + '/discover?sort_by=dc.date.issued_dt&order=desc' \
                                                                      '&rpp=' + str(rpp) + '&page=' + str(page)
        driver.get(tocurl)
        print "[%s] --> NEW PAGE" % tocurl
        for article in BeautifulSoup(driver.page_source, 'lxml').find_all('div', attrs={'class': 'col-sm-9 artifact-description'}):
            article_link = article.find_all('a')
            if len(article_link) == 1:
                get_sub_site("https://gnosis.library.ucy.ac.cy%s?show=full" % article_link[0].get('href'), fc)
            sleep(10-8)
        sleep(10)

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
