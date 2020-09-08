# -*- coding: utf-8 -*-
#harvest theses from Naples U.
#FS: 2020-02-24

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Naples U.'

pages = 5
jnlfilename = 'THESES-NAPLES-%s' % (stampoftoday)

uninterestingdepartments = ["Scienze Biomediche Avanzate", "Economia, Management e Istituzioni",
                            "Medicina Veterinaria e Produzioni Animali",
                            "Agraria", "Biologia", "Farmacia",
                            "Giurisprudenza", "Ingegneria Industriale",
                            "Ingegneria Civile, Edile e Ambientale",
                            "Medicina Clinica e Chirurgia", "Architettura",
                            "Ingegneria Chimica, dei Materiali e della Produzione Industriale",
                            "Ingegneria Elettrica e delle Tecnologie dell'Informazione",
                            'Matematica e Applicazioni "Renato Caccioppoli"',
                            "Neuroscienze e Scienze Riproduttive ed Odontostomatologiche",
                            "Scienze Mediche Traslazionali", "Scienze Sociali",
                            "Scienze della Terra, dell'Ambiente e delle Risorse",
                            "Scienze Economiche e Statistiche",
                            "Strutture per l'Ingegneria e l'Architettura",
                            "Medicina Molecolare e Biotecnologie Mediche",
                            "Sanità Pubblica", "Scienze Politiche",
                            "Scienze Chimiche", "Studi Umanistici"]
                            

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'http://www.fedoa.unina.it/cgi/search/archive/advanced?exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Ctype%3Atype%3AANY%3AEQ%3Athesis_phd%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&_action_search=1&order=-date%2Fcreators_name%2Ftitle&screen=Search&cache=51779&search_offset=' + str(20*page)
    print '---{ %i/%i }---{ %s }------' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(5)
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        for a in tr.find_all('a'):
            if a.has_attr('href') and re.search('unina.it.\d+', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
                rec['artlink'] = a['href']
                rec['doi'] = '20.2000/NAPLES/' + re.sub('\D', '', a['href'])
                prerecs.append(rec)


i = 0
recs = []
for rec in prerecs:
    interesting = True
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
    #author
    for meta in artpage.find_all('meta', attrs = {'name' : 'eprints.creators_name'}):
        rec['autaff'] = [[ meta['content'] ]]
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #email
            if meta['name'] == 'eprints.creators_id':
                if re.search('@', meta['content']):
                    rec['autaff'][-1].append('EMAIL:' + meta['content'])
                else:
                    print meta['content']
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #language
            elif meta['name'] == 'eprints.language':
                if meta['content'] in ['it', 'ita', 'italian']:
                    rec['language'] = 'italian'
            #department
            elif meta['name'] == 'eprints.department':
                if meta['content'] in uninterestingdepartments:
                    print ' skip ', meta['content']
                    interesting = False
                else:
                    rec['note'].append(meta['content'])
            #supervisor
            elif meta['name'] == 'eprints.tutors_name':
                rec['supervisor'] = [[ meta['content'] ]]
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['hidden'] = meta['content']
            #date
            elif meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
            #pages
            elif meta['name'] == 'eprints.pages':
                if re.search('^\d+$', meta['content']):
                    rec['pages'] = meta['content']
            #keywords
            elif meta['name'] == 'eprints.keywords':
                if re.search(';.*;', meta['content']):
                    rec['keyw'] = re.split('; ', meta['content'])                    

    if interesting:
        rec['autaff'][-1].append(publisher)
        recs.append(rec)
        print rec.keys()

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
