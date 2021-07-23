# -*- coding: utf-8 -*-
#harvest theses from CalTech
#FS: 2020-12-08

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
pagestocheck = 3

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Caltech'
jnlfilename = 'THESES-CALTECH-%s' % (stampoftoday)

tocurltrunc = 'https://thesis.library.caltech.edu/cgi/search/archive/advanced?dataset=archive&screen=Search&documents_merge=ALL&documents=&title_merge=ALL&title=&creators_name_merge=ALL&creators_name=&creators_id_merge=ALL&creators_id=&creators_orcid_merge=ALL&creators_orcid=&abstract_merge=ALL&abstract=&date=&thesis_type=phd&keywords_merge=ALL&keywords=&option_major_merge=ANY&option_minor_merge=ANY&divisions=div_pma&divisions_merge=ANY&thesis_advisor_name_merge=ALL&thesis_advisor_name=&thesis_committee_name_merge=ALL&thesis_committee_name=&funders_agency_merge=ALL&funders_agency=&funders_grant_number_merge=ALL&funders_grant_number=&local_group_merge=ALL&local_group=&projects_merge=ALL&projects=&thesis_awards_merge=ALL&thesis_awards=&other_numbering_system_name_merge=ALL&other_numbering_system_name=&other_numbering_system_id_merge=ALL&other_numbering_system_id=&satisfyall=ALL&order=-date%2Fcreators_name%2Ftitle&_action_search=Search'
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
            if re.search('thesis.library.caltech.edu\/\d\d', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK'}
                rec['artlink'] = a['href']
                if not rec['artlink'] in ['https://thesis.library.caltech.edu/13784/']:
                    recs.append(rec)

#check individual thesis pages
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
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
            elif meta['name'] == 'eprints.thesis_advisor_name':
                rec['supervisor'] = [[ meta['content'] ]]
            elif meta['name'] == 'eprints.thesis_advisor_email':
                rec['supervisor'][-1].append('EMAIL:%s' % (meta['content']))
            elif meta['name'] == 'eprints.thesis_advisor_orcid':
                orcid = re.sub('.*(\d\d\d\d\-\d\d\d\d\-\d\d\d\d\-\d\d\d[\dX]).*', r'\1', meta['content'])
                rec['supervisor'][-1].append('ORCID:%s' % (orcid))
            #DOI
            elif meta['name'] == 'eprints.doi':
                rec['doi'] = meta['content']
            #fulltext
            elif meta['name'] == 'eprints.document_url':
                rec['fulltext'] = meta['content']
    rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href'):
            if re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
    if 'fulltext' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['fulltext']
        else:
            rec['hidden'] = rec['fulltext']
    print '    ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()


