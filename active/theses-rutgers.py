# -*- coding: utf-8 -*-
#harvest theses from Rutgers
#FS: 2019-09-15


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

publisher = 'Rutgers U.'

typecode = 'T'

jnlfilename = 'THESES-RUTGERS-%s' % (stampoftoday)
recs = []
hdr = {'User-Agent' : 'Magic Browser'}

for page in range(5):
    tocurl = 'https://rucore.libraries.rutgers.edu/search/results/?orderby=datedesc&ppage=50&numresults=50&key=ETD-RU&start=%i' % (50*page + 1)
    print '---{ %i }---{ %s }---' % (page, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'result__result-entry brief'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://rucore.libraries.rutgers.edu' + a['href']
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
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_author':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Rutgers U., Piscataway (main)')
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw.strip())
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = re.sub('doi:', '', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    for div in artpage.body.find_all('div', attrs = {'class' : 'result__result-field full'}):
        for span in div.find_all('span', attrs = {'class' : 'resultFull__result-title'}):
            if span.text == 'Description':
                for span2 in div.find_all('span', attrs = {'class' : 'resultFull__result-text'}):
                    rec['abs'] = span2.text.strip()
            elif span.text == 'Graduate Program':
                for span2 in div.find_all('span', attrs = {'class' : 'resultFull__result-text'}):
                    rec['note'] = [ span2.text.strip() ]


recsdict = {}
for rec in recs:
    if 'note' in rec.keys():
        program = re.sub('\W', '_', rec['note'][0])
    elif rec['keyw']:
        program = re.sub('\W', '_', rec['keyw'][0])
    else:
        program = 'No_Program'
    if program in recsdict.keys():
        recsdict[program].append(rec)
    else:
        recsdict[program] = [rec]


#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()


        
#for program in recsdict.keys():
#    print '%3i %s' % (len(recsdict[program]), program)
#    jnlfilename = 'THESES-RUTGERS-%s-%s' % (stampoftoday, program)

#    #closing of files and printing
#    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#    ejlmod2.writeXML(recsdict[program], xmlfile, publisher)
#    xmlfile.close()
#    #retrival
#    retfiles_text = open(retfiles_path,"r").read()
#    line = jnlfilename+'.xml'+ "\n"
#    if not line in retfiles_text: 
#        retfiles = open(retfiles_path,"a")
#        retfiles.write(line)
#        retfiles.close()
