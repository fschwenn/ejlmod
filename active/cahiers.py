# -*- coding: utf-8 -*-
#harvest theses from Cahiers de Topologie et Geometrie Differentielle
#FS: 2020-10-20


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

publisher = 'Cahiers'

numofvolumes = 2
hdr = {'User-Agent' : 'Magic Browser'}

tocurl = 'http://cahierstgdc.com/index.php/volumes/'
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
volurls = []
for li in tocpage.body.find_all('li', attrs = {'class' : 'menu-item'}):
    lit = li.text.strip()
    if re.search('^Volume', lit):
        if len(volurls) < numofvolumes:
            for a in li.find_all('a'):
                volurls.append(a['href'])

def roman_to_int(s):
    rom_val = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_val = 0
    for i in range(len(s)):
        if i > 0 and rom_val[s[i]] > rom_val[s[i - 1]]:
            int_val += rom_val[s[i]] - 2 * rom_val[s[i - 1]]
        else:
            int_val += rom_val[s[i]]
    return int_val
    
for volurl in volurls:
    print '==={ %s }===' % (volurl)
    recs = []
    req = urllib2.Request(volurl, headers=hdr)
    volpage = BeautifulSoup(urllib2.urlopen(req))
    year = re.sub('.*(\d\d\d\d).*', r'\1', volpage.title.text.strip())
    vol = str(roman_to_int(re.sub('Volume ([A-Z]+) .*', r'\1', volpage.title.text.strip())))
    issue = False
    for div in volpage.body.find_all('div', attrs = {'class' : 'entry-content'}):
        for p in div.find_all('p'):
            for a in p.find_all('a'):
                at = a.text.strip()
                if not at: continue
                if re.search('^Issue.*\d$', at):
                    issue = at[-1]
                    print '---{ %s.%s }---' % (vol, issue)
                else:
                    print ' ', at
                    rec = {'jnl' : 'Cahiers Topo.Geom.Diff.', 'year' : year, 'tc' : 'P', 'vol' : vol}
                    if issue: rec['issue'] = issue
                    rec['FFT'] = a['href']
                    rec['pdf'] = a['href']
                    rec['tit'] = at
                    a.decompose()
                    for br in p.find_all('br'):
                       br.replace_with(' XXX ')
                    parts = re.split(' *XXX ', re.sub('[\n\t\r]', ' ', p.text.strip()))
                    print ' ', parts
                    #pages
                    rec['p1'] = re.sub('.*?(\d+)\-.*', r'\1', parts[1].strip())
                    rec['p2'] = re.sub('.*\-', '', parts[1].strip())
                    #authors
                    rec['auts'] = re.split(', ', parts[2].strip())
                    recs.append(rec)
                    print '   ', rec.keys()
    jnlfilename = 'cahierstgd%s-%s' % (vol, stampoftoday)
    time.sleep(2)

    #closing of files and printing
    xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
