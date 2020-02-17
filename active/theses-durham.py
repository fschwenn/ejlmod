# -*- coding: utf-8 -*-
#harvest theses from University of Durham
#FS: 2019-09-26


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

publisher = 'Durham U.'

typecode = 'T'

jnlfilename = 'THESES-DURHAM-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for i in range(2):
    tocurl = 'http://etheses.dur.ac.uk/cgi/search/advanced?exp=0|1|-date/creators_name/title|archive|-|department_dur:department_dur:ANY:EQ:DDD21%20DDD25|thesis_qualification_name:thesis_qualification_name:ANY:EQ:PhD|-|eprint_status:eprint_status:ALL:EQ:archive|metadata_visibility:metadata_visibility:ALL:EX:show&_action_search=1&screen=Public::EPrintSearch&cache=9194761&search_offset=' + str(20*i)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for td in tr.find_all('td'):
            for span in td.find_all('span'):
                for a in td.find_all('a'):
                    rec['link'] = a['href']
                    rec['doi'] = '20.2000/' + re.sub('\W', '', a['href'])
                    recs.append(rec)

                
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i}---{ %s }------' % (i, len(recs), rec['link'])
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
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'eprints.creators_name':
                author = meta['content']
                author = re.sub(',', ';', author, count=1)
                author = re.sub(' *, *', ' ', author)
                author = re.sub(';', ',', author)
                rec['autaff'] = [[ author ]]
            #email
            elif meta['name'] == 'eprints.creators_id':
                rec['autaff'][-1].append('EMAIL:' + meta['content'])
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                 rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['FFT'] = meta['content']
    rec['autaff'][-1].append(publisher)


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
