# -*- coding: utf-8 -*-
#harvest theses from U. Santiago de Compostela (main)
#FS: 2020-10-08
import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time
import json

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'THESES-SantiagoDeCompostella-%s' % (stampoftoday)

publisher = 'U. Santiago de Compostela (main)'

hdr = {'User-Agent' : 'Magic Browser'}

rpp = 50
pages = 1
boringdisciplines = ['UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenAvancesenBioloxaMicrobianaeParasitaria',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenBiodiversidadeeConservacindoMedioNatural',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenCienciaeTecnoloxaQumica',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenEnerxasRenovableseSustentabilidadeEnerxtica<',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenEstatsticaeInvestigacinOperativa',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenInnovacinenSeguridadeeTecnoloxaAlimentarias',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenInvestigacineDesenvolvementodeMedicamentos',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenNeurocienciaePsicoloxaClnica',
                     'CentroSingulardeInvestigacinenQumicaBiolxicaeMateriaisMolecularesCiQUS',
                     'FacultadedeQumica',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenCienciadeMateriais',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenCienciasAgrcolaseMedioambientais',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenEnerxasRenovableseSustentabilidadeEnerxtica',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenMedicinaMolecular',
                     'UniversidadedeSantiagodeCompostelaProgramadeDoutoramentoenMedioAmbienteeRecursosNaturais']
                                         
boringdegrees = []

prerecs = []
for page in range(pages):
    tocurl = 'https://minerva.usc.es/xmlui/handle/10347/2291/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        new = True
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'supervisor' : []}
        for span in div.find_all('span', attrs = {'class' : 'date'}):
            if re.search('[12]\d\d\d', span.text):
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                if int(rec['year']) < now.year - 2*10:
                    new = False
                    print '  skip',  rec['year']
        if new:
            for a in div.find_all('a'):
                if re.search('handle', a['href']):
                    rec['artlink'] = 'https://minerva.usc.es' + a['href'] + '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    prerecs.append(rec)
    time.sleep(2)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = meta['content']
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['content']:
                    rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split('[,;] ', meta['content']):
                    if not re.search('^info.eu.repo', keyw):
                        rec['keyw'].append(keyw)
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            tdt = td.text.strip()
            td.decompose()
        for td in tr.find_all('td'):
            if td.text.strip() == 'en_US':
                continue
            #supervisor
            if tdt == 'dc.contributor.advisor':
                rec['supervisor'] = [[ re.sub(' \(.*', '', td.text.strip()) ]]
            #discipline
            elif tdt == 'dc.contributor.affiliation':
                discipline = re.sub('\W', '', td.text.strip())
                if discipline in boringdisciplines:
                    print '  skip "%s"' % (discipline)
                    keepit = False
                else:
                    rec['note'].append(discipline)
            #degree
            elif tdt == 'dc.type':
                degree = td.text.strip()
                if degree in boringdegrees:
                    print '  skip "%s"' % (degree)
                    keepit = False
                else:
                    rec['note'].append(degree)
            #language
            elif tdt == 'dc.language.iso':
                if td.text.strip() == 'spa':
                    rec['language'] = 'spanish'
            #license
            elif tdt == 'dc.rights.uri':
                if re.search('creativecommons.org', td.text):
                    rec['license'] = {'url' : td.text.strip()}
    if keepit:
        recs.append(rec)
        print '  ', rec.keys()
                
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'),'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
