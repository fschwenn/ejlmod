# -*- coding: utf-8 -*-
#harvest theses universities from Ohio
#FS: 2020-09-08

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
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'OhioLink'
jnlfilename = 'THESES-OHIO-%s' % (stampoftoday)
subjects = [(369, '17lhTpxPDBKmMz_It4eqKqNs9zNtX0qcAU_qbPefkoYRwHJKxDJ_rb35lruEesyxv-kroW8Z5tLjaspD9aU_lfA'),
            (1010, '1OMmFJtiSfwjRziKmFB4Cm4Jnu-jQrJzHJI66MDnvKKtb18VeZlBDSrIARHhwrjnnW_JDTRW0vMy3dm57iDLAYQ'),
            (343, '1mzhIi3yLXYvXb2vI0z4zIcCvZMlcG40OLGlU42xcQU7W-v5IyszGNydbLvPmJ00tGdAdQLIWhToKPPGsCQmHgw'),
            (913, '1pvnFdlF4FLWOUXOCYLdm8HUtoQs90sCCGzAKf9Nr4jUQfDyQ1ZsuCrZfrNxHBYpaMFB5NE0pXjRAQ0tb_REgzg'),
            (836, '1YoHx2N5yBKt5O2icId_Uc72DheKPEAQhqPxPDA5OJIvHqoUug3dBILbE4LML8hxSa00jCKly9FIU4KgESaMh5w'),
            (53, '1UmO8xMgdJ7ZKKjkMuFhHKU4iIhP-Gjk4kpUoXQegKhNAUmvB4YD3riY7vX0HI95XTgNT_C0Z9dnbya8tM8Ux8g'),
            (116, '1ip3vNhON-CMKmICh8I9nIbPyig8gUmlZSObE89LW7Fc9fmeXUMojYA-NDyUaaWFP1dzdzaFbuMtgerQ9BNza-A'),
            (482, '1EmR9IYHFy8fr4Tx94tRv_m3L36VSEBbCwUnp17VXVr7dAwTPDJEDvZ7Mbi77t3YFjMeaaz4I2kxvhCFecbgTBw')]


hdr = {'User-Agent' : 'Magic Browser'}
recs = []
links = []
for (subjnr, checksum)  in subjects:
    tocurl = 'https://etd.ohiolink.edu/pg_6?::NO:6:P6_ABSTRACT,P6_ACCESSION_NUM,P6_AUTHOR,P6_COMMITTEE_MEMBER,P6_DEGREE_NAME,P6_DEGREE_YEAR_FROM,P6_DEGREE_YEAR_TO,P6_ETD_INST_DEPTID,P6_INSTID,P6_KEYWORDS,P6_SUBJECTS,P6_TITLE,P6_ETD_LANGUAGEID,P6_PAGE,P6_ORCID:,,,,,2019,2040,,,,%i,,,1,&cs=%s' % (subjnr, checksum)
    tocurl = 'https://etd.ohiolink.edu/apexprod/rws_olink/r/1501/6?p6_abstract=&p6_accession_num=&p6_author=&p6_committee_member=&p6_degree_name=&p6_degree_year_from=2019&p6_degree_year_to=2040&p6_etd_inst_deptid=&p6_instid=&p6_keywords=&p6_subjects=%i&p6_title=&p6_etd_languageid=&p6_page=1&p6_orcid=&clear=6&cs=%s'  % (subjnr, checksum)
    print '==={ %s }===' % (tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    divs = tocpage.body.find_all('div', attrs = {'class' : 'searchResult'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        rec['link'] = 'https://etd.ohiolink.edu' + div.find_all('a')[0]['href']
        rec['doi'] = '20.2000/OHIO/' + re.sub('\W', '', div.find_all('a')[0]['href'])
        if rec['link'] in links:
            print '  %s already in "records"' % (rec['link'])
        else:
            recs.append(rec)
            links.append(rec['link'])
            
    print '  %i records so far' % (len(recs))
    time.sleep(10)


    
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(3)
    except:
        try:
            print "   retry %s in 15 seconds" % (rec['link'])
            time.sleep(15)
            req = urllib2.Request(rec['link'], headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        except:
            print "   no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            elif meta['name'] == 'citation_author_orcid':
                if meta['content']:
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
            elif meta['name'] == 'citation_author_institution':
                    rec['autaff'][-1].append(meta['content'] + ', USA')
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    #abstract
    for span in artpage.body.find_all('span', attrs = {'id' : 'P10_ABSTRACT'}):
        rec['abs'] = span.text
    #supervisor
    for span in artpage.body.find_all('span', attrs = {'id' : 'P10_ADVISORS'}):
        for br in span.find_all('br'):
            br.replace_with(' XXX ')
        for committeemember in re.split(' *XXX *', span.text.strip()):
            if re.search('\(Advisor', committeemember):
                rec['supervisor'].append([re.sub(' *\(.*', '', committeemember)])
    #keywords
    for span in artpage.body.find_all('span', attrs = {'id' : 'P10_KEYWORDS'}):
        for a in span.find_all('a'):
            rec['keyw'].append(a.text.strip())
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'pdf_url' in rec.keys():
                rec['FFT'] = rec['pdf_url']
    #upload PDF at least hidden
    if not 'FFT' in rec.keys() and 'pdf_url' in rec.keys():
        rec['hidden'] = rec['pdf_url']

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
