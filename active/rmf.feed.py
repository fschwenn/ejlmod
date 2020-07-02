#program to translate feeds from "Revista Mexicana de Fisica"
# -*- coding: UTF-8 -*-
## FS 2020-06-01

import os
import ejlmod2
import codecs
import re
import sys
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import base64

tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
pdfpath = '/afs/desy.de/group/library/publisherdata/pdf'
rmfpath = '/afs/desy.de/group/library/publisherdata/RMF'
jnl = 'Rev.Mex.Fis.'

def tfstrip(x): return x.strip()

publisher = 'Sociedad Mexicana de Fisica'

datei = sys.argv[1]
vol = re.sub('.*?_(\d+).*', r'\1', datei)
issue = re.sub('.*?_\d+_(\d+).*', r'\1', datei)
year = re.sub('.*_([12]\d\d\d).*', r'\1', datei)
jnlfilename = 'rmf' + re.sub('.xml$', '', datei)

inf = os.path.join(rmfpath, datei)
xmlfile  = codecs.EncodedFile(codecs.open(inf,mode='rb'),'utf8')
lines = xmlfile.readlines()
xmlfile.close()

feed = BeautifulSoup(''.join(lines))

recs = []
for article in feed.find_all('article'):
    for sf in article.find_all('supplemental_file'):
        sf.decompose()
    rec = {'jnl' : jnl, 'tc' : 'P', 'keyw' : [], 'autaff' : [],
           'vol' : vol, 'year' : year, 'issue' : issue}
    #DOI
    for id in article.find_all('id', attrs = {'type' : 'doi'}):
        rec['doi'] = id.text.strip()
    #title
    for title in article.find_all('title'):
        rec['tit'] = title.text.strip()
    #abstract
    for abstract in article.find_all('abstract'):
        rec['abs'] = abstract.text.strip()
    #keywords
    for indexing in article.find_all('indexing'):
        for subject in indexing.find_all('subject'):
            rec['keyw'] += re.split('[,;] ', subject.text.strip())
    #authors
    for author in article.find_all('author'):
        for ln in author.find_all('lastname'):
            aut = ln.text
        for fn in author.find_all('firstname'):
            aut += ', ' + fn.text
        rec['autaff'].append([aut])
        for aff in author.find_all('affiliation'):
            rec['autaff'][-1].append(re.sub('[\r\n\t]', ' ', aff.text.strip()))
    #pages
    for pages in article.find_all('pages'):
        rec['p1'] = re.sub('\-.*', '', pages.text)
        rec['p2'] = re.sub('.*\-', '', pages.text)
    #date
    for date in article.find_all('date_published'):
        rec['date'] = date.text
    #licence
    for lic in article.find_all('license_url'):
        rec['license'] = {'url' : lic.text}
    #PDF
    for galley in article.find_all('galley'):
        for embed in galley.find_all('embed', attrs = {'mime_type' : 'application/pdf'}):
            ouf = open('%s/%s.pdf' % (pdfpath, re.sub('\/', '_', rec['doi'])), 'wb', 0)
            ouf.write(base64.decodestring(embed.text))
            ouf.close()
    print rec['doi'], rec.keys()
    print rec
    recs.append(rec)



xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#xmlfile  = open(xmlf,'w')
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



#done
os.system('mv %s/%s %s/done/' % (rmfpath, datei, rmfpath))








