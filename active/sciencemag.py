# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Science
# FS 2020-11-24

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
import ssl
import os
import datetime


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'

publisher = 'American Association for the Advancement of Science'
year = sys.argv[1]
#vol = sys.argv[1]
#issue = sys.argv[2]
now = datetime.datetime.now()
hdr = {'User-Agent' : 'Magic Browser'}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

def getissuenumbers(year):
    issues = []
    tocurl = 'https://science.sciencemag.org/content/by/year/%s' % (year)
    tocreq = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(tocreq, context=ctx), features="lxml")
    for div in tocpage.find_all('div', attrs = {'class' : 'archive-issue-list'}):
        for a in div.find_all('a', attrs = {'class' : 'highwire-cite-linked-title'}):
            vol = re.sub('.*tent\/(\d+).*', r'\1', a['href'])
            issue = re.sub('.*\/(\d+).*', r'\1', a['href'])
            issues.append((vol, issue))
    print 'available', issues
    return issues

def getdone():
    regscience = re.compile('science\d+\.\d+')
    ejldir = '/afs/desy.de/user/l/library/dok/ejl'
    issues = []
    for directory in [ejldir+'/onhold', ejldir+'/backup', ejldir+'/backup/' + str(now.year-1)]:
        for datei in os.listdir(directory):
            if regscience.search(datei):
                vol = re.sub('.*science(\d+).*', r'\1', datei)
                issue = re.sub('.*science\d+\.(\d+).*', r'\1', datei)
                issues.append((vol, issue))
    print 'done', issues
    return issues

def harvestissue(vol, issue):
    jnlname = 'Science'
    tocurl = 'https://science.sciencemag.org/content/%s/%s' % (vol, issue)
    print "get table of content of %s %s.%s via %s ..." % (jnlname, vol, issue, tocurl)
    tocreq = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(tocreq, context=ctx), features="lxml")
    for meta in tocpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            if meta['name'] == 'citation_publication_date':
                year = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
    recs = []
    for li in tocpage.find_all('li', attrs = {'class' : ['issue-toc-section-review', 'issue-toc-section-research-articles', 'issue-toc-section-reports']}):
        for article in li.find_all('article'):
            for h3 in article.find_all('h3'):
                for a in h3.find_all('a'):
                    rec = {'tc' : 'P', 'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'year' : year, 'autaff' : []}
                    rec['artlink'] = 'https://science.sciencemag.org' + a['href']
                    recs.append(rec)
    #check article pages
    i = 0
    for rec in recs:
        i += 1
        print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
        try:
            time.sleep(30)
            pagreq = urllib2.Request(rec['artlink'], headers=hdr)
            page = BeautifulSoup(urllib2.urlopen(pagreq), features="lxml")
        except:
            print "retry in 180 seconds"
            time.sleep(180)
            pagreq = urllib2.Request(rec['artlink'], headers=hdr)
            page = BeautifulSoup(urllib2.urlopen(pagreq), features="lxml")
        for meta in page.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #pages
                if meta['name'] == 'citation_firstpage':
                    rec['p1'] = meta['content']
                elif meta['name'] == 'citation_lastpage':
                    rec['p2'] = meta['content']
                #DOI
                elif meta['name'] == 'citation_doi':
                    rec['doi'] = meta['content']
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                #authors
                elif 'citation_author' == meta['name']:
                    rec['autaff'].append([meta['content']])
                elif 'citation_author_institution' == meta['name']:
                    rec['autaff'][-1].append(meta['content'])
                elif meta['name'] == 'citation_author_orcid':
                    orcid = re.sub('.*/', 'ORCID:', meta['content'])
                    rec['autaff'][-1].append(orcid)
                #abstract
                elif 'citation_abstract':
                    if not meta.has_attr('scheme'):
                        rec['abs'] = meta['content']
        #strange page
        if not 'p1' in rec.keys():
            rec['p1'] = re.sub('.*\.', '', rec['doi'])
        #references
        for div in page.find_all('div', attrs = {'class' : 'ref-list'}):
            rec['refs'] = []
            for li in div.find_all('li'):
                for a in li.find_all('a', attrs = {'class' : 'rev-xref-ref'}):
                    a.decompose()
                    for a in li.find_all('a'):
                        a.decompose()
                    rec['refs'].append([('x', li.text.strip())])
    return recs


done = getdone()
available = getissuenumbers(year)
todo = []
for tupel in available:
    if not tupel in done:
        todo.append(tupel)
i = 0
for (vol, issue) in todo:
    i += 1
    print '==={ %i/%i }==={ Volume %s, Issue %s }===' % (i, len(todo), vol, issue)
    recs = harvestissue(vol, issue)
    jnlfilename = 'science%s.%s' % (vol, issue)
    #write recs
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writeXML(recs, xmlfile, publisher)
    xmlfile.close()
    #retrival
    retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
