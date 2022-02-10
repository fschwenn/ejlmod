# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest scielo.org
# FS 2017-03-27

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'

jnl = sys.argv[1]
year = sys.argv[2]
issue = sys.argv[3]

jnlfilename = jnl+year+'.'+issue
typecode = 'P'

if   (jnl == 'rbef'):
    trunc = 'http://www.scielo.br'
    issn = '1806-1117'
    jnlname = 'Rev.Bras.Ens.Fis.'
    publisher = 'Sociedade Brasileira de Fisica'
    #despite its name it does not contain reviews
    #typecode = 'R'
elif (jnl == 'rmaa'):
    trunc = 'http://www.scielo.org.mx'
    issn = '0185-1101'
    jnlname = 'Rev.Mex.Astron.Astrofis.'
    publisher = 'National Autonomous University of Mexico'
else:
    print 'Dont know journal %s!' % (jnl)
    sys.exit(0)

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}

tocurl = '%s/scielo.php?script=sci_issuetoc&pid=%s%s%04i&lng=en&nrm=iso' % (trunc, issn, year, int(issue))
print "get table of content of %s%s.%s via %s ..." %(jnlname, year, issue, tocurl)
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")

recs = []
for tr in tocpage.body.find_all('tr'):
    rec = {'jnl' : jnlname, 'year' : year, 'issue' : issue, 'tc' : typecode,
           'autaff' : [], 'refs' : []}
    for a in tr.find_all('a'):
        if a.has_attr('href') and re.search('text.*ngl', a.text):
                rec['artlink'] = a['href']
    if 'artlink' in rec.keys():
        time.sleep(5)
        print rec['artlink']
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #title
                if meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #author
                elif meta['name'] == 'citation_author':
                    rec['autaff'].append([meta['content']])
                elif meta['name'] == 'citation_author_institution':
                    if not meta['content'] in rec['autaff'][-1]:
                        rec['autaff'][-1].append(meta['content'])
                #pubnote
                elif meta['name'] == 'citation_firstpage':
                    rec['p1'] = meta['content']
                elif meta['name'] == 'citation_lastpage':
                    rec['p2'] = meta['content']
                elif meta['name'] == 'citation_volume':
                    rec['vol'] = meta['content']
                elif meta['name'] == 'citation_issue':
                    rec['issue'] = meta['content']
                #DOI
                elif meta['name'] == 'citation_doi':
                    rec['doi'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['FFT'] = meta['content']
        #abstract
        for div in artpage.find_all('div', attrs = {'class' : 'trans-abstract'}):
            englabs = False
            for p in div.find_all('p'):
                if p.text.strip() == 'ABSTRACT':
                    p.decompose()
                    englabs = True
            if englabs:
                for p in div.find_all('p'):
                    for b in p.find_all('b'):
                        if re.search('Key Word', b.text):
                            b.decompose()
                            rec['keyw'] = re.split('; ', p.text.strip())
                rec['abs'] = div.text.strip()
        #references
        for p in artpage.find_all('p', attrs = {'class' : 'ref'}):
            rec['refs'].append([('x', re.sub('\[ *Links *\]', '', p.text.strip()))])
        #license
        for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
            rec['licence'] = {'url' : a['href']}
        print '  ', rec.keys()
        recs.append(rec)

xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
