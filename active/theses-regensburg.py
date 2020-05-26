# -*- coding: utf-8 -*-
#harvest theses from Regensburg U.
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
pagestocheck = 2

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Regensburg U.'
jnlfilename = 'THESES-REGENSBURG-%s' % (stampoftoday)

tocurltrunc = 'https://epub.uni-regensburg.de/cgi/search/archive/advanced?dataset=archive&screen=Search&documents_merge=ALL&documents=&title_merge=ALL&title=&creators_name_merge=ALL&creators_name=&creators_id_merge=ALL&creators_id=&creators_orcid=&editors_name_merge=ALL&editors_name=&editors_id_merge=ALL&editors_id=&editors_orcid=&date=&id_number_name_merge=ALL&id_number_name=&abstract_merge=ALL&abstract=&keywords_merge=ALL&keywords=&publication_merge=ALL&publication=&publisher_merge=ALL&publisher=&book_title_merge=ALL&book_title=&series_rgbg_merge=ALL&series_rgbg=&series_merge=ALL&series=&teaching_series_merge=ALL&teaching_series=&subjects_merge=ANY&institutions=fak09&institutions=fak10_01&institutions=fak10_02&institutions_merge=ANY&projects_merge=ALL&projects=&network_merge=ANY&research_group_merge=ANY&type=thesis_rgbg&type=thesis&department_merge=ALL&department=&referee_merge=ALL&referee=&isbn_merge=ALL&isbn=&classification_name_merge=ALL&classification_name=&own_doi_merge=ALL&own_doi=&ranking_merge=ANY&own_properties_merge=ALL&own_properties=&satisfyall=ALL&order=-date%2Fcreators_name%2Ftitle&_action_search=Search'
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
#check content pages
for i in range(pagestocheck):
    tocurl = '%s&search_offset=%i' % (tocurltrunc, 20*i)
    print '---{ %i/%i }---{ %s }---' % (i+1, pagestocheck, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        for a in tr.find_all('a'):
            if re.search('epub.uni-regensburg.de\/\d\d', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK'}
                rec['link'] = a['href']
                recs.append(rec)

#check individual thesis pages
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
    #first get author
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.creators_name'}):
        rec['autaff'] = [[ meta['content'] ]]
    #get abstract or translated abstract
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstract_lang'}):
        #abstract is English
        if meta['content'] == 'eng':
            for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstract'}):
                rec['abs'] = meta2['content']
        #abstract is not English
        else:
            #look for translated abstract
            for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstract_translated'}):
                rec['abs'] = meta2['content']
            #fall back to non-English abstract
            if not 'abs' in rec.keys():
                for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.abstract'}):
                    rec['abs'] = meta2['content']
    #other metadata
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #email
            if meta['name'] == 'eprints.contact_email':
                rec['autaff'][-1].append('EMAIL:%s' % (meta['content']))
            #ORCID
            elif meta['name'] == 'eprints.creators_orcid':
                orcid = re.sub('.*(\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-\d\d\d[\dX]).*', r'\1', meta['content']) 
                rec['autaff'][-1].append('ORCID:%s' % (orcid))
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'eprints.datestamp':
                rec['date'] = meta['content'][:10]
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split('[,;] ', meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #supervisor
            elif meta['name'] == 'eprints.referee_one_name':
                rec['supervisor'] = [[meta['content'], 'Regensburg U.']]
            #URN
            elif meta['name'] == 'eprints.own_urn':
                rec['urn'] = meta['content']
            #supervisor
            elif meta['name'] == 'eprints.referee':
                rec['supervisor'] = [[ meta['content'], 'Regensburg U.' ]]
            #language
            elif meta['name'] == 'eprints.title_lang':
                if meta['content'] == 'ger':
                    rec['language'] = 'german'
                    for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'eprints.title_translated'}):
                        rec['transtit'] = meta2['content']
    rec['autaff'][-1].append('Regensburg U.')
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
    print '    ', rec.keys()
    
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


