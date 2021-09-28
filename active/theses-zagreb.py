# -*- coding: utf-8 -*-
#harvest theses from Zagreb U.
#FS: 2020-12-01

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

publisher = 'U. Zagreb (main)'

jnlfilename = 'THESES-ZAGREB-%sA' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
pages = 1

for (subject, aff) in [('Fizika', 'Zagreb U., Phys. Dept.'), ('Matematika',  'U. Zagreb (main)')]:
    for page in range(pages):
        tocurl = 'https://repozitorij.pmf.unizg.hr/en/islandora/search?page=' + str(page) + '&display=default&f%5B0%5D=RELS_EXT_hasModel_uri_s%3A%22info%3Afedora/ir%3AdisertationCModel%22&f%5B1%5D=facet_field_pth%3APRIRODNE%5C%20ZNANOSTI%23' + subject + '%2A&islandora_solr_search_navigation=0&sort=dabar_sort_date_s%20desc'
        print '==={ %s }==={ %i/%i }==={ %s }===' % (subject, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(5)
        for div in tocpage.body.find_all('div', attrs = {'class' : 'islandora-solr-search-result-inner'}):
            for dd in div.find_all('dd', attrs = {'class' : 'bibl_metadata'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'affiliation' : aff,
                       'supervisor' : [], 'note' : [subject]}
                for a in dd.find_all('a'):
                    rec['link'] = a['href']
                    rec['urn'] = a.text.strip()
                    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(10)
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
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], rec['affiliation'] ]]
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
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'hr':
                    rec['language'] = 'croatian'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
    for tr in artpage.find_all('tr'):
        tds = tr.find_all('td')
        if len(tds) == 2:
            tdt = tds[0].text.strip()
            #supervisor
            if tdt == 'Mentor':
                for a in tds[1].find_all('a'):
                    rec['supervisor'].append([a.text.strip()])
            #Abstract
            elif tdt == 'Abstract (english)' or re.search('Sa.*etak .engleski.', tdt):
                rec['abs'] = tds[1].text.strip()
            elif tdt == 'Abstract'  or re.search('Sa.*etak', tdt):
                if re.search(' the ', tds[1].text):
                    rec['abs'] = tds[1].text.strip()
                else:
                    rec['abshr'] = tds[1].text.strip()
            #coration abstract
            elif tdt == 'Abstract (croatian)':
                rec['abshr'] = tds[1].text.strip()
            #pages
            elif tdt in ['Extent', 'Opseg']:
                if re.search('\d\d', tds[1].text):
                    rec['pages'] = re.sub('\D*(\d\d+).*', r'\1', tds[1].text.strip())
            #OA
            elif tdt in ['Access conditions', 'Prava pristupa']:
                if re.search('[oO]pen [aA]ccess', tds[1].text) or re.search('Otvoreni pristup', tds[1].text):
                    if'citation_pdf_url' in rec.keys():
                        rec['hidden'] = rec['citation_pdf_url']
            #english title
            elif tdt in ['Title (english)', 'Naslov (engleski)']:
                if 'language' in rec.keys():
                    rec['transtit'] = tds[1].text.strip()
    if not 'abs' in rec.keys() and 'abshr' in rec.keys():
        rec['abs'] = rec['abshr']
    print rec.keys()

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
