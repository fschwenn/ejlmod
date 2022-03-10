# -*- coding: utf-8 -*-
#harvest theses from Buenos Aires, CONICET
#FS: 2022-02-14

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

rpp = 50

now = datetime.datetime.now()
startyear = now.year-1
stopyear = now.year
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Buenos Aires, CONICET'
jnlfilename = 'THESES-BuenosAiresCONICET-%s-%i_%i' % (stampoftoday, startyear, stopyear)

hdr = {'User-Agent' : 'Magic Browser'}
#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

recs = []
artlinks = []
for (dep, fc) in [('16', 'a'), ('2', 'm'), ('1', ''), ('9', '')]:
    print '======[ %s ]======' % (dep)
    urltrunc = 'https://ri.conicet.gov.ar/discover?filtertype_0=type&filtertype_1=dateIssued&filter_relational_operator_1=equals&filter_relational_operator_0=contains&filter_1=%5B' + str(startyear) + '+TO+' + str(stopyear) + '%5D&filter_0=thesis&filtertype=subjectClassification&filter_relational_operator=authority&filter=' + dep + '&rpp=' + str(rpp) + '&page='
    tocurl = urltrunc + '1'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpages = [ BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml") ]
    for h2 in tocpages[0].find_all('h2', attrs = {'class' : 'ds-div-head'}):
        for span in h2.find_all('span'):
            span.decompose()
        try:
            numoftheses = int(re.sub('.*\D(\d+).*', r'\1', h2.text.strip()))
        except:
            numoftheses = 0
        if numoftheses > 0:
            print '   %4i theses to harvest' % (numoftheses)
    for page in range((numoftheses-1) / rpp):
        time.sleep(3)
        tocurl = urltrunc + str(page+2)
        print tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpages.append(BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml"))
    for tocpage in tocpages:
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
            for a in div.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'note' : [], 'supervisor' : []}
                rec['artlink'] = 'https://ri.conicet.gov.ar' + a['href'] + '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                if fc:
                    rec['fc'] = fc
                if not rec['artlink'] in artlinks:
                    recs.append(rec)
                    artlinks.append(rec['artlink'])
        print '   %4i' %  (len(recs))

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(4)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #supervisor
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([ meta['content'] ])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'spa':
                    rec['language'] = 'spanish'
            #rights
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
    if not 'doi' in rec.keys():
        rec['link'] = rec['artlink']
    print '   ', rec.keys()

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
