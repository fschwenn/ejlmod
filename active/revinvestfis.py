# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Rev.Invest.Fis.
# FS 2022-04-19


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import datetime
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" + '_special'
tmpdir = '/tmp'

def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

typecode = 'P'
publisher = 'San Marcos Natl. U.'

viewid =  sys.argv[1]
tocurl = 'https://revistasinvestigacion.unmsm.edu.pe/index.php/fisica/issue/view/' + viewid

print tocurl
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}
try:
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")

recs = []
for h3 in tocpage.body.find_all('h3', attrs = {'class' : 'title'}):
    rec = {'jnl' : 'Rev.Invest.Fis.', 'tc' : 'P', 'keyw' : [], 'autaff' : []}
    for a in h3.find_all('a'):
        rec['artlink'] = a['href']
    recs.append(rec)


i = 0
for rec in recs:
    i += 1
    autaff = False
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    time.sleep(3)
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #pages
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #authors and affiliations
            #elif meta['name'] == 'citation_author':
            #    rec['autaff'].append([ meta['content'] ])
            #elif meta['name'] == 'citation_author_institution':
            #    rec['autaff'][-1].append(meta['content'])
            #volume and issue
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content']
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.Description':
                if meta.has_attr('xml:lang'):
                    if meta['xml:lang'] in ['en', 'eng']:
                        rec['abs'] = meta['content']
                    else:
                        rec['abses'] = meta['content']
                else:
                    rec['abs'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            elif meta['name'] == 'DC.Title.Alternative':
                rec['transtit'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'es':
                    rec['language'] = 'Spanish'
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #license
            elif meta['name'] == 'DC.Rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
    if not 'abs' in rec.keys() and 'abses' in rec.keys():
        rec['abs'] = rec['abses']
    #authors
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'authors'}):
        for li in ul.find_all('li'):
            for span in li.find_all('span', attrs = {'class' : 'name'}):
                rec['autaff'].append([span.text.strip()])
            for span in li.find_all('span', attrs = {'class' : 'orcid'}):
                for a in span.find_all('a'):
                    rec['autaff'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
            for span in li.find_all('span', attrs = {'class' : 'affiliation'}):
                    rec['autaff'][-1].append(span.text.strip())
    print '  ', rec.keys()
            

jnlfilename = 'revinvestfis%s.%s_%s' % (rec['vol'], rec['issue'], viewid)
    
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
 
