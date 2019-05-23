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

if re.search('isrn',jnl):
    if re.search('astro',jnl):
        urltrunk = "http://www.isrn.com/journals/%s/%s/" % (re.sub('isrn','',jnl),year)
    else:
        urltrunk = "http://www.hindawi.com/journals/isrn/%s/%s/" % (year,re.sub('isrn','',jnl))
        urltrunk = re.sub('\/mp','/mathematical.physics',urltrunk)
else:
    urltrunk = "http://www.hindawi.com/journals/%s/%s/" % (jnl,year)

directoriestocheck = '%s/backup/%s*doki %s/backup/%i/%s*doki %s/backup/%i/%s*doki ' % (ejdir,jnl, ejdir, int(year), jnl, ejdir, int(year)-1, jnl)
done =  map(tfstrip,os.popen("grep '^3.*DOI' %s |sed 's/.*\///'|sed 's/;//'" % (directoriestocheck)))
print "Already done:"
for dd in done:
    print dd
#done = []
 
print "get table of content of %s%s ..." %(jnlname,year)

tocpage = BeautifulSoup(urllib2.urlopen(urltrunk))

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
        artpage = BeautifulSoup(urllib2.urlopen('http://www.hindawi.com/journals/isrn/%s/%s' % (year, articleID)))
    else:
        artpage = BeautifulSoup(urllib2.urlopen('%s/%s' % (urltrunk, articleID)))
    rec = {'year' : year, 'jnl' : jnlname, 'p1' : articleID, 'tc' : 'P', 'vol' : year, 
           'auts' : [], 'aff' : [], 'refs' : [], 'note' : [], 'refs' : []}
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #DOI
            if meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
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
    for h2 in artpage.body.find_all('h2'):
        rec['tit'] = h2.text.strip()
    #authors
    for div in artpage.body.find_all('div', attrs = {'class' : 'author_gp'}):
        for child in div.descendants:
            if type(child) == type(div):
                if child.name == 'a':
                    author = ''
                    for span in child.find_all('span', attrs = {'class' : 'surname'}):
                        author = span.text
                    for span in child.find_all('span', attrs = {'class' : 'given_names'}):
                        author += ', ' + span.text
                    if author:
                        rec['auts'].append(author)
                    else:
                        rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', child.text.strip()))
                elif child.name == 'span':
                    if child.has_attr('class') and 'orcid' in child['class']:
                        for a in child.find_all('a'):
                            orcid = re.sub('.*org\/', r'ORCID:', a['href'])
                            print '  ', orcid
                            rec['auts'][-1] += ', ' + orcid
                elif child.name == 'sup':
                    for aff in re.split(' *, *', child.text.strip()):
                        rec['auts'].append('=Aff%s' % (aff))
        #affiliations come right after
        p = div.next_sibling
        try:
            if p.find_all('sup'):
                aff = False
                for child in p.contents:
                    if type(child) == type(p):
                        if child.name == 'sup':
                            aff = 'Aff%s= ' % (child.text.strip())
                    elif aff:
                        aff += child
                        rec['aff'].append(aff)
            else:
                rec['aff'].append(p.text.strip())
        except:
            print p
            print '^_ could not extract afiliation'
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
    if not rec['tc'] == 'Editorial':
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
