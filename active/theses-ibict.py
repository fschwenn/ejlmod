# -*- coding: utf-8 -*-
#harvest theses from bdtd.ibict.br
#FS: 2020-01-06

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
retfiles_path = '/afs/desy.de/user/l/library/proc/retinspire/retfiles'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
startyear = now.year - 1
stopyear = now.year

subject = sys.argv[1]

filters = {'physics' : (2, 'dc.subject.por.fl_str_mv%3A%22F%C3%ADsica%22'),
          'math' : (1, 'dc.publisher.program.fl_str_mv%3A%22F%C3%ADsica%22'),
          'nucl' : (1, 'dc.subject.por.fl_str_mv%3A%22F%C3%ADsica+nuclear%22'),
          'physpost' : (3, 'dc.publisher.program.fl_str_mv%3A%22Programa+de+P%C3%B3s-Gradua%C3%A7%C3%A3o+em+F%C3%ADsica%22')}

hdr = {'User-Agent' : 'Magic Browser'}
publisher = 'publisher'

numberofpages = filters[subject][0]*5
recs = []
for i in range(numberofpages):
    tocurl = 'http://bdtd.ibict.br/vufind/Search/Results?filter%5B%5D=format%3A%22doctoralThesis%22&filter%5B%5D=' + filters[subject][1] + '&filter%5B%5D=publishDate%3A%22%5B' + str(startyear) + '+TO+' + str(stopyear) + '%5D%22&lookfor=%2A%3A%2A&type=AllFields&page=' + str(i+1)
    print '---{ %i/%i }---{ %s }---'  % (i+1, numberofpages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(10)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'result'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'notes' : []}
        for a in div.find_all('a', attrs = {'class' : 'title'}):
            rec['tit'] = a.text.strip()
            rec['artlink'] = 'http://bdtd.ibict.br' + a['href']
            rec['doi'] = '20.2000/IBICT/' + re.sub('\W', '', a['href'][15:])
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
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
    for table in artpage.body.find_all('table'):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                #date
                if tht == 'Data de Defesa:':
                    rec['date'] = td.text.strip()
                #author
                elif tht == 'Autor/a:':
                    rec['auts'] = [ td.text.strip() ]
                #language
                elif tht == 'Idioma:':
                    tdt = td.text.strip()
                    if tdt == 'por':
                        rec['language'] = 'portuguese'
                    elif tdt != 'eng':
                        rec['language'] = tdt
                        rec['notes'].append('language: '+tdt)
                #link
                elif tht == 'Download Texto Completo:':
                    for a in tr.find_all('a'):
                        rec['link'] = a['href']
                        if re.search('teses\.usp\.br', a['href']):
                            rec['notes'].append('should also be harvested by theses-saopaulo.py')
                        elif re.search('repositorio\.unesp\.br', a['href']):
                            rec['notes'].append('should also be harvested by theses-unsep.py')
                #aff
                elif re.search('Institui', tht):
                    rec['aff'] = [ td.text.strip() + ', Brasil' ]
                #keywords
                elif re.search('Assuntos em Ingl', tht):
                    for a in tr.find_all('a'):
                        rec['keyw'].append(a.text.strip())
                #abstract
                elif re.search('Resumo ingl', tht):
                    rec['abs'] = td.text.strip()
    #try direct link
    if 'link' in rec.keys():
        try:
            artpage2 = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(3)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage2 = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            except:
                print "no access to %s" % (rec['link'])
                continue
        for meta in artpage2.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
            rec['hidden'] = meta['content']
            print '      found PDF'
    else:
        rec['link'] = rec['artlink']        
    print rec.keys()

jnlfilename = 'THESES-IBICT-%s_%s' % (subject, stampoftoday)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, 'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path, 'a')
    retfiles.write(line)
    retfiles.close()
