# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest PROBLEMS OF ATOMIC SCIENCE AND TECHNOLOGY
# FS 2012-06-01

import os
import ejlmod2
import codecs
import re
import sys
import unicodedata
import string
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejdir = '/afs/desy.de/user/l/library/dok/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'


publisher = 'Kharkov Institute of Physics and Technology'
year = sys.argv[1]
issue = sys.argv[2]

jnl = 'past'
jnlname = 'Prob.Atomic Sci.Technol.'
issn = '1562-6016'
jnlfilename = jnl+year+'.'+issue


urltrunk = 'http://vant.kipt.kharkov.ua'

recs = []
recnr = 1
print "get table of content ..."
tocurl = '%s/CONTENTS/CONTENTS_%s_%s.html' % (urltrunk, year, issue)
hdr = {'User-Agent' : 'Magic Browser'}

req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
section = False
recs = []
for tr in tocpage.body.find_all('tr'):
    for h1 in tr.find_all('h1'):
        section = h1.text.strip()
    for h3 in tr.find_all('h3'):
        rec = {'jnl' : jnlname, 'vol' : year, 'year' : year, 'issue' : issue,
               'note' : [], 'tc' : 'P', 'auts' : []}
        if section: rec['note'].append(section)
        #title
        rec['tit'] = re.sub('  ', ' ', re.sub('[\n\t\r]', ' ', h3.text.strip()))
        for a in tr.find_all('a'):
            if a.has_attr('href'):
                #detailed page
                if re.search('html$', a['href']):
                    rec['link'] = 'https://vant.kipt.kharkov.ua' +  a['href'][2:]
                #fulltext
                elif re.search('pdf$', a['href']):
                    rec['FFT'] = 'https://vant.kipt.kharkov.ua' +  a['href'][2:]
        for p in tr.find_all('p'):
            #pages
            pages = re.sub('.*\(\D*(.*?)\).*', r'\1', re.sub('[\t\n\r]', '', p.text.strip()))
            rec['p1'] = re.sub('^(\d+) *\- *(\d+)',r'\1',pages)
            rec['p2'] = re.sub('^(\d+) *\- *(\d+)',r'\2',pages)
            #auts
            auts = re.sub('\(.*', '', re.sub('[\t\n\r]', '', p.text.strip())).strip()
            for aut in re.split(', *', auts):
                rec['auts'].append(re.sub('\.([A-Z][a-z])', r'. \1', aut))
        if 'p2' in rec.keys() and 'p1' in rec.keys():
            print "%s %s (%s) %s-%s" % (jnlname, rec['vol'], year, rec['p1'], rec['p2'])
        if 'link' in rec.keys():
            recs.append(rec)
        else:
            print '   ... no link!?'

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['link'])
    time.sleep(2)
    req = urllib2.Request(rec['link'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))
    for p in artpage.find_all('p', attrs = {'align' : 'justify'}):
        if not 'abs' in rec.keys():
            pt =  re.sub('[\t\n\r]', ' ', p.text.strip())
            #pacs
            if re.search('PACS:', pt):
                pacs = re.sub('.*PACS: *', '', pt)
                rec['pacs'] = re.split(', *', pacs)
                pt = re.sub('PACS:.*', '', pt)
                pt = re.sub('PACS:.*', '', pt)
            #abs
            if len(pt) > 10:
                rec['abs'] = pt
    print rec.keys()
        

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
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
 
