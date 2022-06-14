# -*- coding: utf-8 -*-
#harvest theses from DIVA
#FS: 2019-09-15


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'publisher'

typecode = 'T'


categories = {'physik' : {'Id' : '11520', 'recs' : []},
              'mathe'  : {'Id' : '11501', 'recs' : []}}
startyear = str(now.year-1)
stopyear = str(now.year)

hdr = {'User-Agent' : 'Magic Browser'}
for cate in categories.keys():
    p = 1
    complete = False
    artlinks = []
    while not complete:
        tocurl = 'http://www.diva-portal.org/smash/resultList.jsf?p=' + str(p) + '&fs=false&language=en&searchType=RESEARCH&query=&af=%5B%5D&aq=%5B%5B%5D%5D&aq2=%5B%5B%7B%22dateIssued%22%3A%7B%22from%22%3A%22' + startyear + '%22%2C%22to%22%3A%22' + stopyear + '%22%7D%7D%2C%7B%22categoryId%22%3A%22' + categories[cate]['Id'] + '%22%7D%2C%7B%22publicationTypeCode%22%3A%5B%22comprehensiveDoctoralThesis%22%2C%22monographDoctoralThesis%22%2C%22comprehensiveLicentiateThesis%22%2C%22monographLicentiateThesis%22%5D%7D%5D%5D&aqe=%5B%5D&noOfRows=50&sortOrder=author_sort_asc&sortOrder2=title_sort_asc&onlyFullText=false&sf=all'


        
        print tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(3)

        for a in tocpage.body.find_all('a', attrs = {'class' : 'titleLink'}):
            if a.text == 'Browse':
                continue
            rec  = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'supervisor' : []}
            rec['artlink'] = 'http://www.diva-portal.org' + a['href']
            if not rec['artlink'] in artlinks:
                categories[cate]['recs'].append(rec)
                artlinks.append(rec['artlink'])

        
        for span in tocpage.body.find_all('span', attrs = {'class' : 'paginInformation'}):
            target = int(re.sub('.*of (\d+).*', r'\1', span.text.strip()))
        print '---{ %i of %i }---' % (len(categories[cate]['recs']), target)
        if len(categories[cate]['recs']) < target and p < target:
            p += 50
        else:
            complete = True
        
    jnlfilename = 'THESES-DIVA-%s_%s' % (cate, stampoftoday)
    i = 0
    for rec in categories[cate]['recs']:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (cate, i, len(categories[cate]['recs']), rec['artlink'])
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")    
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #abstract
                if meta['name'] == 'DC.Description':
                    rec['abs'] = meta['content']
                #title
                elif meta['name'] == 'DC.Title':
                    rec['tit'] = meta['content']
                #doi
                elif meta['name'] == 'DC.Identifier.doi':
                    rec['doi'] = meta['content']
                #urn
                elif meta['name'] == 'DC.Identifier':
                    if re.search('^urn', meta['content']):
                        rec['urn'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.Subject':
                    if meta['xml:lang'] == "en":
                        rec['keyw'].append(meta['content'])
                #language
                elif meta['name'] == 'DC.Language':
                    if meta['content'] == 'swe':
                        rec['language'] = 'swedish'
                #date
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['FFT'] = meta['content']
        if not 'doi' in rec.keys():
            for link in artpage.head.find_all('link', attrs = {'rel' : 'canonical'}):
                rec['link'] = link['href']
        for div in artpage.body.find_all('div', attrs = {'id' : 'innerEastCenter'}):
             section = ''
             for child in div.children:
                try:
                    name = child.name
                except:
                    continue
                #author
                if name == 'div' and not rec['autaff']:
                    for h3 in child.find_all('h3'):
                        rec['autaff'].append([ h3.text.strip() ])
                        h3.replace_with('')
                    for span in child.find_all('span', attrs = {'class' : 'singleRow'}):
                        spant = re.sub('[\n\t]', '', span.text.strip())
                        spant = re.sub('ORCID ..: *', 'ORCID:', spant)
                        span.replace_with('')
                        rec['autaff'][0].append(spant)
                    for span in child.find_all('span'):
                        spant = re.sub('[\n\t]', '', span.text.strip())
                        if spant:
                            rec['autaff'][0].append(spant)
#                if name == 'span':
#                    for grandchild in child.children:
                if 1 == 1:
                        try:
                            gname = child.name
                        except:
                            gname = ''
                        if gname == 'h5':
                            section = re.sub('[\n\t]', '', child.text.strip())
                        #abstract
                        elif section == 'Abstract [en]' and gname == 'span':
                            rec['abs'] = child.text.strip()
                            section = ''
                        #ISBN
                        elif section == 'Identifiers' and gname == 'span':
                            gtext = child.text.strip()
                            if re.search('ISBN:', gtext):
                                isbn = re.sub('.*(978.*?) .*', r'\1', re.sub('[\n\t]', '', gtext))
                                rec['isbn'] = re.sub('\-', '', isbn)
                                section = ''
                        elif gname == 'script':
                            section = ''
                                
        print rec
        time.sleep(10)




                
    #closing of files and printing
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writenewXML(categories[cate]['recs'],xmlfile,publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
