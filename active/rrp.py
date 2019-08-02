# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Romanian Reports in Physics
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



ejdir = '/afs/desy.de/user/l/library/dok/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


publisher = 'Romanian Academy Publishing House'
year = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]

jnl = 'rrp'
jnlname = 'Rom.Rep.Phys.'

jnlfilename = '%s%s.%s' % (jnl, vol, issue)
xmlf = os.path.join(xmldir,jnlfilename+'.xml')

url = 'http://rrp.infim.ro/%s_%s_%s.html' % (year, vol, issue)

print "get table of content of %s%s.%s ... via %s" %(jnlname, vol, issue, url)
tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(url))

tsection = ''
recs = []
done = []
for table in tocpage.body.find_all('table', attrs = {'dwcopytype' : 'CopyTableRow'}):
    for tr in table.find_all('tr'):
        for font in tr.find_all('font', attrs = {'color' : '#ff0000'}):
            fonttext = font.text.strip()
            if fonttext:
                tsection = fonttext
        for b in tr.find_all('b', attrs = {'class' : 'tocTitle'}):
            rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'year' : year,
                   'tc' : 'P', 'note' : [tsection], 'auts' : []}
            rec['tit'] = b.text.strip()
        for div in tr.find_all('div'):
            for i1 in div.find_all('i'):
                i1.replace_with('')
                rec['abs'] = re.sub('[\n\t\r ]+', ' ', div.text.strip())
        for i2 in tr.find_all('i', attrs = {'class' : 'tocAuth'}):
            authors = i2.text.strip()
            for author in re.split(' *, *', authors):
                rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', author))
        for td in tr.find_all('td', attrs = {'width' : '60%'}):
            for a in td.find_all('a'):
                rec['pdf'] = 'http://www.rrp.infim.ro/' + re.sub('^\.\/', '', a['href'])
                rec['p1'] = re.sub('.*? (\d+).*', r'\1', re.sub('[\n\t\r]', '', td.text.strip()))
                if rec['p1'] not in done:
                    recs.append(rec)
                    done.append(rec['p1'])

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
