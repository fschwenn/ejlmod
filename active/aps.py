#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest APS-journals
# FS 2017-08-15

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import time
import urllib2
import urlparse
import time
import datetime
from bs4 import BeautifulSoup

tmpdir = '/tmp'
def tfstrip(x): return x.strip()
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'APS'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]
jnlfilename = 'aps_%s%s.%s_%s' % (jnl, vol, issue, stampoftoday)

if   (jnl == 'pra'): 
    issn = '1094-1622'
    jnlname = "Phys.Rev."
    jvol = "A"+vol
elif (jnl == 'prb'): 
    issn = '1550-235X'
    jnlname = "Phys.Rev."
    jvol = "B"+vol
elif (jnl == 'prc'):
    issn = '1089-490X' 
    jnlname = "Phys.Rev."
    jvol = "C"+vol
elif (jnl == 'prd'):
    issn = '1550-2368' 
    jnlname = "Phys.Rev."
    jvol = "D"+vol
elif (jnl == 'pre'): 
    issn = '1550-2376'
    jnlname = "Phys.Rev."
    jvol = "E"+vol
elif (jnl == 'prx'): 
    issn = '2160-3308'
    jnlname = "Phys.Rev."
    jvol = "X"+vol
elif (jnl == 'prl'):
    issn = '1079-7114' 
    jnlname = "Phys.Rev.Lett."
    jvol = vol
elif (jnl == 'rmp'):
    issn = '1539-0756' 
    jnlname = "Rev.Mod.Phys."
    jvol = vol
elif (jnl == 'prab'):
    issn = '1098-4402' 
    jnlname = "Phys.Rev.Accel.Beams"
    jvol = vol

#check for DOIs that have been processed already to avoid traffic 
donedois = []
reducedoi = re.compile('.*URLDOC=(.*?);.*')
for doi in os.popen("grep URL=DOI %s/onhold/*aps*doki" % (ejldir)).readlines():
    donedois.append(reducedoi.sub(r'\1', doi.strip()))
for doi in os.popen("grep URL=DOI %s/backup/*aps*doki" % (ejldir)).readlines():
    donedois.append(reducedoi.sub(r'\1', doi.strip()))
print '%i DOIs already done' % (len(donedois))

toclink = 'https://journals.aps.org/%s/issues/%s/%s' % (jnl, vol, issue)

try:
    tocpage = BeautifulSoup(urllib2.urlopen(toclink))
except:
    print '%s not found' % (toclink)
    sys.exit(0)

subject = ''
recs = []
for div in tocpage.find_all('div', attrs = {'class' : 'search-results'}):
    for child in div.contents:
        if type(child) == type(div):
            if child.name == 'h2':
                subject = child.text
            elif child.name == 'div' and subject != 'HIGHLIGHTED ARTICLES':
                #information from toc page
                rec = {'jnl' : jnlname, 'vol' : jvol, 'issue' : issue, 'note' : [subject],
                       'autaff' : [], 'tc' : 'P'}
                autaff = False
                rec['doi'] = child['data-id']
                for h5 in child.find_all('h5'):
                    for a in h5.find_all('a'):
                        rec['tit'] = a.text      
                        rec['artlink'] = 'https://journals.aps.org' + a['href']
                #information from articlepage
                if rec['doi'] in donedois:
                    print '%s already done' % (rec['doi'])
                    continue
                print rec['doi']
                recs.append(rec)
            elif child.name == 'section' and subject != 'HIGHLIGHTED ARTICLES':
                for child2 in child.contents:
                    if type(child2) == type(div):
                        if child2.name == 'h4':
                            subject = child2.text
                        elif child2.name == 'div' and subject != 'HIGHLIGHTED ARTICLES':
                            #information from toc page
                            rec = {'jnl' : jnlname, 'vol' : jvol, 'issue' : issue, 'note' : [subject],
                                   'autaff' : [], 'tc' : 'P'}
                            autaff = False
                            for div2 in child2.find_all('div', attrs = {'class' : 'article panel article-result'}):
                                rec['doi'] = div2['data-id']
                            for h5 in child2.find_all('h5'):
                                for a in h5.find_all('a'):
                                    rec['tit'] = a.text      
                                    rec['artlink'] = 'https://journals.aps.org' + a['href']
                            #information from articlepage
                            if rec['doi'] in donedois:
                                print '%s already done' % (rec['doi'])
                                continue
                            print rec['doi']
                            recs.append(rec)



for rec in recs:
    artpage = BeautifulSoup(urllib2.urlopen(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            #autaff
            elif meta['name'] == 'citation_author':
                if autaff:
                    rec['autaff'].append(autaff)
                autaff = [ meta['content'] ]
            elif meta['name'] == 'citation_author_institution':
                autaff.append(meta['content'])
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                autaff.append('ORCID:%s' % (orcid))
            elif meta['name'] == 'citation_author_email':
                email = meta['content']
                autaff.append('EMAIL:%s' % (email))    
    #abstract
    for abstr in artpage.body.find_all('div', attrs = {'class' : 'content', 'data-loaded' : 'yes'}):
        for p in abstr.find_all('p'):
            if not rec.has_key('abs'):
                rec['abs'] = p.text
    #authors if not in meta
    if not rec['autaff']:
        for h5 in artpage.body.find_all('h5', attrs = {'class' : 'authors'}):
            authors = re.sub(' *et al\.', '', h5.text)
            rec['autaff'].append([re.sub('(.*) (.*)', r'\2, \1', authors)])
    print rec
    time.sleep(185)
    

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








