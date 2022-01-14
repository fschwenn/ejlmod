# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest MS journals
# FS 2020-12-05

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

now = datetime.datetime.now()
lastyear = now.year - 1
llastyear = now.year - 2
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'MSP'
volumestodo = 3
journals = {'gt' : ('Geom.Topol.', 'https://msp.org/gt/2020/24-4/'),
            'pjm' : ('Pacific J.Math.', 'https://msp.org/pjm/2020/308-1/index.xhtml'),
            'agt' : ('Algebr.Geom.Topol.', 'https://msp.org/agt/2020/20-5/'),
            'gtm' : ('Geom.Topol.Monographs', 'https://msp.org/gtm/1998/01/'),
            'apde' : ('Anal.Part.Diff.Eq.', 'https://msp.org/apde/2020/13-7/'),
            'paa' : ('Pure Appl.Anal.', 'https://msp.org/paa/2020/2-3/')}

j = 0
for jnl in journals.keys():
    j += 1
    (jnlname, url) = journals[jnl]
    #all issues page
    print '===[ %s | %s | %s ]===' % (jnl, jnlname, url)
    todo = []
    page = BeautifulSoup(urllib2.urlopen(url))
    issuelinks = []
    for a in page.find_all('a', attrs = {'class' : 'about'}):
        if a.has_attr('href') and re.search('index\.xhtml', a['href']):
            link = 'https://msp.org' + a['href']
            issuelinks.append(link)
    #print ' issues:', issuelinks
    if jnl == 'gtm':
        tc = 'S'
        todo = issuelinks[-volumestodo:]
    else:
        tc = 'P'
        todo = issuelinks[:volumestodo]
    i = 0 
    for link in todo:
        recs = []
        i += 1
        print '==={ %s (%i/%i) }==={ %i/%i }==={ %s }==' % (jnl, j, len(journals.keys()), i, len(todo), link)
        if jnl == 'gtm':
            structure = re.search('.*\/([12]\d\d\d)\/(\d+).*', link)
            year = structure.group(1)
            vol = structure.group(2)
            iss = False
            jnlfilename = 'msp_%s%s' % (jnl, vol)
        else:
            structure = re.search('.*\/([12]\d\d\d)\/(\d+)\-(\d+).*', link)
            year = structure.group(1)
            vol = structure.group(2)
            iss = structure.group(3)
            jnlfilename = 'msp_%s%s.%s' % (jnl, vol, iss)
        #check whether file already exists
        goahead = True
        for ordner in ['/', '/zu_punkten/', '/zu_punkten/enriched/', 
                       '/backup/', '/backup/%i/' % (lastyear), 
                       '/backup/%i/' % (llastyear), '/onhold/']:
            if os.path.isfile(ejldir + ordner + jnlfilename + '.doki') or os.path.isfile(ejldir + ordner + 'LABS_'+jnlfilename + '.doki'):
                print '    Datei %s exisitiert bereit in %s' % (jnlfilename, ordner)
                goahead = False
        if not goahead:
            continue
        print ' file: ', jnlfilename
        time.sleep(2)
        tocpage = BeautifulSoup(urllib2.urlopen(link))
        for table in tocpage.body.find_all('table', attrs = {'id' : 'toc-area'}):
            for a in table.find_all('a', attrs = {'class' : 'title'}):
                rec = {'jnl' : jnlname, 'tc' : tc, 'vol' : vol, 'year' : year, 'autaff' : []}
                rec['artlink'] = re.sub('index.xhtml', a['href'], link)
                if iss:
                    rec['issue'] = iss
                recs.append(rec)
        k = 0
        for rec in recs:
            k += 1
            print '---{ %s (%i/%i) }---{ %i/%i }---{ %i/%i }---{ %s }---' % (jnl, j, len(journals.keys()), i, len(todo), k, len(recs), rec['artlink'])
            time.sleep(3)
            artpage = BeautifulSoup(urllib2.urlopen(rec['artlink']))
            for meta in artpage.find_all('meta'):
                if meta.has_attr('name'):
                    #title
                    if meta['name'] == 'citation_title':
                        rec['tit'] = meta['content']
                    #authors
                    elif  meta['name'] == 'citation_author':
                        rec['autaff'].append([meta['content']])
                    elif  meta['name'] == 'citation_author_institution':
                        rec['autaff'][-1].append(meta['content'])
                    #pages
                    elif  meta['name'] == 'citation_firstpage':
                        rec['p1'] = meta['content']
                    elif  meta['name'] == 'citation_lastpage':
                        rec['p2'] = meta['content']
                    #date
                    elif  meta['name'] == 'citation_publication_date':
                        rec['date'] = meta['content']
                    #fulltext
                    elif  meta['name'] == 'citation_pdf_url':
                        rec['hidden'] = meta['content']
                    #DOI
                    elif  meta['name'] == 'citation_doi':
                        rec['doi'] = meta['content']
            for table in artpage.find_all('table', attrs = {'class' : 'article'}):
                for h5 in table.find_all('h5'):
                    h5t = h5.text.strip() 
                    #abstract
                    if h5t == 'Abstract':
                        for p in table.find_all('p'):
                            rec['abs'] = p.text.strip()
                    #keywords
                    elif h5t == 'Keywords':
                        for div in table.find_all('div', attrs = {'class' : 'keywords'}):
                            rec['keyw'] = re.split(', ', div.text.strip())
                    #references
                    elif h5t == 'References':
                        for a in table.find_all('a'):
                            refurl = re.sub('index.xhtml', a['href'], link)
                            print '  references:', refurl
                            time.sleep(1)
                            refpage = BeautifulSoup(urllib2.urlopen(refurl))
                            for table2 in refpage.find_all('table', attrs = {'class' : 'article'}):
                                rec['refs'] = []
                                for tr in table2.find_all('tr'):
                                    rdoi = ''
                                    for a in tr.find_all('a'):
                                        if re.search('doi.org\/', a['href']):
                                            rdoi = re.sub('.*doi.org\/', ', DOI: ', a['href'])
                                    ref = tr.text.strip() + rdoi
                                    rec['refs'].append([('x', ref)])
                #arXiv
                for a in table.find_all('a'):
                    if a.has_attr('href') and re.search('arxiv.org', a['href']):
                        rec['arxiv'] = a.text.strip()
            print '  ', rec.keys()
        #Hauptaufnahme
        if jnl == 'gtm':
            rec = {'jnl' : jnlname, 'tc' : 'B', 'vol' : vol, 'year' : year, 'autaff' : []}
            #DOI
            for td in tocpage.find_all('td', attrs = {'class' : 'article-area'}):
                for a in td.find_all('a'):
                    if re.search('doi.org\/', a['href']):
                        rec['doi'] = re.sub('.*doi.org\/', ', DOI: ', a['href'])
            #Editors
            for h3 in tocpage.find_all('h3'):
                h3t = h3.text.strip()
                if re.search('^Editor', h3t):
                    h3t = re.sub('^.*?: *', '', h3t)
                    h3t = re.sub(' and ', ', ', h3t)
                    for editor in re.split(' *, *', h3t):
                        rec['autaff'].append([editor+ ' (Ed.)'])
            #Title
            for div in tocpage.find_all('div', attrs = {'class' : 'title'}):
                rec['tit'] = div.text.strip()
            recs.append(rec)

        #write xml
        if recs:
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

