# -*- coding: utf-8 -*-
#harvest theses from University of Cardiff 
#FS: 2021-12-07

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Cardiff U.'

hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-CARDIDFF-%s' % (stampoftoday)
recs = []

pages = 5
for page in range(pages):
    tocurl = 'https://orca.cardiff.ac.uk/cgi/search/archive/advanced?exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Csubjects%3Asubjects%3AANY%3AEQ%3AQ1+QA+QB+QC%7Ctype%3Atype%3AANY%3AEQ%3Athesis%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&_action_search=1&order=-date%2Fcreators_name%2Ftitle&screen=Search&cache=15457074&search_offset=' + str(page*20)

    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'autaff' : [], 'supervisor' : [], 'note' : [], 'fc' : []}
        for a in tr.find_all('a'):
            if re.search('ac.uk\/\d', a['href']):
                rec['link'] = a['href']
                rec['tit'] = a.text.strip()
                rec['doi'] = '20.2000/Cardiff/'+re.sub('\D', '', a['href'])
                recs.append(rec)
    time.sleep(5)
            
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
            #author
            elif meta['name'] == 'eprints.creators_name':
                rec['autaff'] = [[  meta['content'] ]]
            elif meta['name'] == 'eprints.creators_id':
                if re.search('@', meta['content']):
                    rec['autaff'][-1].append('EMAIL:' + meta['content'])
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = re.sub('[\n\t\r]', ' ', meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split('[,;] ', re.sub('[\n\t\r]', ', ', meta['content']))
            #supervisor
            elif meta['name'] == 'eprints.supervisors_name':
                rec['supervisor'].append([meta['content']])
            #pages
            elif meta['name'] == 'eprints.pages':
                rec['pages'] = re.sub('\D', '', meta['content'])
            #note
            elif meta['name'] == 'eprints.note':
                rec['note'].append(meta['content'])
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append(meta['content'])
                if re.search('QA', meta['content']):
                    rec['fc'] = 'm'
                if re.search('QB', meta['content']):
                    rec['fc'] = 'a'
            #level
            elif meta['name'] == 'eprints.qualification_levelt':
                if meta['content'] != 'doctoral':
                    rec['note'].append(meta['content'])
    #fulltext and license
    for td in artpage.body.find_all('td', attrs = {'valign' : 'top'}):
        if re.search('Supplemental Material', td.text):
            continue
        for a in td.find_all('a'):
            if a.has_attr('href'):
                if re.search('creativecommons.org', a['href']):
                    rec['license'] = {'url' : a['href']}
                elif re.search('pdf$', a['href']) and re.search('Download', a.text):
                    if 'license' in rec.keys():
                        rec['FFT'] = a['href']
                    else:
                        rec['hidden'] = a['href']
                    break
    print '   ', rec.keys()
            
    rec['autaff'][-1].append(publisher)
        
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
