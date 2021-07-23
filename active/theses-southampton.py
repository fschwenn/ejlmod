# -*- coding: utf-8 -*-
#harvest theses from University of Southampton
#FS: 2019-09-26


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

publisher = 'Southampton U.'

hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-SOUTHAMPTON-%s' % (stampoftoday)
recs = []
tocurl = 'https://eprints.soton.ac.uk/cgi/search/archive/advanced?order=-date%2Fcontributors_name%2Ftitle&_action_search=Reorder&screen=Search&dataset=archive&exp=0%7C1%7Ccontributors_name%2F-date%2Ftitle%7Carchive%7C-%7Cdivisions%3Adivisions%3AANY%3AEQ%3Aa2476d18-5515-484c-b0b5-7be7b4f0cd2f+a8c9dd07-9533-48da-a2e5-0a51a7be7743%7Ctype%3Atype%3AANY%3AEQ%3Athesis%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow'

print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'autaff' : [], 'supervisor' : []}
    for a in tr.find_all('a'):
        rec['link'] = a['href']
        recs.append(rec)
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['FFT'] = meta['content']
            #pages
            elif meta['name'] == 'eprints.pages':
                rec['pages'] = meta['content']
            #UUID
            elif meta['name'] == 'eprints.pure_uuid':
                rec['uuid'] = meta['content']
                rec['doi'] = '20.2000/southampton/' + meta['content']
    #license
    for div in artpage.body.find_all('div', attrs = {'class' : 'uos-eprints-fileblock-line'}):
        if re.search('under [lL]icense', div.text):
            for a in div.find_all('a'):
                rec['license'] = {'url' : a['href']}
    #contributors section
    for div in artpage.body.find_all('div', attrs = {'class' : 'uos-grid'}):
        for h2 in div.find_all('h2'):
            if h2.text.strip() == 'Contributors':
                #individual contributor
                for div2 in div.find_all('div', attrs = {'class' : 'uos-eprints-dv'}):
                    for span in div2.find_all('span', attrs = {'class' : 'uos-eprints-dv-label'}):
                        ctype = span.text.strip()
                    for span in div2.find_all('span', attrs = {'class' : 'person_name'}):
                        cname = [span.text.strip()]
                    for a in div2.find_all('a'):
                        if re.search('orcid.org', a['href']):
                            cname.append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                    cname.append('Southampton U.')
                    if ctype == 'Author:':
                        rec['autaff'].append(cname)
                    elif ctype == 'Thesis advisor:':
                        rec['supervisor'].append(cname)
            
                        
                        
    


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
