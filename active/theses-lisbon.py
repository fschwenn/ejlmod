# -*- coding: utf-8 -*-
#harvest theses from U. Lisbon (main) 
#FS: 2021-02-09


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import unicodedata
import datetime
import time
import json

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Lisbon (main)'
jnlfilename = 'THESES-LISBON-%s' % (stampoftoday)

rpp = 50
pages = 2

standard = ['Universidade de Lisboa', 'Tese de doutoramento', 'Faculdade de Ciencias',
            'Tese de Doutoramento']
boring = ['Energia e Ambiente (Energia e Desenvolvimento Sustentavel)',
          'Alteracoes Climaticas e Politicas de Desenvolvimento Sustentavel (Ciencias do Ambiente)',
          'Biologia (Biologia de Sistemas)', 'Biologia (Biotecnologia)',
          'Biologia e Ecologia das Alteracoes Globais (Biologia e Ecologia Tropical)',
          'Ciencias do Mar', 'Engenharia Biomedica e Biofisica', 'Quimica (Quimica)',
          'Arte e Sociedade (Filosofia da Tecnologia)', 'Biodiversidade (Genetica e Evolucao)',
          'Biodiversidade', 'Biologia (Biodiversidade)', 'Biologia (Biologia do Desenvolvimento)',
          'Biologia (Biologia Marinha e Aquacultura)', 'Biologia (Microbiologia)',
          'Bioquimica (Bioquimica Estrutural)', 'Ciencias Geofisicas e da Geoinformacao (Geofisica)',
          'Ciencias Geofisicas e da Geoinformacao (Meteorologia)', 'Doutoramento em Bioquimica', 
          'Doutoramento em Biologia e Ecologia das Alteracoes Globais', 'Doutoramento em Biologia',
          'Doutoramento em Ciencias do Mar', 'Doutoramento em Ciencias Geofisicas e da Geoinformacao',
          'Doutoramento em Informatica', 'Doutoramento em Quimica', 'Geologia (Geodinamica Interna)', 
          'Doutoramento em Sistemas Sustentaveis de Energia', 'Genetica e Evolucao',
          'Geologia (Geoquimica)', 'Historia e Filosofia das Ciencias', 'logica e fundamentos)', 
          #'Informatica (Ciencia da Computacao)',
          'Informatica (Engenharia Informatica)',
          'Logica e Fundamentos)', 'Quimica (Quimica Analitica)', 'Quimica (Quimica Inorganica)',
          'Doutoramento em Alteracoes Climaticas e Politicas de Desenvolvimento Sustentavel',
          'Doutoramento em Biodiversidade Genetica e Evolucao', 'Doutoramento em Ciencias do Ambiente', 
          'Doutoramento em Biologia (Antropologia Biologica)', 'Doutoramento em Ciencias Geofisicas',
          'Doutoramento em Educacao', 'Doutoramento em Energia e Ambiente',
          'Doutoramento em Engenharia Biomedica e Biofisica', 'Doutoramento em Engenharia Fisica',
          'Doutoramento em e-Planeamento', 'Doutoramento em Geologia',
          'Doutoramento em Historia e Filosofia das Ciencias', 'Doutoramento em Historia',
          'Tese doutoramento em Biologia (Biologia Molecular) Universidade de Lisboa',
          'Tese doutoramento em Ciencias do Mar. Universidade de Lisboa',
          'Tese doutoramento em Quimica (Quimica Analitica) Universidade de Lisboa',
          'Quimica (Quimica Organica)', 'Tecnologia', 'Sistemas Sustentaveis de Energia']

#get ORCID from author search page
def getorcid(a):
    #print '{', 'https://repositorio.ul.pt' + a['href'], '}'
    authorpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('https://repositorio.ul.pt' + a['href']))
    for span in authorpage.find_all('span'):
        spant = span.text.strip()
        #print spant
        if re.search('\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-', spant):
            return 'ORCID:' + spant
    return False

###remove accents from a string
def akzenteabstreifen(string):
    if not type(string) == type(u'unicode'):
        string = unicode(string,'utf-8', errors='ignore')
        if not type(string) == type(u'unicode'):
            return string
        else:
            return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')
    else:
        return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')

            

refac = re.compile('(Life|Health|Medicine|Social|Information|Music|Arts|Chemistry)')
hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for j in range(pages):
    tocurl = 'https://repositorio.ul.pt/handle/10451/27/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(j*rpp) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }==' % (j+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for td in tocpage.body.find_all('td', attrs = {'headers' : 't2'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'note' : [], 'supervisor' : []}
        for a in td.find_all('a'):
            rec['artlink'] = 'https://repositorio.ul.pt' + a['href'] + '?locale=en'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)
    time.sleep(10)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    if not re.search('\:\:', keyw) and not re.search('Teses de doutoramento', keyw):
                        rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' the ',  meta['content']):
                    rec['abs'] = meta['content']
                else:
                    rec['abspt'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'por':
                    rec['language'] = 'Portuguese'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'pdf_url' in rec.keys():
                rec['FFT'] = rec['pdf_url']
    #hidden PDF
    if not 'FFT' in rec.keys():
        if 'pdf_url' in rec.keys():
            rec['hidden'] = rec['pdf_url']
    #abstract
    if not 'abs' in rec.keys() and 'abspt' in rec.keys():
        rec['abs'] = rec['abspt']
    for tr in artpage.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
            tht = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue'}):
            #author
            if re.search('Author:', tht):
                for a in td.find_all('a'):
                    rec['autaff'] = [[ re.sub(', \d.*', '', a.text.strip()) ]]
                    orcid = getorcid(a)
                    if orcid:
                        rec['autaff'][-1].append(orcid)
                    rec['autaff'][-1].append(publisher)
            #supervisor
            elif re.search('Advisor:', tht):
                for a in td.find_all('a'):
                    rec['supervisor'].append([ re.sub(', \d.*', '', a.text.strip()) ])
                    orcid = getorcid(a)
                    if orcid:
                        rec['supervisor'][-1].append(orcid)
            #department
            elif re.search('Designation:', tht):
                desig = akzenteabstreifen(td.text.strip())
                for part in re.split(', ', desig):
                    if len(part) > 4 and not part in standard:
                        if part in boring:
                            print '  skip', part
                            keepit = False
                        else:
                            rec['note'].append(part)
    if keepit:                
        print '  ', rec.keys()
        recs.append(rec)

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
