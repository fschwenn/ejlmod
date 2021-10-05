# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest De Gruyter journals
# FS 2016-01-04

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
import datetime


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'
urltrunc = 'https://www.degruyter.com'
publisher = 'De Gruyter'

journal = sys.argv[1]
year = sys.argv[2]
vol = sys.argv[3]
iss = sys.argv[4]



reemail = re.compile('(.*); ([^@]+@[^@]+\.[a-zA-Z]+) *$')

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'dg%s.%s.%s_%s' %  (journal, vol, iss, stampoftoday)
if journal == 'phys':
    if int(vol) <= 12:
        jnl = 'Central Eur.J.Phys.'
    else:        
        jnl = 'Open Phys.'
elif journal == 'ract':
    jnl = 'Radiochim.Acta'
elif journal == 'astro':
    jnl = 'Open Astron.'
elif journal == 'ijnsns':
    jnl = 'Int.J.Nonlin.Sci.Numer.Simul.'
elif journal == 'kern':
    jnl = 'Kerntech.'
elif journal == 'crll':
    jnl = 'J.Reine Angew.Math.'

#get list of volumes
if journal in ['kern', 'ract', 'phys', 'astro', 'crll']:
    tocurl = 'https://www.degruyter.com/journal/key/%s/%s/%s/html' % (journal.upper(), vol, iss)
else:
    tocurl = "%s/view/j/%s.%s.%s.issue-%s/issue-files/%s.%s.%s.issue-%s.xml" % (urltrunc, journal, year, vol, iss, journal, year, vol, iss)        
print tocurl

tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

#get volumes
recs = []
i = 0
#for h4 in tocpage.find_all('h4'):
for div in tocpage.find_all('div', attrs = {'class' : 'resultTitle'}):
    for a in div.find_all('a'):        
        if a.has_attr('href'):
            i += 1
            vollink = 'https://www.degruyter.com' + a['href']
            print i, vollink
            rec = {'tc' : 'P', 'jnl' : jnl, 'year' : year, 'vol' : vol, 'issue' : iss, 'autaff' : [],
                   'auts' : [], 'aff' : [], 'keyw' : [], 'pacs' : []}
            #title
            rec['tit'] = a.text.strip()
            if rec['tit'] in ['Frontmatter', 'Backmatter', 'Contents', 'Editorial']:
                continue
            #get details
            if not os.path.isfile('/tmp/dg%s.%i' % (jnlfilename, i)):
                time.sleep(5)
                os.system('wget -T 300 -t 3 -q -U "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0"  -O /tmp/dg%s.%i %s' % (jnlfilename, i, vollink))
            inf = open('/tmp/dg%s.%i' % (jnlfilename, i), 'r')
            artpage = BeautifulSoup(''.join(inf.readlines()))
            inf.close()
            for meta in  artpage.find_all('meta'):
                if meta.has_attr('name'):
                    #pages
                    if meta['name'] == 'citation_firstpage':
                        rec['p1'] = meta['content']
                    elif meta['name'] == 'citation_lastpage':
                        rec['p2'] = meta['content']
                    #DOI
                    elif meta['name'] == 'citation_doi':
                        rec['doi'] = meta['content']
                    #keywords
                    elif meta['name'] == 'citation_keywords':
                        if re.search('^\d\d\.\d\d...$', meta['content']):
                            rec['pacs'].append(meta['content'])
                        else:
                            rec['keyw'] += re.split('; ', meta['content'])
                if meta.has_attr('property'):
                    #abstract
                    if meta['property'] == 'og:description':
                        rec['abs'] = meta['content']
            #abstract
            divs  = artpage.find_all('div', attrs = {'class' : 'articleBody_abstract'})
            if not divs:
                divs = artpage.find_all('section', attrs = {'class' : 'abstract'})
            for div in divs:
                for p in div.find_all('p'):
                    rec['abs'] = p.text.strip()
            #affiliations
            for div in artpage.find_all('div', attrs = {'class' : 'NLM_affiliations'}):                
                for p in div.find_all('p'):
                    for sup in p.find_all('sup'):
                        cont = sup.text
                        sup.replace_with('Aff%s= ' % (cont))
                    rec['aff'].append(p.text.strip())
            if not rec['aff']:
                for ul in artpage.find_all('ul', attrs = {'class' : 'affiliation-list'}):
                    for li in ul.find_all('li'):
                        for sup in li.find_all('sup'):
                            cont = sup.text
                            sup.replace_with('Aff%s= ' % (cont))
                        rec['aff'].append(li.text.strip())
                    ul.decompose()
            #authors
            divs = artpage.find_all('div', attrs = {'class' : 'contributors'})
            if not divs:
                divs = artpage.find_all('div', attrs = {'class' : 'component-content-contributors'})
            for div in divs:
                for span in div.find_all('span'):
                    if span.text.strip() in [',', ', and']:
                        span.replace_with(' / ')
                    elif re.search('^,.*and$', span.text.strip()):
                        span.replace_with(' / ')
                for sup in div.find_all('sup'):
                    for a in sup.find_all('a'):
                        cont = a.text.strip()
                        a.replace_with(' / =Aff%s ' % (cont))
                for aut in re.split(' +\/ +', re.sub('[\n\t\r]+', ' ', div.text)):
                    if re.search('=Aff', aut):
                        rec['auts'].append(aut)
                    else:
                        rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', aut))
            if not divs:
                divs = artpage.find_all('div', attrs = {'class' : 'contributors-AUTHOR mb-2'})
                del rec['auts']
                del rec['aff']
                for div in divs:
                    for span in div.find_all('span'):
                        if span.has_attr('class'):
                            if 'contributor' in span['class']:
                                rec['autaff'].append([span.text])
                                if span.has_attr('title'):
                                    aff = span['title']
                                    if reemail.search(aff):
                                        email = reemail.sub(r'EMAIL:\2', aff)
                                        realaff = reemail.sub(r'\1', aff)
                                        rec['autaff'][-1].append(email)
                                        rec['autaff'][-1].append(realaff)
                                    else:
                                        rec['autaff'][-1].append(aff)
                            elif 'orcidLink' in span['class']:
                                for a in span.find_all('a'):
                                    rec['autaff'][-1].append(re.sub('.*\/', 'ORCID:', a['href']))
            #keywords / PACS
            for p in artpage.find_all('p', attrs = {'class' : 'articleBody_keywords'}):
                for span in p.find_all('span'):
                    if re.search('PACS', span.text):
                        key = 'pacs'                        
                    else:
                        key = 'keyw'
                    rec[key] = []
                for a in p.find_all('a'):
                    if a.text and not a.text in rec[key]:
                        rec[key].append(a.text)
            #keywords
            for div in artpage.find_all('div', attrs = {'class' : 'column'}):
                for dl in div.find_all('dl'):
                    for dt in dl.find_all('dt'):
                        if re.search('Keywords', dt.text):
                            for dd in dl.find_all('dd'):
                                for a in dd.find_all('a'):
                                    rec['keyw'].append(a.text.strip())
            #references
            referencesection = artpage.find_all('div', attrs = {'class' : 'moduleDetail refList'})
            if not referencesection:
                referencesection = artpage.find_all('ul', attrs = {'class' : 'simple'})
            if not referencesection:
                referencesection = artpage.find_all('ul', attrs = {'class' : 'List'})
            for div in referencesection:
                rec['refs'] = []
                for li in div.find_all('li'):
                    for a in li.find_all('a'):
                        if a.has_attr('href'):
                            if re.search('doi.org', a['href']):
                                doi = re.sub('.*doi.org.', '', a['href'])
                                a.replace_with(', DOI: %s  ' % (doi))
                            elif re.search('google.com', a['href']):
                                a.replace_with('')
                    rec['refs'].append([('x', li.text)])
            if not 'refs' in rec.keys():
                for span in artpage.find_all('span', attrs = {'class' : 'ref-list'}):
                    rec['refs'] = []
                    for p in span.find_all('p', attrs = {'class' : 'reference'}):
                        for a in p.find_all('a'):
                            if a.text.strip() == 'Search in Google Scholar':
                                a.decompose()
                        rec['refs'].append([('x', re.sub(';', ',', p.text))])                                
                    
            #date
            for div in artpage.find_all('div', attrs = {'class' : 'pubHistory'}):
                for dl in div.find_all('dl', attrs = {'id' : 'date-epub'}):
                    for dd in dl.find_all('dd', attrs = {'class' : 'fieldValue'}):
                        rec['date'] = dd.text
            for span in artpage.find_all('span', attrs = {'class' : 'publicationDate'}):
                rec['date'] = span.text
            #licence
            for div in artpage.find_all('div', attrs = {'class' : 'permissions'}):
                for a in div.find_all('a'):
                    rec['licence'] = {'url' : a['href']}
                    #fulltext pdf
                    for meta in artpage.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                        rec['FFT'] = meta['content']
            if not rec.has_key('licence'):
                for a in  artpage.find_all('a', attrs = {'class' : ['ccLink', 'creative-commons-license']}):
                    rec['licence'] = {'url' : a['href']}
                    #fulltext pdf
                    for meta in artpage.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                        rec['FFT'] = meta['content']
            #pages 
            if not rec.has_key('p1'):
                for div in artpage.find_all('div', attrs = {'class' : 'citationInfo'}):
                    pages = re.sub('.*Volume \d*(.*)DOI:.*', r'\1', div.text.strip())
                    if re.search('[pP]ages \d+\D\d+', pages):
                        rec['p1'] = re.sub('.*[pP]ages (\d+).*', r'\1', pages)
                        rec['p2'] = re.sub('.*[pP]ages \d+\D(\d+).*', r'\1', pages)
            #authors
            if not rec['autaff'] and not rec['aff']:
                print '   DEL AUTS'
                del rec['auts']
                for span in artpage.find_all('span', attrs = {'class' : 'contrib'}):
                    (affs, email) = ([], '')
                    for a in span.find_all('a', attrs = {'class' : 'contrib-corresp'}):
                        email = re.sub('mailto.(.*?)\?.*', r'\1', a['href'])
                    for li in span.find_all('li'):
                        if not re.search('(De Gruyter Online|Other articles by this author|Email)', li.text):
                            aff = re.sub('Corresponding author', '', li.text.strip())
                            if aff:
                                affs.append(aff)
                        li.replace_with('')
                    if email:
                        rec['autaff'].append([span.text.strip(), ' and '.join(affs), 'EMAIL:'+email])
                    else:
                        rec['autaff'].append([span.text.strip(), ' and '.join(affs)])
            recs.append(rec)
            print '  ', rec.keys()
   
            
#write xml
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

