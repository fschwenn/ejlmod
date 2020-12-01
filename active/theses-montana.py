# -*- coding: utf-8 -*-
#harvest theses from Montana State U.
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Montana State U.'

rpp = 100
pages = 2

hdr = {'User-Agent' : 'Firefox'}
jnlfilename = 'THESES-MONTANASTATEU-%s' % (stampoftoday)

boringdeps = ['Montana State University - Bozeman, College of Agriculture',
              'Montana State University - Bozeman, College of Arts & Architecture',
              'Montana State University - Bozeman, College of Education, Health & Human Development',
              'Montana State University - Bozeman, College of Engineering',
              'Montana State University - Bozeman, Norm Asbjornson College of Engineering',
              'Montana State University - Bozeman, College of Nursing']
boringdegrees = ['MS', 'MFA', 'MA']

prerecs = []
for page in range(pages):
    tocurl = 'https://scholarworks.montana.edu/xmlui/handle/1/733/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    tocfilename = '/tmp/montanastateu.%s.%04i.html' % (stampoftoday, page)
    if not os.path.isfile(tocfilename):
        os.system('wget -q -O  %s "%s"' % (tocfilename, tocurl))
        time.sleep(5)
    inf = open(tocfilename, 'r')
    tocpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for span in div.find_all('span', attrs = {'class' : 'Z3988'}):
            degree = re.sub('.*rft.degree=(.*?)\&.*', r'\1', span['title'])
            if not degree in boringdegrees:
                for span in div.find_all('span', attrs = {'class' : 'publisher'}):
                    dep = span.text.strip()
                    if not dep in boringdeps:
                        rec['note'] = [ dep ]
                        for a in div.find_all('a'):
                            for h4 in a.find_all('h4'):
                                rec['link'] = 'https://scholarworks.montana.edu' + a['href']# + '?show=full'
                                rec['doi'] = '20.2000/MontanaStateU/' + re.sub('\D', '', a['href'])
                                prerecs.append(rec)
    print '   %i recs so far' % (len(prerecs))

recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    artfilename = '/tmp/montanastateu.%s.thesis' % (re.sub('\D', '', rec['link']))
    if not os.path.isfile(artfilename):
        os.system('wget -q -O %s "%s"' % (artfilename, rec['link']))
        time.sleep(5)
    inf = open(artfilename, 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
                rec['autaff'][-1].append(publisher)
            #pages
            elif meta['name'] == 'citation_lastpage':
                rec['pages'] = meta['content']
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #abstract
            elif meta['name'] == 'citation_dissertation_name':
                rec['degree'] = meta['content']
    if 'degree' in rec.keys():
        if rec['degree'] in boringdegrees:
            print '  skip "%s"' % (rec['degree'])
        else:
            rec['note'].append(rec['degree'])
            print ' ', rec.keys()
            recs.append(rec)
    else:
        print ' ', rec.keys()
        recs.append(rec)


#closing of files and printing
xmlf    = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
        
