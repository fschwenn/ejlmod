# -*- coding: utf-8 -*-
#harvest theses from Puebla U.
#JH: 2022-06-07


import getopt
import sys
import os
import codecs
import datetime
import ejlmod2
from selenium import webdriver
from bs4 import BeautifulSoup
from iso_codes import IsoCodeConverter
from time import sleep

# Initiate webdriver
driver = webdriver.PhantomJS()

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Puebla U., Inst. Fis.'
jnlfilename = 'THESES-PUEBLA-%s' % (stampoftoday)

recs = []

rpp = 50
pages = 2

boring = [u'Facultad de Ciencias Químicas', u'Área de Ciencias Sociales y Humanidades',
          u'Área Económico Administrativa', u'Área de Ciencias Sociales',
          u'Área de Educación y Humanidades']
boring += [u'Facultad de Economía', u'Facultad de Derecho y Ciencias Sociales',
           u'Facultad de Arquitectura', u'Instituto de Fisiología',
           u'nstituto de Ciencias de Gobierno y Desarrollo Estratégico<',
           u'Facultad de Filosofía y Letras']

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

def format_license(rec, data):
    rec['license'] = {
        'url': data
    }
    splitted_url = data.split('/')
    statement = splitted_url[-2] + '-' + splitted_url[-1]
    rec['license']['statement'] = statement.upper()

# Initiate ISO-Converter
iso_converter = IsoCodeConverter('db/iso_codes.db')
# iso_converter.write_database()


def get_sub_site(url):
    global uninterestingDOIS
    keepit = True
    print '[%s] --> Harversting Data' % url
    driver.get(url)

    rec = {'tc': 'T', 'jnl': 'BOOK', 'supervisor': [], 'autaff': [], 'keyw': [], 'link' : url, 'note' : []}

    rows = BeautifulSoup(driver.page_source, 'lxml').find_all('tr', attrs={'class': 'ds-table-row'})
    for row in rows:
        columns = row.find_all('td')
        label = columns[0].text
        data = columns[1].text

        # Get the supervisor
        if label == 'dc.contributor.advisor':
            rec['supervisor'].append([data.split(';')[0]])

        # Get the author
        elif label == 'dc.contributor.author':
            rec['autaff'].append([data, publisher])

        # Get the issued date
        elif label == 'dc.date.issued':
            rec['date'] = data

        # Get the handle
        elif label == 'dc.identifier.uri':
            splitted_hdl = data.split('/')
            rec['hdl'] = splitted_hdl[-2] + '/' + splitted_hdl[-1]

        # Get the abstract
        elif label == 'dc.description.abstract':
            rec['abs'] = data

        # Get the language
        elif label == 'dc.language.iso':
            try:
                lang = iso_converter.get_country_name(data).split(', ')[0]
                if lang != 'English':
                    rec['language'] = lang
            except:
                pass

        # Get the subject
        elif label == 'dc.rights.uri':
            format_license(rec, data)

        # Get the keywords
        elif label.find('dc.subject') != -1:
            rec['keyw'].append(data)

        # Get the title
        elif label == 'dc.title':
            rec['tit'] = data

        # Check if it is really a PhD
        elif label == 'dc.type.degree':
            if data != 'Doctorado':
                keepit = False

        #department
        elif label in ['dc.thesis.degreegrantor', 'dc.thesis.degreediscipline']:
            if data in boring:
                keepit = False
            else:
                rec['note'].append(label+': '+data)

    

    # Get the pdf link
    #pdf_section = BeautifulSoup(driver.page_source, 'lxml').find_all('div', attrs={'class': 'file-link col-xs-6 '
    #                                                                                        'col-xs-offset-6 col-sm-2'
    #                                                                                        'col-sm-offset-0'})
    #if len(pdf_section) == 1:
    #    link_section = pdf_section[0].find_all('a')
    #    if len(link_section) == 1:
    #        rec['FFT'] = 'https://repositorioinstitucional.buap.mx%s' % link_section[0].get('href')
    for meta in BeautifulSoup(driver.page_source, 'lxml').find_all('meta', attrs={'name': 'citation_pdf_url'}):
        rec['FFT'] = meta['content' ]
    if keepit:
        recs.append(rec)
    else:
        newuninterestingDOIS.append(url)
    return

for page in range(pages):
    print "--- PAGE %i of %i ---" % (page, pages)
    to_curl = 'https://repositorioinstitucional.buap.mx/handle/20.500.12371/7/discover?rpp=' + str(rpp) + '&etal=0' \
                                                                                                          '&group_by' \
                                                                                                          '=none&page='\
              + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc '

    driver.get(to_curl)
    for article in BeautifulSoup(driver.page_source, 'lxml').find_all('div', attrs={'class': 'col-sm-9 '
                                                                                             'artifact-description'}):
        article_link = article.find_all('a')
        if len(article_link) == 1:
            url = 'https://repositorioinstitucional.buap.mx%s?show=all' % article_link[0].get('href')
            if not url in uninterestingDOIS:
                get_sub_site(url)
                sleep(4)
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

ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()
