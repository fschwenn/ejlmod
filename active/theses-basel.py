# -*- coding: utf-8 -*-
#harvest theses from Basel U.
#FS: 2019-10-25


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
pagestocheck = 5

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Basel U. (main)'
jnlfilename = 'THESES-BASEL-%s' % (stampoftoday)

reasonstoskip = []
for reason in ['Master Thesis', 'Faculty of Humanities and Social Sciences',
               'Faculty of Medicine', 'Faculty of Psychology']:
    reasonstoskip.append((reason, re.compile(reason)))

tocurltrunc = 'https://edoc.unibas.ch/cgi/search/archive/advanced?screen=Search&cache=4845765&order=-date%2Fcreators_name%2Ftitle&_action_search=1&exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Cthesis_status%3Athesis_status%3AANY%3AEQ%3Acomplete%7Ctype%3Atype%3AANY%3AEQ%3Athesis%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow'
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
#check content pages
for i in range(pagestocheck):
    tocurl = '%s&search_offset=%i' % (tocurltrunc, 20*i)
    print '---{ %i/%i }---{ %s }---' % (i+1, pagestocheck, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        keep = True
        for a in tr.find_all('a'):
            if re.search('edoc.unibas.ch\/\d\d', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK'}
                rec['artlink'] = a['href']
        for reason in reasonstoskip:
            if reason[1].search(tr.text):
                print ' skip %s' % (reason[0])
                keep = False
                break
        if keep:
            recs.append(rec)

#check individual thesis pages
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    #first get author
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.creators_name'}):
        rec['autaff'] = [[ meta['content'] ]]
    #other metadata
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #email
            if meta['name'] == 'eprints.contact_email':
                rec['autaff'][-1].append('EMAIL:%s' % (meta['content']))
            #ORCID
            elif meta['name'] == 'eprints.creators_orcid':
                orcid = re.sub('.*(\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-\d\d\d\d).*', r'\1', meta['content']) 
                rec['autaff'][-1].append('ORCID:%s' % (orcid))
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'eprints.datestamp':
                rec['date'] = meta['content'][:10]
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split('[,;] ', meta['content'])
            #DOI, URN
            elif meta['name'] == 'DC.identifier':
                if re.search('10.5451\/unibas.\d\d\d', meta['content']):
                    rec['doi'] = re.sub('.*?(10.5451\/.*)', r'\1', meta['content'])
                elif re.search('urn:nbn', meta['content']):
                    rec['urn'] = re.sub('.*?(urn:nbn.*)', r'\1', meta['content'])
    rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href'):
            if re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.document_url'}):
                    rec['FFT'] = meta2['content']
    #upload PDF at least hidden
    if not 'FFT' in rec.keys():
        for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.document_url'}):
            rec['hidden'] = meta2['content']
    #pseudoDOI
    if not 'doi' in rec.keys():
        rec['link'] = rec['artlink']
        if not 'urn' in rec.keys():
            rec['doi'] = '20.2000/' + re.sub('\W', '', rec['artlink'])
    print '    ', rec.keys()
    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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


