# -*- coding: utf-8 -*-
#harvest theses from Zurich U.
#FS: 2020-11-27

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Zurich U.'

pages = 4
rpp = 20

jnlfilename = 'THESES-ZURICH-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://www.zora.uzh.ch/cgi/search/archive/advanced?exp=0%7C1%7C-date%2Fcreators_name%2Feditors_name%2Ftitle%7Carchive%7C-%7Csubjects%3Asubjects%3AANY%3AEQ%3A10172+10123+10192%7Ctype%3Atype%3AANY%3AEQ%3Adissertation+habilitation%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&_action_search=1&order=-date%2Fcreators_name%2Feditors_name%2Ftitle&screen=Search&cache=7376471&search_offset=' + str(page*rpp)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    for dt in tocpage.body.find_all('dt', attrs = {'class' : 'dreiklang_title'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'ddc' : []}
        for a in dt.find_all('a'):
            rec['artlink'] = a['href']
            prerecs.append(rec)

recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(10)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('10.5167', meta['content']):
                    rec['doi'] = re.sub('.*?(10.5167.*)', r'\1', meta['content'])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split(' *, +', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'ger':
                    rec['language'] = 'german'
                elif meta['content'] != 'eng':
                    rec['language'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['fulltextlink'] = meta['content']
            #pages
            elif meta['name'] == 'eprints.pages':
                rec['pages'] = meta['content']
            #DDC
            elif meta['name'] == 'eprints.dewey':
                rec['ddc'].append(re.sub('^ddc', '', meta['content']))
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
    if 'fulltextlink' in rec.keys():
        if 'licence' in rec.keys():
            rec['FFT'] = rec['fulltextlink']
        else:
            rec['hidden'] = rec['fulltextlink']
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/Zurich/' + re.sub('\D', '', rec['artlink'])
        rec['link'] = rec['artlink']
    keepit = True
    if 'ddc' in rec.keys():
        keepit = False
        for ddc in rec['ddc']:
            if re.search('^5[0123]', ddc):
                keepit = True
    if keepit:
        recs.append(rec)
        print rec.keys()
    else:
        print '  skip', rec['ddc']

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
