# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Cambridge-Books
# FS 2017-08-22


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
import time
import datetime
from bs4 import BeautifulSoup
import json


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'Cambridge University Press'
#urltrunc = 'http://www.cambridge.org/de/academic/subjects'
#serieses = ['physics/particle-physics-and-nuclear-physics',
#            'physics/history-philosophy-and-foundations-physics',
#            'physics/quantum-physics-quantum-information-and-quantum-computation',
#            'physics/theoretical-physics-and-mathematical-physics',
#            'physics/mathematical-methods',
#            'mathematics/mathematical-physics',
#            'physics/astrophysics',
#            'physics/cosmology-relativity-and-gravitation']


sections = [('physics', 'https://www.cambridge.org/core/what-we-publish/books/listing?sort=canonical.date%3Adesc&aggs%5BproductTypes%5D%5Bfilters%5D=BOOK&aggs%5BproductDate%5D%5Bfilters%5D=Last+12+months&aggs%5BproductSubject%5D%5Bfilters%5D=DBFB610E9FC5E012C011430C0573CC06&searchWithinIds=0C5182F27A492FDC81EDF8D3C53266B5'),
            ('math', 'https://www.cambridge.org/core/what-we-publish/books/listing?sort=canonical.date%3Adesc&aggs%5BproductTypes%5D%5Bfilters%5D=BOOK&aggs%5BproductDate%5D%5Bfilters%5D=Last+12+months&aggs%5BproductSubject%5D%5Bfilters%5D=FA1467C44B5BD46BB8AA6E58C2252153&searchWithinIds=0C5182F27A492FDC81EDF8D3C53266B5')]


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)



def formatreference(content):
    if re.search('citation_title', content):
        citationdict = {}
        for part in re.split('; citation_', content[9:]):
            subparts = re.split('=', part, 1)
            if subparts[0] in citationdict.keys():
                citationdict[subparts[0]].append(subparts[1])
            else:
                citationdict[subparts[0]] = [subparts[1]]
        if 'author' in citationdict.keys():
            ref = ', '.join(citationdict['author'])
        else:
            ref = ''
        if 'title' in citationdict.keys():
            ref += ': "%s"' % (citationdict['title'][0])
        if 'journal_title' in citationdict.keys():
            ref += ', ' + citationdict['journal_title'][0]
        elif 'inbook' in citationdict.keys():
            ref += ' in: ' + citationdict['inbook'][0]
        if 'volume' in citationdict.keys():
            ref += ' ' + citationdict['volume'][0]
        if 'firstpage' in citationdict.keys():
            ref += ', ' + citationdict['firstpage'][0]
        if 'lastpage' in citationdict.keys():
            ref += '-'  + citationdict['lastpage'][0]
        if 'publication_date' in citationdict.keys():
            ref += ' (%s)' % (citationdict['publication_date'][0])
        if 'doi' in citationdict.keys():
            ref += ', doi: ' + citationdict['doi'][0]
        return [('x', ref)]
    else:
        return [('x', content)]
        

recs = []
for section in sections:
    print '==={ %s }===' % (section[0])
    tocreq = urllib2.Request(section[1], headers={'User-Agent' : "Magic Browser"}) 
    toc = BeautifulSoup(urllib2.urlopen(tocreq))
    for li in toc.body.find_all('li', attrs = {'class' : 'title'}):
        for a in li.find_all('a', attrs = {'class' : 'part-link'}):
            rec = {'tit' : a.text.strip(), 'note' : [ section[0] ], 'autaff' : [],
                   'tc' : 'B', 'jnl' : 'BOOK'}
            rec['artlink'] = 'https://www.cambridge.org' + a['href']
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    artreq = urllib2.Request(rec['artlink'], headers={'User-Agent' : "Magic Browser"}) 
    artpage = BeautifulSoup(urllib2.urlopen(artreq))
    haseditor = False
    refs = []
    rec['doi'] = '20.2000/CambridgeBooks/' + re.sub('\W', '', rec['artlink'][10:])
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #DOI
            if meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #ISBNs
            elif meta['name'] == 'citation_isbn':
                if 'isbns' in rec.keys():
                    rec['isbns'].append([('a', meta['content'])])
                else:
                    rec['isbns'] = [ [('a', meta['content'])]  ]
            #references
            elif meta['name'] == 'citation_reference':
                if not meta['content'] in refs:
                    refs.append(meta['content'])
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            #editor
            elif meta['name'] == 'citation_editor':
                haseditor = True
                rec['autaff'].append([meta['content'] + ' (ed.)'])
            #affiliation
            elif meta['name'] in ['citation_author_institution', 'citation_editor_institution']:
                rec['autaff'][-1].append(meta['content'])
            #date
            elif meta['name'] == 'citation_online_date':
                rec['date'] = meta['content']
            #year
            elif meta['name'] == 'citation_publication_date':
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
    if haseditor:
        rec['note'].append('ggf. Einzelaufnahmen!')
    else:
        rec['refs'] = map(formatreference, refs)
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'spec'}):
        for li in ul.find_all('li'):
            for span in li.find_all('span', attrs = {'class' : 'medium-4'}):
                spant = span.text.strip()
            for span in li.find_all('span', attrs = {'class' : 'medium-8'}):
                #keywords
                if spant == 'Subjects:':
                    rec['keyw'] = []
                    for a in span.find_all('a'):
                        rec['keyw'].append(a.text.strip())
                #book series
                elif spant == 'Series:':
                    rec['bookseries'] = [('a', span.text.strip())]
    print rec.keys()
    time.sleep(10 + i % 5)

jnlfilename = 'CambridgeBooks__%s' % (stampoftoday)

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
