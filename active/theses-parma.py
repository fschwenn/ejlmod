# -*- coding: utf-8 -*-
#harvest theses from Parma U.
#FS: 2020-08-31


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

publisher = 'Parma U.'


recs = []
jnlfilename = 'THESES-PARMA-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'http://dspace-unipr.cineca.it/handle/1889/636/browse?type=dateissued&sort_by=2&order=DESC&rpp=100&etal=0&submit_browse=Update'
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
for table in tocpage.body.find_all('table', attrs = {'class' : 'miscTable'}):
    for tr in table.find_all('tr'): 
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'supervisor' : [], 'keyw' : []}
        for td in tr.find_all('td', attrs = {'headers' : 't2'}):
            rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', td.text.strip())
        for td in tr.find_all('td', attrs = {'headers' : 't3'}):
            for a in td.find_all('a'):
                rec['artlink'] = 'http://dspace-unipr.cineca.it' + a['href'] 
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                if int(rec['year']) >= now.year - 1:
                    recs.append(rec)

i = 0
for rec in recs:
    interesting = True
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_authors':
                rec['autaff'] = [[ meta['content'] ]]
            #email
            elif meta['name'] == 'citation_author_email':
                rec['autaff'][-1].append('EMAIL:' + meta['content'])
            #ORCID
            elif meta['name'] == 'citation_author_orcid':
                rec['autaff'][-1].append('ORCID:' + meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' (the|of|and) ', meta['content']):
                    rec['abs'] = meta['content']
            #thesis type
            elif meta['name'] == 'DC.type':
                rec['note'].append(meta['content'])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'Italiano':
                    rec['language'] = 'italian'
            #keywords
            elif meta['name'] == 'citation_keywords':
                for part in re.split('[;,] ', meta['content']):
                    if re.search('^[A-Z][A-Z][A-Z]\/\d+', part):
                        rec['note'].append(part)
                    else:
                        rec['keyw'].append(part)
            #supervisor
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([meta['content']])

        #FFT
        for td in artpage.body.find_all('td', attrs = {'class' : 'standard'}):
            for a in td.find_all('a'):
                if re.search('pdf$', a['href']):
                    rec['pdflink'] = 'http://dspace-unipr.cineca.it' + a['href']        
    rec['autaff'][-1].append(publisher)
    #license            
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['licence'] = {'url' : a['href']}
    if 'pdflink' in rec.keys():
        if 'licence' in rec.keys():
            rec['FFT'] = rec['pdflink']
        else:
            rec['hidden'] = rec['pdflink']
    print '    ', rec.keys()

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
