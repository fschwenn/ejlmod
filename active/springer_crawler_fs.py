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

urltrunc = 'https://link.springer.com'

jnlfilename = re.sub(' ', '_', "%s%s.%s" % (jnl,vol,issue))
if len(sys.argv) > 5:
    cnum = sys.argv[5]
    jnlfilename += '_' + cnum


print "%s %s, Issue %s" %(jnl,vol,issue)
print "get table of content... from %s" % (toclink)




def get_records(url):
    recs = []
    print('get_records:'+url)
    try:
        page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(url)
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
                        page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)
                        pages[tocurl] = BeautifulSoup(page)
                except:
                    tocurl = '%s?page=%i' % (url, i+1) 
                    if not tocurl in pages.keys():
                        print(tocurl)
                        page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)
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
                        page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)
                        pages[tocurl] = BeautifulSoup(page)
                except:
                    tocurl = '%s?page=%i' % (url, i+1)
                    if not tocurl in pages.keys():
                        print(tocurl)
                        page = urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)
                        pages[tocurl] = BeautifulSoup(page)
    links = []
    for tocurl in pages.keys():
        page = pages[tocurl]
        newlinks = []
        newlinks += page.body.findAll('p', attrs={'class': 'title'})
        newlinks += page.body.findAll('h3', attrs={'class': ['title', 'c-card__title']})
        links += newlinks
        print('a) %i potential links in %s' % (len(newlinks), tocurl))
    if not links:
        for tocurl in pages.keys():
            if tocurl == url and len(pages) > 1: continue
            page = pages[tocurl]
            newlinks = page.body.findAll('div', attrs={'class': 'content-type-list__title'})        
            links += newlinks
            print('b) %i potential links in %s' % (len(newlinks), tocurl))
    if not links:
        for tocurl in pages.keys():
            page = pages[tocurl]
            newlinks = page.body.findAll('p', attrs={'class': 'item__title'})
            links += newlinks
            print('a) %i potential links in %s' % (len(newlinks), tocurl))
            #urltrunc = 'https://materials.springer.com'
    artlinks = []
    #print links
    for link in links:
        rec = {'jnl' : jnl, 'vol' : vol, 'autaff' : []}
        if issue != '0':
            rec['issue'] = issue
        if len(sys.argv) > 5:
            rec['cnum'] = cnum
            rec['tc'] = 'C'
        else:
            rec['tc'] = 'P'
        rec['tit'] = link.text.strip()
        for a in link.find_all('a'):
            if re.search('https?:', a['href']):
                rec['artlink'] = a['href']
            else:
                rec['artlink'] = urltrunc + a['href']
            if not rec['artlink'] in artlinks:
                recs.append(rec)
                artlinks.append(rec['artlink'])
    return recs





recs = get_records(toclink)
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
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
            elif meta['name'] in ['description', 'dc.description']:
                if not 'abs' in rec.keys() or len(meta['content']) > len(rec['abs']):
                    rec['abs'] = meta['content']
            elif meta['name'] == 'citation_cover_date':
                rec['date'] = meta['content']
    if not 'date' in rec.keys():
        for  meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_publication_date'}):
            rec['date'] = meta['content']
    if not 'date' in rec.keys():
        for span in artpage.body.find_all('span', attrs = {'class' : 'bibliographic-information__value', 'id' : 'copyright-info'}):
            if re.search('[12]\d\d\d', span.text):
                rec['date'] = re.sub('.*?([12]\d\d\d).*', r'\1', span.text.strip())
    #Abstract
    for section in artpage.body.find_all('section', attrs = {'class' : 'Abstract'}):
        abstract = ''
        for p in section.find_all('p'):
            abstract += p.text.strip() + ' '
        if not 'abs' in rec.keys() or len(abstract) > len(rec['abs']):
            rec['abs'] = abstract
    #Keywords
    for div in artpage.body.find_all('div', attrs = {'class' : 'KeywordGroup'}):
        rec['keyw'] = []
        for span in div.find_all('span', attrs = {'class' : 'Keyword'}):
            rec['keyw'].append(span.text.strip())
    #References
    for ol in artpage.body.find_all('ol', attrs = {'class' : ['BibliographyWrapper', 'c-article-references']}):
        rec['refs'] = []
        for li in ol.find_all('li'):
            for a in li.find_all('a'):
                if a.text.strip() in ['Google Scholar', 'MathSciNet']:
                    a.replace_with(' ')
                elif a.text.strip() == 'CrossRef':
                    rdoi = re.sub('.*doi.org\/', '', a['href'])
                    a.replace_with(', DOI: %s' % (rdoi))
            rec['refs'].append([('x', li.text.strip())])
    #SPECIAL CASE LANDOLT-BOERNSTEIN
    if not rec['autaff']:
        del rec['autaff']
        #date
        #rec['tc'] = 'S'
        if not 'date' in rec.keys():
            rec['date'] = re.sub('.* (\d\d\d\d) *$', r'\1', rec['abs'])
        for dl in artpage.body.find_all('dl', attrs = {'class' : 'definition-list__content'}):
            chapterDOI = False
            #ChapterDOI
            for child in dl.children:
                try:
                    child.name
                except:
                    continue
                if re.search('Chapter DOI', child.text):
                    chapterDOI = True
                elif chapterDOI:
                    rec['doi'] = child.text.strip()
                    chapterDOI = False
            #Authors and Email
            for dd in dl.find_all('dd', attrs = {'id' : 'authors'}):
                rec['auts'] = []
                for li in dd.find_all('li'):
                    email = False
                    for sup in li.find_all('sup'):
                        aff = re.sub('.*\((.*)\).*', r'\1', sup.text.strip())
                        sup.replace_with(',,=Aff%s' % (aff))
                    for a in li.find_all('a'):
                        for img in a.find_all('img'):
                            if re.search('@', img['title']):
                                email = img['title']
                                a.replace_with('') 
                    autaff = re.split(' *,, *', re.sub('[\n\t]', '', li.text.strip()))
                    author = autaff[0]
                    if email:
                         rec['auts'].append(re.sub(' *(.*) (.*)', r'\2, \1', author) + ', EMAIL:%s' % (email))
                    else:
                         rec['auts'].append(re.sub(' *(.*) (.*)', r'\2, \1', author))
                    if len(autaff) > 1:
                        rec['auts'] += autaff[1:]
            #Affiliations
            for dd in dl.find_all('dd', attrs = {'class' : 'definition-description author-affiliation'}):
                rec['aff'] = []
                for li in dd.find_all('li'):
                    aff = re.sub('[\n\t]', ' ', li.text.strip())
                    aff = re.sub('  +', ' ', aff).strip()
                    rec['aff'].append(re.sub('^(\d.*?) (.*)', r'Aff\1= \2', aff))
        #Abstract
        if not 'abs' in rec.keys():
            for div in artpage.body.find_all('div', attrs = {'class' : 'section__content'}):
                for p in div.find_all('p'):
                    rec['abs'] = p.text.strip()
        print '   ', rec.keys()
                
                        
                    
                    

  
#write xml
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
