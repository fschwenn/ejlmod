# -*- coding: utf-8 -*-
#harvest theses from Paraiba U.
#FS: 2021-01-29


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import unicodedata 
import codecs
import datetime
import time
import json
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Paraiba U.'
pages = 2
rpp = 100
boringdeps = ['Arquitetura e Urbanismo', 'Administrao', 'Antropologia', 'Artes Cnicas',
              'Biologia Celular e Molecular', 'Biologia Molecular', 'Biotecnologia',
              'Cidadania e Direitos Humanos', 'Cincia das Religies', 'Cincias da Nutrio',
              'Cincias Jurdicas', 'Cincias Veterinrias', 'Educao', 'Enfermagem',
              'Engenharia de Materiais', 'Engenharia de Produo', 'Engenharia Eltrica',
              'Engenharia Mecnica', 'Engenharia Qumica', 'Filosofia', 'Histria',
              'Finanas e Contabilidade', 'Gerenciamento Ambiental', 'Gesto Pblica',
              'Economia do Trabalho e Economia de Empresas',
              'Informtica', 'Jornalismo', 'Letras', 'Lingustica', 'Medicina', 'Msica',
              'Cincia da Informao', 'Engenharia Civil e Ambiental', 'Zoologia',
              'Engenharia de Alimentos', 'Farmacologia', 'Geografia', 'Odontologia', 
              'Psicologia Social', 'Psicologia', 'Servio Social', 'Sociologia',
              'Direitos Humanos', 'Lingustica e ensino', 'cincias Juridicas',
              'Qumica e Bioqumica de Alimentos', 'Tecnologia Agroalimentar',
              'Tecnologia de Alimentos',
              'Economia', 'Engenharias Renovveis', 'Letras Clssicas e Vernculas', 
              'Agricultura', 'Artes Visuais', 'Cincia Animal', 'Cincias Biolgicas',
              'Comunicao', 'Engenharia Cvil e Ambiental', 'Engenharia de Energias Renovveis',
              'Engenharia e Meio Ambiente', 'Fsica', 'Solos e Engenharia Rural', 'Zootecnia',
              'Nutrio', 'Qumica', 'Relaes Internacionais']
              

jnlfilename = 'THESES-PARAIBA-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

prerecs = []
for page in range(pages):
    tocurl = 'https://repositorio.ufpb.br/jspui/simple-search?location=&query=&filter_field_1=type&filter_type_1=equals&filter_value_1=Disserta%C3%A7%C3%A3o&rpp=' + str(rpp) + '&sort_by=dc.date.issued_dt&order=DESC&etal=0&submit_search=Update&start=' + str((page+20 + 20)*rpp)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    for td in tocpage.body.find_all('td', attrs = {'headers' : 't2'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [], 'keyw' :[]}
        for a in td.find_all('a'):
            rec['link'] = 'https://repositorio.ufpb.br' + a['href'] #+ '?show=full'
            rec['doi'] = '20.2000/Paraiba/' + re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)
    time.sleep(2)
        

i = 0
reprog = re.compile('^(Programa de|Mestrado Profissional|Programa Associado de) ')
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if not meta.has_attr('xml:lang'):
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author, publisher ]]
            #supervisor
            elif meta['name'] == 'DC.contributor':
                if not meta.has_attr('xml:lang'):
                    rec['supervisor'].append([meta['content']])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] != 'eng':
                    if meta['content'] == 'por':
                        rec['language'] = 'Portuguese'
                    else:
                        rec['language'] = meta['content']
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #department
            elif meta['name'] == 'DC.publisher':
                dep = meta['content'].encode('ascii', 'ignore')
                if not dep in ['Brasil', 'UFPB', 'Universidade Federal da Paraba']:
                    if not reprog.search(dep):
                        if dep in boringdeps:
                            print '  skip', dep
                            keepit = False
                        else:
                            rec['note'].append(dep)
                            print '  ', dep
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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
