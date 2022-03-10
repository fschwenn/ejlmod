# -*- coding: UTF-8 -*-
#program to harvest journals from the AGU journals
# FS 2019-03-26

import ejlmod2
import re
import sys
import unicodedata
import codecs
import urllib2
import urlparse
import time
import os
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'AGU'
tc = 'P'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]

if   (jnl == 'jgrsp'):
    jnlname = 'J.Geophys.Res.Space Phys.'
    toclink = 'https://agupubs.onlinelibrary.wiley.com/toc/21699402/%i/%s/%s' % (int(vol)+1895, vol, issue)
elif (jnl == 'jgrp'):
    jnlname = 'J.Geophys.Res.Planets'
    toclink = 'https://agupubs.onlinelibrary.wiley.com/toc/21699100/%i/%s/%s' % (int(vol)+1895, vol, issue)
elif (jnl == 'jgra'):
    jnlname = 'J.Geophys.Res.Atmos.'
    toclink = 'https://agupubs.onlinelibrary.wiley.com/toc/21698996/%i/%s/%s' % (int(vol)+1895, vol, issue)
elif (jnl == 'jgrse'):
    jnlname = 'J.Geophys.Res.Solid Earth'
    toclink = 'https://agupubs.onlinelibrary.wiley.com/toc/21699356/%i/%s/%s' % (int(vol)+1895, vol, issue)
elif (jnl == 'jgro'):
    jnlname = 'J.Geophys.Res.Oceans'
    toclink = 'https://agupubs.onlinelibrary.wiley.com/toc/21699291/%i/%s/%s' % (int(vol)+1895, vol, issue)

if len(sys.argv) > 4:
    cnum = sys.argv[4]
    tc = 'C'
    jnlfilename = '%s%s.%s_%s' % (jnl, vol, issue, cnum)
else:
    jnlfilename = '%s%s.%s' % (jnl, vol, issue)

print toclink
#tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
tocfilename = '/tmp/%s.toc' % (jnlfilename)
if not os.path.isfile(tocfilename):
    os.system('wget -T 300 -t 3 -q -O %s "%s"' % (tocfilename, toclink))
inf = open(tocfilename, 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()))
inf.close()

(note1, note2) = (False, False)
prerecs = []
for div in tocpage.body.find_all('div', attrs = {'class' : ['card', 'issue-items-container']}):
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'h3':
            note1 = child.text.strip()
            print '=====[ %s ]=====' % (note1)
        elif child.name == 'div':
            for child2 in child.children:
                try:
                    child2.name
                except:
                    continue
                if child2.name == 'h4':
                    note2 = child2.text.strip()
                    print '-----[ %s ]-----' % (note2)
                elif child2.name == 'div':
                    at = child2.find_all('a', attrs = {'class' : 'issue-item__title'})
                    if not at:
                        at = child2.find_all('a', attrs = {'class' : ['issue-item__title', 'visitable']})
                    for a in at:
                        rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'year' : '%i' % (int(vol)+1895),
                               'tc' : tc, 'note' : [], 'autaff' : [], 'keyw' : []}
                        if len(sys.argv) > 4:
                            rec['cnum'] = cnum
                        if re.search('\/10\.', a['href']):
                            rec['doi'] = re.sub('.*\/(10\..*)', r'\1', a['href'])
                            rec['artlink'] = 'https://agupubs.onlinelibrary.wiley.com' + a['href']
                            if note1:
                                rec['note'].append(note1)
                            if note2:
                                rec['note'].append(note2)
                            print '    a)', rec['doi']
                            prerecs.append(rec)
                elif child2.name == 'a':
                    if child2.has_attr('class') and ('issue-item__title' in child2['class'] or 'issue-item__title visitable' in child2['class']):
                        rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'year' : '%i' % (int(vol)+1895),
                               'tc' : tc, 'note' : [], 'autaff' : [], 'keyw' : []}
                        if len(sys.argv) > 4:
                            rec['cnum'] = cnum
                        if re.search('\/10\.', child2['href']):
                            rec['doi'] = re.sub('.*\/(10\..*)', r'\1', child2['href'])
                            rec['artlink'] = 'https://agupubs.onlinelibrary.wiley.com' + child2['href']
                            if note1:
                                rec['note'].append(note1)
                            if note2:
                                rec['note'].append(note2)
                            print '    b)', rec['doi']
                            prerecs.append(rec)




i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(prerecs), rec['artlink'])
    #artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    artfilename = '/tmp/%s.%s' % (jnlfilename, re.sub('\W', '', rec['artlink'][8:]))
    print artfilename
    if not os.path.isfile(artfilename):
        time.sleep(10)
        os.system('wget -T 300 -t 3 -q -O %s "%s"' % (artfilename, rec['artlink']))
    if int(os.path.getsize(artfilename)) == 0:
        time.sleep(10)
        os.system('wget -T 300 -t 3 -q -O %s "%s"' % (artfilename, rec['artlink']))        
    inf = open(artfilename, 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    for meta in artpage.head.find_all('meta'):
        if meta.attrs.has_key('name'):
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #pubnote
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([ meta['content'] ])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                rec['autaff'][-1].append('ORCID:%s' % (orcid))
            elif meta['name'] == 'citation_author_email':
                email = meta['content']
                rec['autaff'][-1].append('EMAIL:%s' % (email))
    #articleID
    if not 'p1' in rec.keys():
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'article_references'}):
            if re.search('http', meta['content']):
                rec['p1'] = re.sub('.*, (.*?)\. http.*', r'\1', meta['content'])
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : ['article-section__content', 'en', 'main']}):
        rec['abs'] = div.text.strip()
    #references
    for section in artpage.body.find_all('section', attrs = {'id' : 'references-section'}):
        rec['refs'] = []
        refswithdoi = 0
        for li in section.find_all('li'):
            if not li.has_attr('data-bib-id'):
                continue
            refno = re.sub('.*\-', '', li['data-bib-id'])
            rdoi = False
            for a in li.find_all('a'):
                if a.text in ['CrossRef', 'Crossref']:
                    rdoi = re.sub('.*=', '', a['href'])
                    rdoi = re.sub('%28', '(', rdoi)
                    rdoi = re.sub('%29', ')', rdoi)
                    rdoi = re.sub('%2F', '/', rdoi)
                    rdoi = re.sub('%3A', ':', rdoi)
                    a.replace_with('')
                elif a.text in ['Wiley Online Library']:
                    rdoi = re.sub('.*\/doi\/', '', a['href'])
                    a.replace_with('')
                else:
                    a.replace_with('')
            if rdoi:
                lit = re.sub('\.? *$', ', DOI: %s' % (rdoi), li.text.strip())
                refswithdoi += 1
            else:
                lit = li.text.strip()
            ref = '[%s] %s' % (refno, lit)
            #print '         ', ref
            rec['refs'].append([('x', ref)])
        print '        %i references found (%i with DOI)' % (len(rec['refs']), refswithdoi)
    if not rec['autaff'] and rec['tit'] in ['Issue Information']:
        pass
    else:
        print '    ', rec.keys()
        recs.append(rec)









#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()


