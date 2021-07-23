# -*- coding: utf-8 -*-
#harvest theses from Padua U.
#FS: 2020-03-16


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Padua U.'

scuolae = ['astronomia', 'fisica', 'matematica', 'fisicaord2014']
startyear = now.year - 1

recs = []
jnlfilename = 'THESES-PADUA-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}
for scuola in scuolae:
    tocurl = 'http://tesi.cab.unipd.it/view/facoltacdltriennale/facoltacdltriennalescuoladiscienze%s.html' % (scuola)
    print '---{ %s }---{ %s }------' % (scuola, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    for p in tocpage.body.find_all('p'):
        for span in p.find_all('span', attrs = {'class' : 'person_name'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [scuola], 'supervisor' : []}
            rec['autaff'] = [[ span.text.strip() ]]
            for a in p.find_all('a'):
                rec['link'] = a['href']
                rec['doi'] = '20.2000/Padua/' + re.sub('\D', '', a['href'])
                rec['tit'] = a.text.strip()
            pt = p.text.strip()
            if re.search('\([12]\d\d\d\)', pt):
                rec['year'] = re.sub('.*\(([12]\d\d\d).*', r'\1', pt)
                if int(rec['year']) < startyear:
                    print '  %s is too old' % (rec['year'])
                else:
                    recs.append(rec)
            else:
                print '  unknown year?!'
                recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
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
        if meta.has_attr('name') and meta.has_attr('content'):
            #keywords
            if meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #date
            elif meta['name'] == 'DC.date':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['hidden'] = meta['content']
    rec['autaff'][-1].append(publisher)
    for tr in artpage.body.find_all('tr'):
        for th in tr.find_all('th'):
            tht = th.text.strip()
        for td in tr.find_all('td'):
            if re.search('Relatore', tht):
                rec['supervisor'].append([td.text.strip()])






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
