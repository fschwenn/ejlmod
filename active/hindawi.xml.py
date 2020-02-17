# -*- coding: UTF-8 -*-
#program to harvest journals from the Hindawi journals
# FS 2016-12-14


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
ejdir = '/afs/desy.de/user/l/library/dok/ejl'
def tfstrip(x): return x.strip()

publisher = 'HINDAWI'
jnl = sys.argv[1]
year = sys.argv[2]
month = sys.argv[3]

jnlfilename = jnl+year+'.'+month

if   (jnl == 'ahep'): 
    issn = '1687-7357'
    jnlname = 'Adv.High Energy Phys.'
elif (jnl == 'amp'):
    issn = ' 1687-9120'
    jnlname = 'Adv.Math.Phys.'
elif (jnl == 'aa'):
    issn = '1687-7969'
    jnlname = 'Adv.Astron.'
elif (jnl == 'physri'):
    issn = '2090-2220'
    jnlname = 'Phys.Res.Int.'
elif (jnl == 'isrnhep'):
    issn = ''
    jnlname = 'ISRN High Energy Phys.'
elif (jnl == 'isrnastro'):
    issn = ''
    jnlname = 'ISRN Astron.Astrophys.'
elif (jnl == 'isrnmp'):
    issn = ''
    jnlname = 'ISRN Math.Phys.'
elif (jnl == 'isrncmp'):
    issn = ''
    jnlname = 'ISRN Cond.Matt.Phys.'
elif (jnl == 'gravity'):
    issn = ''
    jnlname = 'J.Grav.'
elif (jnl == 'jgrav'):
    issn = ''
    jnlname = 'J.Grav.'
elif (jnl == 'aaa'):
    jnlname = 'Abstr.Appl.Anal.'
elif (jnl == 'jam'):
    jnlname = 'J.Appl.Math.'
elif (jnl == 'acmp'):
    jnlname = 'Adv.Cond.Mat.Phys.'

if re.search('isrn',jnl):
    if re.search('astro',jnl):
        urltrunk = "https://www.isrn.com/journals/%s/%s/" % (re.sub('isrn','',jnl),year)
    else:
        urltrunk = "https://www.hindawi.com/journals/isrn/%s/%s/" % (year,re.sub('isrn','',jnl))
        urltrunk = re.sub('\/mp','/mathematical.physics',urltrunk)
else:
    urltrunk = "https://www.hindawi.com/journals/%s/%s/" % (jnl,year)

directoriestocheck = '%s/backup/%s*doki %s/backup/%i/%s*doki %s/backup/%i/%s*doki ' % (ejdir,jnl, ejdir, int(year), jnl, ejdir, int(year)-1, jnl)
done =  map(tfstrip,os.popen("grep '^3.*DOI' %s |sed 's/.*\///'|sed 's/;//'" % (directoriestocheck)))
print "Already done:"
for dd in done:
    print dd
#done = []
 
print "get table of content of %s%s via %s ..." % (jnlname, year, urltrunk)

#tocpage = BeautifulSoup(urllib2.urlopen(urltrunk))
#tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
tocfilename = '/tmp/%s.toc' % (jnlfilename)
if not os.path.isfile(tocfilename):
    os.system('wget  -T 300 -t 3 -q  -O %s "%s"' % (tocfilename, urltrunk))
    time.sleep(2)
tocfil = open(tocfilename,'r')
tocpage = BeautifulSoup(''.join(tocfil.readlines()))
tocfil.close()

articleIDs = []
for li in tocpage.body.find_all('li'):
    for a in li.find_all('a'):
        if re.search('.*\/(\d+)', a['href']):
            articleID = re.sub('.*\/(\d+).*', r'\1', a['href'])
            if not articleID in done:
                if not articleID in articleIDs:
                    articleIDs.append(articleID)
print articleIDs


recs = []
i = 0
for articleID in articleIDs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(articleIDs), articleID)
    if re.search('isrn',jnl):
        artpage = BeautifulSoup(urllib2.urlopen('https://www.hindawi.com/journals/isrn/%s/%s' % (year, articleID)))
    else:
        #artpage = BeautifulSoup(urllib2.urlopen('%s/%s' % (urltrunk, articleID)))
        artfilename = '/tmp/hindawi.%s' % (articleID)
        if not os.path.isfile(artfilename):
            os.system('wget  -T 300 -t 3 -q  -O %s "%s/%s"' % (artfilename, urltrunk, articleID))
            time.sleep(2)
    artfil = open(artfilename,'r')
    artpage = BeautifulSoup(''.join(artfil.readlines()))
    artfil.close()
    rec = {'year' : year, 'jnl' : jnlname, 'p1' : articleID, 'tc' : 'P', 'vol' : year, 
           'auts' : [], 'aff' : [], 'refs' : [], 'note' : [], 'refs' : []}
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #DOI
            if meta['name'] == 'citation_doi':
                rec['doi'] = re.sub('http.*doi.org\/', '', meta['content'])
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #PDF-link
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #article type
            elif meta['name'] == 'prism.section':
                rec['note'].append(meta['content'])
                if re.search('Review', meta['content']):
                    rec['tc'] = 'R'
    #editorial
    for div in artpage.body.find_all('div', attrs = {'class' : 'article_type'}):
        if div.text == 'Editorial':
            rec['tc'] = 'Editorial'
    #licence
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['licence'] = {'url' : a['href']}
    #number of pages
    for pre in artpage.body.find_all('pre'):
        pretext = pre.text.strip()
        if re.search('Article ?ID.*\d+ pages', pretext):
            rec['pages'] = re.sub('.* (\d+) pages.*', r'\1', pretext)
    #abstract (better)
    for div  in artpage.body.find_all('div', attrs = {'class' : 'xml-content'}):
        for h4 in div.find_all('h4', attrs = {'class' : 'header'}):
            ps = div.find_all('p')
            rec['abs'] = ps[0].text.strip()
    #title (better)
    #for h2 in artpage.body.find_all('h2'):
    #    rec['tit'] = h2.text.strip()
    #authors
    for div in artpage.body.find_all('div', attrs = {'class' : 'article_authors'}):
        for child in div.children:
            try:
                child.name
            except:
                continue
            if child.name == 'span':
                affs = []
                orcid = False
                for sup in child.find_all('sup'):
                    affs = re.split(' *, *', sup.text.strip())
                    sup.replace_with('')
                for a in child.find_all('a'):
                    if a.has_attr('href') and re.search('orcid.org', a['href']):
                        orcid = re.sub('.*org\/(\d.*\d).*', r'ORCID:\1', a['href'])
                    a.replace_with('')
                author = re.sub(' *and$', '', re.sub(' *,', '', child.text.strip()))
                if orcid:
                    author += ', ' + orcid
                rec['auts'].append(author)
                for aff in affs:
                    rec['auts'].append('=Aff%s' % (aff))
            elif child.name == 'div':
                for sup in child.find_all('sup'):
                    supt = sup.text.strip()
                    sup.replace_with('Aff%s= ' % (supt))
                for p in child.find_all('p'):
                    rec['aff'].append(re.sub('[\n\t\r]', '', p.text.strip()))

    #references
    for ol in artpage.body.find_all('ol'):
        refnum = ''
        for li in ol.find_all('li'):
            if li.has_attr('id'):
                refnum = li['id']
            for a in li.find_all('a'):
                if re.search('doi.org\/10', a['href']):
                    doi = re.sub('http.*doi.org.', ', DOI: ', a['href'])
                    doi = re.sub('%2[fF]', '/', doi)                    
                    doi = re.sub('%28', '(', doi)                    
                    doi = re.sub('%29', ')', doi)                    
                    doi = re.sub('%20', ' ', doi)                    
                    doi = re.sub('%3a', ':', doi)                    
                    a.replace_with(doi)
                else:
                    a.replace_with('')
            lit = li.text.strip()
            #change pubnote to be digestable by refextract
            lit = re.sub(', no. [0-9]+, ', ', ', lit)
            lit = re.sub(', vol. ', ', ', lit)
            lit = re.sub(', Article ID ', ', ', lit)
            lit = re.sub(', pp. ', ', ', lit)
            lit = re.sub(u',\u201d', '",', lit)
            lit = re.sub(u'\u201c', '"', lit)
            lit = re.sub(u'\u2013', '-', lit)
            if refnum:                
                ref = '[%s] %s' % (refnum, lit)
            else:
                ref = li.text.strip()
            rec['refs'].append([('x', ref)])
    if rec['tc'] == 'Editorial':
        print 'skip Editorial'
    else:
        recs.append(rec)
        print ' keys: ' + ', '.join(rec.keys())




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
