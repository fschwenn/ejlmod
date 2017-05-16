# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Electronic Proceedings in Theoretical Computer Science
# FS 2016-01-06

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()


publisher = 'EPTCS'
confid = sys.argv[1]
#cnum = sys.argv[2]

jnlfilename = 'eptcs' + confid

url = 'http://eptcs.web.cse.unsw.edu.au/content.cgi?' + confid
print url

tocpage = BeautifulSoup(urllib2.urlopen(url))

artlinks = []
for a in tocpage.body.find_all('a'):
    if a.has_key('href') and re.search('^paper.cgi', a['href']):
        artlinks.append('http://eptcs.web.cse.unsw.edu.au/' + a['href'])

print 'found %i links to articles' % (len(artlinks))

typecode = 'C'
recs = []
for artlink in artlinks:
    rec = {'jnl' : 'EPTCS', 'autaff' : [], 'tc' : typecode}
    if len(sys.argv) > 2:
        rec['cnum'] = sys.argv[2]
    print ' ', artlink
    artpage = BeautifulSoup(urllib2.urlopen(artlink))
    for meta in artpage.head.find_all('meta'):
        if meta.attrs.has_key('name'):
            if meta['name'] == 'citation_publication_data':
                rec['date'] = re.sub('\/', '-', meta['content'])
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    #title
    for h2 in artpage.body.find_all('h2'):
        rec['tit'] = h2.text
    #tables
    tables = artpage.body.find_all('table')
    #authors
    for td in tables[0].find_all('td'):
        for font in td.find_all('font'):
            if font.has_key('color') and font['color'] == 'darkblue':
                for font2 in font.find_all('font'):
                    if font2['color'] == 'blue':
                        surname = font2.text
                    font2.replace_with('')
                givenname = font.text.strip()
                autaff = ['%s, %s' % (surname, givenname)]
            elif font.has_key('size'):
                autaff.append(re.sub('^\((.*)\)$', r'\1', font.text))
        rec['autaff'].append(autaff)
    #abstract
    rec['abs'] = tables[1].text.strip()
    #unique ids
    for a in tables[2].find_all('a'):
        if a.has_key('href'):
            if re.search('arxiv.org', a['href']):
                rec['arxiv'] = re.sub('.*\/', '', a['href'])
            elif re.search('dx.doi.org', a['href']):
                rec['doi'] = re.sub('.*dx.doi.org.', '', a['href'])
    #print rec
    recs.append(rec)


xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
