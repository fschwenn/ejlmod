# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest journals from Siberian Federal U.
# FS 2017-07-17

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
def tfstrip(x): return x.strip()

publisher = 'Siberian Federal U., Krasnoyarsk'
hdr = {'User-Agent' : 'Mozilla/5.0'}

jnl = sys.argv[1]
vol = sys.argv[2]
issues = sys.argv[3]
if jnl == 'mp':
    jnlname = 'J.Sib.Fed.U.'
    starturl = 'http://journal.sfu-kras.ru/en/series/mathematics_physics'

    
jnlfilename = 'sibfed_%s.%s.%s' % (jnl, vol, re.sub(',', '_', issues))
def tfstrip(x): return x.strip()


print starturl
req = urllib2.Request(starturl, headers=hdr)
startpage = BeautifulSoup(urllib2.urlopen(req))

#searchterms to find toclink on startpage
searchterms = []
for issue in re.split(',', issues):
    searchterms.append((issue, re.compile('Vol. %s, Issue %s' % (vol, issue))))

tocurls = []
for div in startpage.body.find_all('div', attrs = {'class' : 'collapsed-content'}):
    for li in div.find_all('li'):
        lit = li.text.strip()
        year = re.sub('.*(20\d\d).*', r'\1', lit)
        for searchterm in searchterms:
            if searchterm[1].search(lit):
                for a in li.find_all('a'):
                    print ' -', lit
                    tocurls.append((searchterm[0], 'http://journal.sfu-kras.ru' + a['href']))

i = 0
prerecs = []
for (issue, tocurl) in tocurls:
    i += 1
    print '==={ %i/%i }==={ %s }===' % (i, len(tocurls), tocurl)
    time.sleep(2)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for ol in tocpage.body.find_all('ol', attrs = {'class' : 'articles'}):
        for li in ol.find_all('li'):
            rec = {'jnl' : jnlname, 'tc' : 'P', 'vol' : vol, 'issue' : issue, 'autaff' : [], 'year' : year}
            for strong in li.find_all('strong'):
                rec['tit'] = strong.text.strip()
            for a in li.find_all('a'):
                if a.text.strip() == 'abstract':
                     rec['artlink'] = 'http://journal.sfu-kras.ru' + a['href']
                     prerecs.append(rec)
i=0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(prerecs), rec['artlink'])
    artfilename = '/tmp/sibfed.%s' % (re.sub('\D', '', rec['artlink']))
    if not os.path.isfile(artfilename):
        time.sleep(2)
        os.system('wget  -T 300 -t 3 -q  -O %s %s' % (artfilename, rec['artlink']))
    artfil = codecs.EncodedFile(codecs.open(artfilename, mode='rb', errors='replace'), 'utf8')
    artlines = ''.join(map(tfstrip, artfil.readlines()))
    artfil.close()
    artlines = re.sub('.*<html', '<html', artlines)
    artpage = BeautifulSoup(artlines)
    try:
        artpage.body.find_all('a')
    except:
        print '!!! %s !!!' % (rec['artlink'])
        del rec        
        continue
    #req = urllib2.Request(rec['artlink'], headers=hdr)
    #artpage = BeautifulSoup(urllib2.urlopen(req))
    #FFT
    for a in artpage.body.find_all('a', attrs = {'class' : 'xfulltext'}):
        rec['hidden'] = a['href']
    for dl in artpage.body.find_all('dl'):
        for child in dl.children:
            try:
                child.name
            except:
                continue
            if child.name == 'dt':
                dtt = child.text.strip()
            elif child.name == 'dd':
                #authors
                if dtt == 'Contact information':
                    for script in child.find_all('script'):
                        script.replace_with('')
                    for autaff in re.split(' *; *', child.text.strip()):
                        if re.search(':', autaff):
                            parts = re.split(' *: *', autaff)
                            rec['autaff'].append([parts[0], parts[1]])
                #keywords
                elif dtt == 'Keywords':
                    rec['keyw'] = re.split('; ', child.text.strip())
                #abstract
                elif dtt == 'Abstract':
                    rec['abs'] = child.text.strip()
                #pages
                elif dtt == 'Pages':
                    rec['p1'] = re.sub('\D.*', '', child.text.strip())
                    rec['p2'] = re.sub('.*\D', '', child.text.strip())
                #DOI
                elif dtt == 'DOI':
                    rec['doi'] = child.text.strip()
                #link
                elif dtt == 'Paper at repository of SibFU' and not 'doi' in rec.keys():
                    rec['link'] = child.text.strip()
                    rec['doi'] = '20.2000/SibFed' + re.sub('.*handle', '', rec['link'])
                
    print '  ', rec.keys()
    recs.append(rec)


#write xml
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

