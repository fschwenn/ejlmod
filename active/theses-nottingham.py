# -*- coding: utf-8 -*-
#harvest theses from University of Nottingham
#FS: 2021-12-06


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Nottingham U.'

hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-NOTTINGHAM-%s' % (stampoftoday)
recs = []

pages = 4
for page in range(pages):
    tocurl = 'http://eprints.nottingham.ac.uk/cgi/search/archive/advanced_t?exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Ceth_subjects%3Aeth_subjects%3AANY%3AEQ%3AQA+QB+QC%7Cthesis_type%3Athesis_type%3AANY%3AEQ%3APhD%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow%7Ctype%3Atype%3AANY%3AEQ%3Aethesis&_action_search=1&order=-date%2Fcreators_name%2Ftitle&screen=Search&cache=15020075&search_offset=' + str(page*20)

    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'autaff' : [], 'supervisor' : [], 'note' : [], 'fc' : []}
        for a in tr.find_all('a'):
            if not re.search('(zip|pdf)$', a['href']):
                rec['link'] = a['href']
                rec['doi'] = '20.2000/Nottingham/'+re.sub('\D', '', a['href'])
                if not rec['doi'] in ['20.2000/Nottingham/289862']:
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
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['hidden'] = meta['content']
            #supervisor
            elif meta['name'] == 'eprints.supervisors_name':
                rec['supervisor'].append([meta['content']])
            #devision
            elif meta['name'] == 'eprints.eth_divisions':
                rec['note'].append([meta['content']])
                if meta['content'] == 'e_Sci_Maths':
                    rec['fc'].append('m')
                elif meta['content'] == 'e_Sci_Computer':
                    rec['fc'].append('c')
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
