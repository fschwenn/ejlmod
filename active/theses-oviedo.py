# -*- coding: utf-8 -*-
#harvest theses from Oviedo U.
#FS: 2021-09-14

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
rpp = 3
pages = 60

publisher = 'Oviedo U.'

jnlfilename = 'THESES-OVIEDO-%s' % (stampoftoday)
boring = [u'Biología Molecular y Celular, Departamento de',
          u'Ciencias de la Salud, Departamento de',
          u'Administración de Empresas, Departamento de',
          u'Biología de Organismos y Sistemas, Departamento de',
          u'Biología Funcional, Departamento de',
          u'Bioquímica y Biología Molecular, Departamento de',
          u'Ciencia de los Materiales e Ingeniería Metalúrgica, Departamento de',
          u'Ciencias de la Educación, Departamento de',
          u'Ciencias Jurídicas Básicas, Departamento de',
          u'Ciencia y Tecnología Náutica, Departamento de',
          u'Cirugía y Especialidades Médico Quirúrgicas, Departamento de',
          u'Construcción e Ingeniería de Fabricación, Departamento de',
          u'Derecho Privado y de la Empresa, Departamento de',
          u'Derecho Público, Departamento de',
          u'Economía Aplicada, Departamento de',
          u'Economía, Departamento de',
          u'Economía y Empresa, Facultad de',
          u'Energía, Departamento de',
          u'Estadística e Investigación Operativa y Didáctica de la Matemática, Departamento de',
          u'Explotación y Prospección de Minas, Departamento de',
          u'Filología Anglogermánica y Francesa, Departamento de',
          u'Filología Clásica y Románica, Departamento de',
          u'Filología Española, Departamento de',
          u'Filosofía, Departamento de',
          u'Geografía, Departamento de',
          u'Geología, Departamento de',
          u'Historia del Arte y Musicología, Departamento de',
          u'Historia, Departamento de',
          u'Informática, Departamento de',
          u'Ingeniería eléctrica, electrónica, de computadores y sistemas, Departamento de',
          u'Ingeniería Eléctrica, Electrónica, de Computadores y Sistemas, Departamento de',
          u'Ingeniería Química y Técnica del medio Ambiente, Departamento de',
          u'Ingeniería Química y Tecnología del Medio Ambiente, Departamento de',
          u'Medicina, Departamento de',
          u'Morfología y Biología Celular, Departamento de',
          u'Química Orgánica e Inorgánica, Departamento de',
          u'Universidad de Oviedo. Facultad de Filosofía y Letras',
          u'Psicología, Departamento de',
          u'Contabilidad, Departamento de',
          u'Economía Cuantitativa, Departamento de',
          u'Instituto Universitario de Neurociencias del Principado de Asturias (INEUROPA)',
          u'Instituto Universitario de Oncología, IUOPA',
          u'Sociología, Departamento de']

prerecs = []

realpages = pages
for page in range(pages):
        tocurl = 'https://digibuo.uniovi.es/dspace/handle/10651/5573/discover?rpp=' + str(rpp) + '&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
        print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
        try:
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (tocurl)
            time.sleep(180)
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            for a in div.find_all('a'):
                for h4 in a.find_all('h4'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'keyw' : [], 'note' : []}
                    rec['tit'] = a.text.strip()
                    rec['link'] = 'https://digibuo.uniovi.es' + a['href']
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'] += re.split('; ', meta['content'])
            elif meta['name'] == 'DC.contributor':
                if meta.has_attr('xml:lang'):
                    department = meta['content']
                    if department in boring:
                        keepit = False
                    else:
                        rec['note'].append(department)
                else:
                    rec['supervisor'].append([meta['content']])
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            elif meta['name'] == 'citation_date':
                if re.search('^\d\d\d\d\-\d\d\-\d\d', meta['content']): 
                    rec['date'] = meta['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d p\.', meta['content']):
                    rec['pages'] = re.sub('\D', '', meta['content'])
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
            #languag
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'spa':
                    rec['language'] = 'spanish'
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
