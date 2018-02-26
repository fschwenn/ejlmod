# -*- coding: UTF-8 -*-
#program to crawl Springer
# FS 2017-02-22


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


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'Springer'
toclink = sys.argv[1]
jnl = sys.argv[2]
vol = sys.argv[3]
issue = sys.argv[4]

jnlfilename = re.sub(' ', '_', "%s%s.%s" % (jnl,vol,issue))
if len(sys.argv) > 4:
    cnum = sys.argv[5]
    jnlfilename += '_' + cnum


print "%s %s, Issue %s" %(jnl,vol,issue)
print "get table of content... from %s" % (toclink)




def get_records(url):
    recs = []
    print('get_records:'+url)
    try:
        page = urllib2.urlopen(url)
        pages = {url : BeautifulSoup(page)}
    except:
        print('failed to open %s' % (url))
        sys.exit(0)
    #content spread over several pages?
    numpag = pages[url].body.findAll('span', attrs={'class': 'number-of-pages'})
    print(numpag)
    if len(numpag) > 0:
        if re.search('^\d+$', numpag[0].string):
            for i in range(int(numpag[0].string)):
                try:
                    tocurl = '%s/page/%i' % (url, i+1)  
                    if not tocurl in pages.keys():
                        print(tocurl)
                        page = urllib2.urlopen(tocurl)
                        pages[tocurl] = BeautifulSoup(page)
                except:
                    tocurl = '%s?page=%i' % (url, i+1) 
                    if not tocurl in pages.keys():
                        print(tocurl)
                        page = urllib2.urlopen(tocurl)
                        pages[tocurl] = BeautifulSoup(page)
        else:
            print("number of pages %s not an integer" % (numpag[0].string))
    else:
        for input in pages[url].body.findAll('input', attrs={'class': 'c-pagination__input'}):
            if re.search('^\d+$', input['max']):
                maxpage = int(input['max'])
            print(maxpage)
            for i in range(maxpage):
                try:
                    tocurl = '%s/page/%i' % (url, i+1) 
                    if not tocurl in pages.keys():
                        print(tocurl)
                        page = urllib2.urlopen(tocurl)
                        pages[tocurl] = BeautifulSoup(page)
                except:
                    tocurl = '%s?page=%i' % (url, i+1)
                    if not tocurl in pages.keys():
                        print(tocurl)
                        page = urllib2.urlopen(tocurl)
                        pages[tocurl] = BeautifulSoup(page)
    links = []
    for tocurl in pages.keys():
        page = pages[tocurl]
        newlinks = []
        newlinks += page.body.findAll('p', attrs={'class': 'title'})
        newlinks += page.body.findAll('h3', attrs={'class': 'title'})
        links += newlinks
        print('%i potential links in %s' % (len(newlinks), tocurl))
    if not links:
        for tocurl in pages.keys():
            if tocurl == url: continue
            page = pages[tocurl]
            newlinks = page.body.findAll('div', attrs={'class': 'content-type-list__title'})        
            links += newlinks
            print('%i potential links in %s' % (len(newlinks), tocurl))
    artlinks = []
    for link in links:
        rec = {'jnl' : jnl, 'vol' : vol, 'autaff' : []}
        if issue != '0':
            rec['issue'] = issue
        if len(sys.argv) > 4:
            rec['cnum'] = cnum
            rec['tc'] = 'C'
        else:
            rec['tc'] = 'P'
        rec['tit'] = link.text.strip()
        for a in link.find_all('a'):
            rec['artlink'] = 'https://link.springer.com' + a['href']
        if not rec['artlink'] in artlinks:
            recs.append(rec)
            artlinks.append(rec['artlink'])
    return recs





recs = get_records(toclink)
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    artpage = BeautifulSoup(urllib2.urlopen(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            elif meta['name'] == 'citation_author_email':
                rec['autaff'][-1].append('EMAIL:' + meta['content'])
            elif meta['name'] == 'description':
                rec['abs'] = meta['content']
            elif meta['name'] == 'citation_cover_date':
                rec['date'] = meta['content']
    #Abstract
    for section in artpage.body.find_all('section', attrs = {'class' : 'Abstract'}):
        rec['abs'] = ''
        for p in section.find_all('p'):
            rec['abs'] += p.text.strip() + ' '
    #Keywords
    for div in artpage.body.find_all('div', attrs = {'class' : 'KeywordGroup'}):
        rec['keyw'] = []
        for span in div.find_all('span', attrs = {'class' : 'Keyword'}):
            rec['keyw'].append(span.text.strip())
    #References
    for ol in artpage.body.find_all('ol', attrs = {'class' : 'BibliographyWrapper'}):
        rec['refs'] = []
        for li in ol.find_all('li'):
            for a in li.find_all('a'):
                if a.text.strip() in ['Google Scholar', 'MathSciNet']:
                    a.replace_with(' ')
                elif a.text.strip() == 'CrossRef':
                    rdoi = re.sub('.*doi.org\/', '', a['href'])
                    a.replace_with(', DOI: %s' % (rdoi))
            rec['refs'].append([('x', li.text.strip())])


  
#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
