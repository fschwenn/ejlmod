# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest AIP-journals
# FS 2015-02-11

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'Global Science Press'

jnl = sys.argv[1]
vol = sys.argv[2]
iss = sys.argv[3]
jnlfilename = '%s%s.%s' % (jnl, vol, iss)

if jnl == 'cicp':
    jnlname = 'Commun.Comput.Phys.'
elif (jnl == 'jpde'):
    jnlname = 'J.Part.Diff.Eq.'
else:
    print ' does not know journal "%s"' % (jnl)


#get issue-page
tocurl = False
listurl = 'http://www.global-sci.com/%s/periodical_list.html' % (jnl)
print 'get list of issues via "%s"' % (listurl)
listpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(listurl))
for div in listpage.find_all('div', attrs = {'class' : 'periodical-catalog'}):
    for div2 in div.find_all('div'):
        div2t = div2.text.strip()
        if 'Volume %s, Issue %s ' % (vol, iss) in div2t:
            for a in div2.find_all('a'):
                tocurl = 'http://www.global-sci.com' + a['href']

#get TOC page
print 'get table of contents via "%s"' % (tocurl)
if not tocurl:
    print ' could not find TOC for %s' % (jnlfilename)
    sys.exit(0)
else:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'article-list-info'}):
    rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : iss, 'tc' : 'P', 'pacs' : []}
    #DOI
    for a in div.find_all('a', attrs = {'class' : 'doi'}):
        rec['doi'] = a.text.strip()
    #title
    for a in div.find_all('a', attrs = {'class' : 'article-list-title'}):
        rec['tit'] = a.text.strip()
        rec['artlink'] = 'http://www.global-sci.com' + a['href']
        recs.append(rec)

#get indiviual article pages
i = 0
repacs = re.compile('.*(\d\d\.\d\d\.[A-Za-z].).*')
regcr = re.compile('[\n\r\t]')
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---{ %s }---' % (i, len(recs), rec['doi'], rec['artlink'])
    time.sleep(3)
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #keywords
            if meta['name'] == 'keywords':
                rec['keyw'] = re.split(' *, *', meta['content'].strip())
    for div in artpage.body.find_all('div', attrs = {'class' : 'article-list-info'}):
        #authors and pages
        for div2 in div.find_all('div', attrs = {'class' : 'article-list-content'}):
            ps = div2.find_all('p')
            authors = regcr.sub(' ', ps[0].text.strip())
            pages = ps[1].text.strip()
            rec['auts'] = re.split(' *, *', re.sub(' and ', ', ', authors))
            rec['year'] = re.sub('.*\((\d+)\).*', r'\1', pages)
            rec['p1'] = re.sub('.*\).*?(\d+).*', r'\1', pages)
            if re.search('\).*\-', pages):
                rec['p2'] = re.sub('.*\-(\d+).*', r'\1', pages)
        for div2 in div.find_all('div', attrs = {'class' : 'authorization-title'}):
            #date
            for p in div2.find_all('p'):
                pt = regcr.sub(' ', p.text.strip())
                if re.search('Published online:', pt):
                    rec['date'] = re.sub('^\D*', '', pt)
            #PACS (there are some PACS 'hidden' in the AMS classification
            for a in div2.find_all('a'):
                if a.has_attr('href') and re.search('type=ams', a['href']):
                    at = regcr.sub(' ', a.text.strip())
                    if repacs.search(at):
                        rec['pacs'].append(repacs.sub(r'\1', at))
            #abstract
            for ul in div2.find_all('ul', attrs = {'class' : 'authorization-title-nav'}):
                if re.search('Abstract', ul.text):
                    for p in div2.find_all('p', attrs = {'class' : 'authorization-content'}):
                        rec['abs'] = p.text.strip()
                        if not rec['abs']:
                            rec['abs'] = re.sub('^ *Abstract', '', div2.text.strip())
    print rec.keys()




#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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
