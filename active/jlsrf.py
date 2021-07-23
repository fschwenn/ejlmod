# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Journal of large-scale research facilities
# FS 2017-09-11

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Forschungszentrum Julich'
view = sys.argv[1]
jnlfilename = 'jlsrf.%s_%s' % (view, stampoftoday)

    
urltrunk = 'http://jlsrf.org/index.php/lsf/issue/view/%s' % (view)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))


recs = []
(sec, subsec) = (False, False)
for div in tocpage.body.find_all('div', attrs = {'class' : 'tocTitle'}):
    for a in div.find_all('a'):
        rec = {'jnl' : 'JLSRF', 'tc' : '', 'autaff' : [],
               'refs' : []}
        artlink = a['href']
        try:
            print artlink
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (artlink)
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                if meta['name'] == 'DC.Identifier.DOI':
                    rec['doi'] = meta['content'] 
                elif meta['name'] == 'citation_date':
                    rec['date'] = meta['content'] 
                elif meta['name'] == 'DC.Description':
                    rec['abs'] = meta['content'] 
                elif meta['name'] == 'DC.Rights':
                    rec['licence'] = {'url' : meta['content']}
                elif meta['name'] == 'DC.Title':
                    rec['tit'] = meta['content'] 
                elif meta['name'] == 'citation_volume':
                    rec['vol'] = meta['content'] 
                elif meta['name'] == 'citation_author':
                    rec['autaff'].append([meta['content']])
                elif meta['name'] == 'citation_author_institution':
                    rec['autaff'][-1].append(meta['content'])
                elif meta['name'] == 'citation_firstpage':
                    rec['p1'] = 'A' + meta['content'] 
                elif meta['name'] == 'citation_pdf_url':
                    if not rec.has_key('FFT'):
                        rec['FFT'] = meta['content'] 
        for refs in artpage.body.find_all('div', attrs = {'id' : 'articleCitations'}):
            for p in refs.find_all('p')[:-1]:
                rec['refs'].append([('x', p.text)])
        recs.append(rec)
        #print rec






                                       
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
 
