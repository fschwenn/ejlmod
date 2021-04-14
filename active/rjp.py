# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Romanian Journal of Physics
# FS 2017-06-27

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import ssl

ejdir = '/afs/desy.de/user/l/library/dok/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


publisher = 'Romanian Academy Publishing House'
year = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]

jnl = 'rjp'
jnlname = 'Rom.J.Phys.'

jnlfilename = '%s%s.%s' % (jnl, vol, issue)
xmlf = os.path.join(xmldir,jnlfilename+'.xml')

url = 'http://www.nipne.ro/%s/%s_%s_%s.html' % (jnl, year, vol, issue)

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

print "get table of content of %s%s.%s ... via %s" %(jnlname, vol, issue, url)
hdr = {'User-Agent' : 'Magic Browser'}
req = urllib2.Request(url, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))

tsection = ''
recs = []
for div in tocpage.body.find_all('div'):
    if div.has_attr('class'):
        if 'tsection' in div['class']:
            tsection = div.text.strip()
        elif 'docsource' in div['class']:
            for a in div.find_all('a'):
                if re.search('Full text', a.text):
                    rec['pdf'] = 'http://www.nipne.ro/rjp/' + a['href']
                    print '   [%s]' % (rec['pdf'])
        elif 'abstract' in div['class']:
            rec['abs'] = div.text.strip()
            recs.append(rec)
    elif div.has_attr('style') and div['style'] == 'vertical-align:top;text-align:left;':
        rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'year' : year, 
               'tc' : 'P', 'note' : [tsection], 'auts' : []}
        for span in div.find_all('span', attrs = {'class' : 'toct'}):
            rec['tit'] = span.text.strip()
        for span in div.find_all('span', attrs = {'class' : 'toca'}):
            authors = span.text.strip()
            for author in re.split(' *, *', authors):
                rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', author))
        for span in div.find_all('span', attrs = {'style' : 'font-size:8pt;'}):
            p1p2 = re.sub('[\r\n\t]', ' ', span.text.strip())            
            p1p2 = re.split('\-', re.sub('.*,.*?(\d+\-?\d+).*', r'\1', p1p2))
            rec['p1'] = p1p2[0]
            if len(p1p2) > 1:
                rec['p2'] = p1p2[1]
        print rec
    
        


xmlfile  = codecs.EncodedFile(open(xmlf,mode='wb'),"utf8")
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
