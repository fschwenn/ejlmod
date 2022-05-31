# -*- coding: utf-8 -*-
# Harvest theses from Barcelona Polytechnic U.
#JH: 2022-23-05



from selenium import webdriver
from bs4 import BeautifulSoup
from time import sleep
import getopt
import sys
import os
import codecs
import datetime
import ejlmod2
import re


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

publisher = "Barcelona, Polytechnic U."
pages = 6
rpp = 50

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Barcelona Polytechnic U.'
jnlfilename = 'THESES-BARCELONAPOLYTECH-%s' % (stampoftoday)

# Initialize Webdriver
driver = webdriver.PhantomJS()


boring = [u"Universitat Politècnica de Catalunya. Departament d'Urbanisme i Ordenació del Territori",
          u"Universitat Politècnica de Catalunya. Departament de Projectes Arquitectònics",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria de la Construcció",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria de Projectes i de la Construcció",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Minera, Industrial i TIC",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Química",
          u"Universitat Politècnica de Catalunya. Departament d'Òptica i Optometria",
          u"Universitat Politècnica de Catalunya. Departament d'Organització d'Empreses",
          u"Universitat Politècnica de Catalunya. Departament de Ciència dels Materials i Enginyeria Metal·lúrgica",
          u"Universitat Politècnica de Catalunya. Departament de Composició Arquitectònica",
          u"Universitat Politècnica de Catalunya. Departament de Projectes d'Enginyeria",
          u"Universitat Politècnica de Catalunya. Departament de Resistència de Materials i Estructures a l'Enginyeria",
          u"Universitat Politècnica de Catalunya. Departament de Tecnologia de l'Arquitectura",
          u"Universitat Politècnica de Catalunya. Departament d'Arquitectura de Computadors",
          u"Universitat Politècnica de Catalunya. Departament de Representació Arquitectònica",
          u"Escola Tècnica Superior d'Enginyers de Camins, Canals i Ports de Barcelona",
          u"Universitat Politècnica de Catalunya. Centre de Cooperació per al Desenvolupament",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Agroalimentària i Biotecnologia",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Civil i Ambiental",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria de Sistemes, Automàtica i Informàtica Industrial",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Elèctrica",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Electrònica",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Mecànica",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Telemàtica",
          u"Universitat Politècnica de Catalunya. Departament d'Enginyeria Tèxtil i Paperera",
          u"Universitat Politècnica de Catalunya. Departament d'Estadística i Investigació Operativa",
          u"Universitat Politècnica de Catalunya. Departament d'Expressió Gràfica a l'Enginyeria",
          u"Universitat Politècnica de Catalunya. Departament d'Expressió Gràfica Arquitectònica I",
          u"Universitat Politècnica de Catalunya. Departament d'Infraestructura del Transport i del Territori",
          u"Universitat Politècnica de Catalunya. Departament de Ciència i Enginyeria Nàutiques",
          u"Universitat Politècnica de Catalunya. Departament de Ciències de la Computació",
          u"Universitat Politècnica de Catalunya. Departament de Construccions Arquitectòniques I",
          u"Universitat Politècnica de Catalunya. Departament de Màquines i Motors Tèrmics",
          u"Universitat Politècnica de Catalunya. Departament de Mecànica de Fluids",
          u"Universitat Politècnica de Catalunya. Departament de Teoria del Senyal i Comunicacions",
          u"Universitat Politècnica de Catalunya. Departament de Teoria i Història de l'Arquitectura i Tècniques de Comunicació",
          u"Universitat Politècnica de Catalunya. Institut d'Investigació Tèxtil i Cooperació Industrial de Terrassa",
          u"Universitat Politècnica de Catalunya. Institut d'Organització i Control de Sistemes Industrials",
          u"Universitat Politècnica de Catalunya. Institut de Tècniques Energètiques",
          u"Universitat Politècnica de Catalunya. Institut Universitari de Recerca en Ciència i Tecnologies de la Sostenibilitat"]

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

def update_record(rec, name, data, non_nested=False):
    if name in rec.keys():
        if non_nested:
            rec[name].append(data)
        else:
            rec[name].append([data])
    else:
        if non_nested:
            rec[name] = [data]
        else:
            rec[name] = [[data]]

    return rec


recs = []
regorcid = re.compile('.*orcid:(\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-\d\d\d.).*')
def get_sub_site(url):
    if url in uninterestingDOIS:
        return
    else:
        print '[%s] --> Harvesting data' % url
    rec = {'tc': 'T', 'jnl': 'BOOK', 'link' : url, 'note' : []}
    keepit = True


    driver.get(url+'?show=full')
    fullpage = BeautifulSoup(driver.page_source, 'lxml')
    rows = fullpage.find_all('tr', attrs={'class': 'ds-table-row'})
    for row in rows:
        columns = row.find_all('td')
        title = columns[0].text
        data = columns[1].text

        # Get the author
        if title == 'dc.contributor.author':
            rec['autaff'] = [[ data, publisher ]]

        # Get the supervisor
        if title == 'dc.contributor':
            rec = update_record(rec, 'supervisor', data)

        # Get the date
        if title == 'dc.date.issued':
            rec['date'] = data

        # Get the handle
        if title == 'dc.identifier.uri':
            rec['hdl'] = re.sub('.*handle.net\/', '', data)

        # Get the abstract in english
        if title == 'dc.description.abstract':
            if data.find('the') != -1:
                rec['abs'] = data

        # Get the pages
        if title == 'dc.format.extent':
            rec['pages'] = data.replace(' p.', '')

        # Get the language
        if title == 'dc.language.iso':
            if data == 'spa':
                rec['language'] = 'Spanish'

        # Get the license link
        if title == 'dc.rights.uri':
            rec['license'] = {
                'url': data
            }
            splitted_url = data.split('/')
            statement = splitted_url[-3] + '-' + splitted_url[-2]
            rec['license']['statement'] = statement.upper()

        # Get the keywords
        if title.find('dc.subject') != -1:
            rec = update_record(rec, 'keyw', data, True)

        # Get the title
        if title == 'dc.title':
            rec['tit'] = data

        #department
        elif title == 'dc.contributor.other':
            if data in boring:
                keepit = False
            else:
                rec['note'].append(data)
                

    # Get the pdf link
    pdf_section = fullpage.find_all('a', attrs={'class': 'image-link'})
    if len(pdf_section) == 1:
        rec['hidden'] = "https://upcommons.upc.edu%s" % pdf_section[0].get('href')
    if keepit:
        recs.append(rec)
        print '  ', rec.keys()
    else:
        newuninterestingDOIS.append(url)

    #check for ORCIDs
    sleep(5)
    driver.get(url)
    page = BeautifulSoup(driver.page_source, 'lxml')
    #author
    for div in page.find_all('div', attrs={'class': 'simple-item-view-authors'}):
        for a in div.find_all('a'):
            if a.has_attr('href') and re.search('browse.authority', a['href']):
                rec['autaff'] = [[ a.text.strip() ]]
                if regorcid.search(a['href']):
                    rec['autaff'][-1].append(regorcid.sub(r'ORCID:\1', a['href']))
                rec['autaff'][-1].append(publisher)
    #supervisor        
    for div in page.find_all('div', attrs={'class': 'simple-item-view-description'}):
        for span in div.find_all('span'):
            if re.search('Tutor', span.text):
                rec['supervisor'] = []
                for a in div.find_all('a'):
                    if a.has_attr('href') and re.search('browse.authority', a['href']):
                        rec['supervisor'].append([ a.text.strip() ])
                        if regorcid.search(a['href']):
                            rec['supervisor'][-1].append(regorcid.sub(r'ORCID:\1', a['href']))
                        rec['supervisor'][-1].append(publisher)

                        
for page in range(pages):
    print('OPENING PAGE %i OF %i' % (page+1, pages))
    tocurl = 'https://upcommons.upc.edu/discover?rpp=' +str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Doctoral+thesis&sort_by=dc.date.issued_dt&order=desc'
    driver.get(tocurl)
    for article in BeautifulSoup(driver.page_source, 'lxml').find_all('h4', attrs={'class': 'artifact-title'}):
        article_link = article.find_all('a')
        if len(article_link) == 1:
            article_link = article_link[0].get('href')
            get_sub_site('https://upcommons.upc.edu%s' % article_link)
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
