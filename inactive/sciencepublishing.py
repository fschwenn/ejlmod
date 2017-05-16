# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest journals from Science Publishing Group
# FS 2015-01-26

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

publisher = 'Science Publishing Group'

journals = {'ijamp' : (322, 'Int.J.Appl.Math.Theor.Phys.'),
            'ajpa'  : (622, 'Am.J.Phys.Appl.'),
            'ajmp'  : (122, 'Am.J.Mod.Phys'),
            'ijhep' : (124, 'Int.J.High Energy Phys.')}
journals = {'ajmp'  : (122, 'Am.J.Mod.Phys')}
volumestodo = 1

for jnl in journals.keys():
    #all issues page
    print journals[jnl][1]
    url = 'http://www.sciencepublishinggroup.com/journal/archive?journalid=%i&issueid=-1' % (journals[jnl][0])
    page = BeautifulSoup(urllib2.urlopen(url))
    todo = []
    for div in page.body.find_all('div', attrs = {'class' : 'middle_left'}):
        for a in div.find_all('a'):
            if a.has_attr('href') and re.search('issueid=', a['href']):
                if re.search('http', a['href']):
                    link = a['href']
                else:
                    link = 'http://www.sciencepublishinggroup.com' + a['href']
                text = a.text.strip()
                if len(todo) < volumestodo:
                    todo.append(link)
                    print ' ', text
                else:
                    break
    #individual volumes
    for link in todo:
        jnlfilename = jnl + re.sub('.*=', '', link)
        #check whether file already exists
        goahead = True
        for ordner in ['/', '/zu_punkten/', '/zu_punkten/enriched/', '/backup/', '/onhold/']:
            if os.path.isfile(ejldir + ordner + jnlfilename + '.doki'):
                print '    Datei %s exisitiert bereit in %s' % (jnlfilename, ordner)
                goahead = False
        if not goahead:
            continue
        print '   ', jnlfilename
        tocpage = BeautifulSoup(urllib2.urlopen(link))
        #make list of article links
        articles = []
        for div in tocpage.body.find_all('div', attrs = {'class' : 'content1'}):
            for a in div.find_all('a'):
                if re.search('http', a['href']):
                    articles.append(a['href'])
                else:
                    articles.append('http://www.sciencepublishinggroup.com' + a['href'])
        #print articles
        recs = []
        for article in articles:
            rec = {'jnl' : journals[jnl][1], 'auts' : [], 'aff' : [], 'tc' : 'P', 'note' : [], 'refs' : []}
            articlepage = BeautifulSoup(urllib2.urlopen(article))
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_firstpage'}):
                rec['p1'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_lastpage'}):
                rec['p2'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_date'}):
                rec['date'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_volume'}):
                rec['vol'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_issue'}):
                rec['issue'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_doi'}):
                rec['doi'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'prism.section'}):
                rec['note'].append(meta['content'])
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'keywords'}):
                rec['keyw'] = re.split(', ',  meta['content'])
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'dc.description'}):
                rec['abs'] = meta['content']
            for meta in articlepage.head.find_all('meta', attrs = {'name' : 'title'}):
                rec['tit'] = meta['content']
            #'real' title
            for p in articlepage.body.find_all('p', attrs = {'class' : 'SciencePG-Paper-title'}):
                rec['tit'] = p.text
            #authors and affiliations
            for p in articlepage.body.find_all('p', attrs = {'class' : 'SciencePG-Author'}):
                for span in p.find_all('span'):
                    for sup in span.find_all('sup'):
                        affs = ''
                        for aff in re.split(', *', sup.string):
                            if re.search('[0-9a-zA-Z]', aff):
                                affs += ', =Aff%s' % aff
                        sup.replace_with(affs)
                    rec['auts'] += re.split(', *', span.text)
            for p in articlepage.body.find_all('p', attrs = {'class' : 'SciencePG-Affiliation'}):
                for sup in p.find_all('sup'):
                    for span in sup.find_all('span'):
                        span.replace_with('Aff%s= ' % (span.string))
                rec['aff'].append(p.text)
            #references
            for ol in articlepage.body.find_all('ol'):
                for li in ol.find_all('li'):
                    if li.has_attr('id') and re.search('reference', li['id']):
                        rec['refs'].append([('x', li.text)])
            print '        ', rec['doi']
            recs.append(rec)
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

