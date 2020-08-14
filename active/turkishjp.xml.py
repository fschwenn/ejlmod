#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Turkish Journal of Physics 
# FS 2015-08-26

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
import time



ejdir = '/afs/desy.de/user/l/library/dok/ejl'
tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

def tfstrip(x): return x.strip()

publisher = u'TÜBİTAK'
#publisher = 'TUBITAK'
jnl = sys.argv[1]
vol = sys.argv[2]
year = str(int(vol)+1976)
issue = sys.argv[3]

if   (jnl == 'tjp'):
    jnlname = 'Turk.J.Phys.'
    issn = "0019-5596"
    urlkey = 'physics'
    oldurlkey = 'fiz'
elif (jnl == 'tjm'):
    urlkey = 'math'
    oldurlkey = 'mat'
    jnlname = 'Turk.J.Math.'
    issn = "1300-0098"


#get issue-ID
page = BeautifulSoup(urllib2.urlopen('http://journals.tubitak.gov.tr/%s/archive.htm' % (urlkey)))
issueID = False
for li in page.body.find_all('li'):
    for a in li.find_all('a'):
        try:
            if re.search('Volume. '+vol, a.string) and re.search('Number '+issue, a.string):
                issueID = a['href']
        except:
            pass
if not issueID:
    print 'Issue not found'
    sys.exit(0)


print 'get table of content from http://journals.tubitak.gov.tr/%s/%s' % (urlkey, issueID)
page = BeautifulSoup(urllib2.urlopen('http://journals.tubitak.gov.tr/%s/%s' % (urlkey, issueID)))

recs = []
for div in page.body.find_all('div', attrs = {'class' : 'panel-body'}):
    for li in div.find_all('li'):
        rec = {'jnl' : jnlname, 'tc' : 'P', 'vol' : vol, 'issue' : issue, 'year' : year, 'auts' : []}
        divs = li.find_all('div', attrs = {'class' : 'rowhilite'})
        for strong in divs[0].find_all('strong'):
            rec['tit'] = strong.text.strip()
        authors = divs[1].string
        for aut in re.split(', ', authors.strip()):
            rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1',aut))
        if len(divs) < 4:
            continue
        for a in divs[3].find_all('a'):
            if re.search('pdf$', a['href']):
                rec['link'] = a['href']
                rec['doi'] = re.sub('.*\/(.*?)\.pdf',r'\1',rec['link'])
                rec['doi'] = '10.3906/'+oldurlkey+'-'+re.sub('.*?\-(\d\d\d\d.*)',r'\1',rec['doi'])
            else:
                abstract = BeautifulSoup(urllib2.urlopen(a['href']))
                for meta in abstract.head.find_all('meta'):
                    if meta.has_attr('name'):
                        if meta['name'] == 'citation_keywords':
                            rec['keyw'] = re.split(', ', meta['content'])
                        if meta['name'] == 'citation_publication_date':
                            rec['date'] = meta['content']
                        if meta['name'] == 'citation_firstpage':
                            rec['p1'] = meta['content']
                        if meta['name'] == 'citation_lastpage':
                            rec['p2'] = meta['content']
                for diva in abstract.body.find_all('div', attrs = {'class' : 'panel-body'}):
                    ps = diva.find_all('p', attrs = {'align' : 'justify'})
                    #print ps[1]
                    #print ps[1].text
                    rec['abs'] = re.sub('Abstract.', '', ps[1].text).strip()
        print rec.keys()
        recs.append(rec)


jnlfilename = jnl+vol+'.'+issue



xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
