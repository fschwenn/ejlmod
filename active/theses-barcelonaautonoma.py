# -*- coding: utf-8 -*-
#harvest Barcelona, Autonoma U.
#FS: 2021-01-08


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
rpp = 50
pages = 10

publisher = 'Barcelona, Autonoma U.'
hdr = {'User-Agent' : 'Magic Browser'}

departmentstoskip = ['e%20Biologia%20Cel%C2%B7lular%2C%20de%20Fisiologia%20i%20d%27Immunologia',
                     'e%20Did%C3%A0ctica%20de%20la%20Llengua%20i%20la%20Literatura%20i%20de%20les%20Ci%C3%A8ncies%20Socials',
                     'e%20Filologia%20Espanyola', 'e%20Psicologia%20Social',
                     'e%20Traducci%C3%B3%20i%20d%27Interpretaci%C3%B3%20i%20d%27Estudis%20de%20l%27%C3%80sia%20Oriental',
                     'e%20Telecomunicaci%C3%B3%20i%20Enginyeria%20de%20Sistemes',
                     '%27Hist%C3%B2ria%20Moderna%20i%20Contempor%C3%A0nia',
                     '%27Antropologia%20Social%20i%20Cultural',
                     'e%20Medicina', 'e%20Prehist%C3%B2ria',
                     'e%20Pediatria%2C%20d%27Obstetr%C3%ADcia%20i%20Ginecologia%20i%20de%20Medicina%20Preventiva',                     
                     'e%20Psiquiatria%20i%20de%20Medicina%20Legal',
                     'e%20Ci%C3%A8ncies%20de%20l%27Antiguitat%20i%20de%20l%27Edat%20Mitjana',
                     'e%20Filologia%20Anglesa%20i%20de%20German%C3%ADstica', 'e%20Filosofia',
                     'e%20Geografia', 'e%20Pedagogia%20Sistem%C3%A0tica%20i%20Social',
                     'e%20Psicologia%20B%C3%A0sica%2C%20Evolutiva%20i%20de%20l%27Educaci%C3%B3',
                     'e%20Psicologia%20Cl%C3%ADnica%20i%20de%20la%20Salut',
                     '%27Economia%20Aplicada', 'e%20Cirurgia', '%27Empresa',
                     '%27Antropologia%20Social%20i%20Prehist%C3%B2ria',
                     'e%20Biologia%20Cel%C2%B7lular%20i%20de%20Fisiologia',
                     'e%20Bioqu%C3%ADmica%20i%20Biologia%20Molecuar',
                     'e%20Ci%C3%A8ncia%20i%20Tecnologia%20Ambientals',
                     #'e%20Ci%C3%A8ncies%20de%20la%20Computaci%C3%B3',
                     'e%20Comunicaci%C3%B3%20Audiovisual%20i%20de%20Publicitat',
                     'e%20Did%C3%A0ctica%20de%20l%27Expressi%C3%B3%20de%20la%20M%C3%BAsica%2C%20Arts%20Pl%C3%A0stiques%20i%20l%27Educaci%C3%B3%20Corporal',
                     'e%20Did%C3%A0ctica%20i%20Organitzaci%C3%B3%20Educativa',
                     'e%20Patologia%20i%20de%20Producci%C3%B3%20Animals',
                     'e%20Psicologia%20de%20l%27Educaci%C3%B3',
                     'e%20Psicologia%20de%20la%20Salut%20i%20de%20Psicologia%20Social',
                     'e%20Publicitat%2C%20Relacions%20P%C3%BAbliques%20i%20Comunicaci%C3%B3%20Audiovisual',
                     'e%20Traducci%C3%B3%20i%20d%27Interpretaci%C3%B3',
                     'e%20Traducci%C3%B3%20i%20Filologia', '%27Infermeria',
                     '%27Economia%20de%20l%27Empresa', 'e%20Dret%20Privat',
                     '%27Enginyeria%20Qu%C3%ADmica%2C%20Biol%C3%B2gica%20i%20Ambiental',
                     'e%20Biologia%20Animal%2C%20de%20Biologia%20Vegetal%20i%20d%27Ecologia',
                     'e%20Bioqu%C3%ADmica%20i%20de%20Biologia%20Molecular',
                     'e%20Ci%C3%A8ncia%20Animal%20i%20dels%20Aliments',
                     'e%20Ci%C3%A8ncia%20Pol%C3%ADtica%20i%20de%20Dret%20P%C3%BAblic',
                     '%27Arquitectura%20de%20Computadors%20i%20Sistemes%20Operatius',
                     '%27Economia%20i%20d%27Hist%C3%B2ria%20Econ%C3%B2mica',
                     '%27Enginyeria%20de%20la%20Informaci%C3%B3%20i%20de%20les%20Comunicacions',
                     '%27Enginyeria%20Electr%C3%B2nica', '%27Art',
                     '%27Enginyeria%20Qu%C3%ADmica', 'e%20Geologia',
                     'e%20Ci%C3%A8ncies%20Morfol%C3%B2giques',
                     'e%20Comunicaci%C3%B3%20Audiovisual%20i%20Publicitat',
                     'e%20Did%C3%A0ctica%20de%20l%27Expressi%C3%B3%20Musical%2C%20Pl%C3%A0stica%20i%20Corporal',
                     'e%20Farmacologia%2C%20de%20Terap%C3%A8utica%20i%20de%20Toxicologia',
                     'e%20Microelectr%C3%B2nica%20i%20Sistemes%20Electr%C3%B2nics',
                     'e%20Pedagogia%20Aplicada', 'e%20Sociologia',
                     'e%20Psicobiologia%20i%20de%20Metodologia%20de%20les%20Ci%C3%A8ncies%20de%20la%20Salut',
                     'e%20Construccions%20Arquitect%C3%B2niques%20I',
                     'e%20Dret%20P%C3%BAblic%20i%20de%20Ci%C3%A8ncies%20Historicojur%C3%ADdiques',
                     'e%20Gen%C3%A8tica%20i%20de%20Microbiologia',
                     'e%20Medicina%20i%20Cirurgia%20Animals',
                     'e%20Mitjans%2C%20Comunicaci%C3%B3%20i%20Cultura',
                     'e%20Periodisme%20i%20de%20Ci%C3%A8ncies%20de%20la%20Comunicaci%C3%B3',
                     'e%20Sanitat%20i%20d%27Anatomia%20Animals',
                     '%27Art%20i%20de%20Musicologia', 'e%20Filologia%20Catalana',
                     'e%20Filologia%20Francesa%20i%20Rom%C3%A0nica', 'e%20Qu%C3%ADmica']
                     
recs = []
jnlfilename = 'THESES-BarcelonaAutonomaU-%s' % (stampoftoday)
for page in range(pages):
    tocurl = 'https://ddd.uab.cat/search?cc=tesis&ln=en&rg=' + str(rpp) + '&jrec=' + str(page*rpp+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for table in tocpage.body.find_all('table'):
        keepit = False
        for td in table.find_all('td', attrs = {'class' : 'dades'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'autaff' : [], 'supervisor' : []}
            for a in td.find_all('a'):
                if a.has_attr('href') and re.search('record\/\d', a['href']):
                    rec['link'] = 'https://ddd.uab.cat' + a['href']
                    rec['tit'] = a.text.strip()
                    keepit = True
        for a in table.find_all('a'):
            if a.has_attr('href') and re.search('p=Departament', a['href']):
                dep = re.sub('.*p=Departament%20d(.*?)\&.*', r'\1', a['href'])
                if dep in departmentstoskip:
                    keepit = False
                    #print '  skip "%s"' % (dep)
                else:
                    rec['note'].append(dep)
        if keepit:
            recs.append(rec)
    print '   %i records so far' % (len(recs))


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print 'no access to %s' % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):                
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #abstract
            elif meta['name'] == 'citation_abstract':
                if re.search(' the ', meta['content']):
                    rec['abs'] = meta['content']
                else:
                    rec['absspa'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #PDF
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            #ISBN
            elif meta['name'] == 'citation_isbn':
                rec['isbn'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
    rec['autaff'][-1].append(publisher)
    for tr in artpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'etiqueta'}):
            tddesc = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'text'}):
            tdt = td.text.strip()
            #pages
            if tddesc == 'Description:':
                if re.search('\d\d p.gines', tdt):
                    rec['pages'] = re.sub('.*?(\d\d+) p.*', r'\1', tdt)
            #license
            elif tddesc == 'Rights:':
                for a in td.find_all('a'):
                    if re.search('creativecommons', a['href']):
                        rec['license'] = {'url' : a['href']}
            #language
            elif tddesc == 'Language:':
                if re.search('Castel', tdt) or re.search('Catal', tdt):
                    rec['language'] = 'Catalan'
                elif re.search('Itali', tdt):
                    rec['language'] = 'Italian'
                elif re.search('Portug', tdt):
                    rec['language'] = 'Portuguese'
                elif re.search('Franc', tdt):
                    rec['language'] = 'French'
                elif not re.search('Angl', tdt):
                    rec['language'] = tdt
                    rec['note'].append('LANG='+tdt)
    #Handle
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('hdl.handle.net', a['href']):
            rec['hdl'] = re.sub('.*net\/', '', a['href'])
    #fulltext ?
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    #pseudoDOI ?
    if not 'hdl' in rec.keys():
        rec['doi'] = '20.2000/BarcelonaAutonomaU/' + re.sub('\D', '', rec['link'])
    #abstract
    if not 'abs' in rec.keys() and 'absspa' in rec.keys():
        rec['abs'] = rec['absspa']
    print '   ', rec.keys()

                    
                    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path,'a')
    retfiles.write(line)
    retfiles.close()
    

