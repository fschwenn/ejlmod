# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Communications/Papers in Physics
# FS 2017-12-13

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

typecode = 'P'

jnl = sys.argv[1]
vol = sys.argv[2]

if jnl == 'pip':
    publisher = 'Papers in Physics'
    jnlname = 'Papers Phys.'
    urltrunk = 'http://www.papersinphysics.org/papersinphysics/issue/view/%s' % (vol)
elif jnl == 'cip':
    publisher = 'Publishing House for Science and Technology, Vietnam Academy of Science and Technology'
    jnlname = 'Commun.Phys.'
    urltrunk = 'http://vjs.ac.vn/index.php/cip/issue/view/%s/showToc' % (vol)
elif jnl == 'eureka':
    publisher = 'Scientific Route OU'
    jnlname = 'Eureka'
    urltrunk = 'http://eu-jr.eu/engineering/issue/view/%s' % (vol)

    
now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = '%s%s_%s' % (jnl, vol, stampoftoday)


    
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))

recs = []
if jnl == 'pip':
    tables = tocpage.body.find_all('div', attrs = {'class' : 'obj_article_summary'})
elif jnl == 'cip':
    tables = tocpage.body.find_all('table', attrs = {'class' : 'tocArticle'})
elif jnl == 'eureka':
    tables = tocpage.body.find_all('table', attrs = {'class' : 'tocArticle'})

for table in tables:
    rec = {'jnl' : jnlname, 'tc' : typecode, 'vol' : vol, 'keyw' : [], 'autaff' : [], 'refs' : []}
    #PDF
    for a in table.find_all('a'):
        if re.search('PDF', a.text):
            rec['FFT'] = re.sub('\/view\/', '/download/', a['href'])
    #article link
    for td in table.find_all('td', attrs = {'class' : 'tocTitle'}):
        rec['tit'] = td.text.strip()
        for a in td.find_all('a'):
            rec['artlink'] = a['href']
    if not rec.has_key('tit'):
        for div in table.find_all('div', attrs = {'class' : 'tocTitle'}):
            rec['tit'] = div.text.strip()
            for a in div.find_all('a'):
                rec['artlink'] = a['href']
    if not rec.has_key('tit'):
        for div in table.find_all('div', attrs = {'class' : 'title'}):
            rec['tit'] = div.text.strip()
            for a in div.find_all('a'):
                rec['artlink'] = a['href']
    recs.append(rec)


i = 0
for rec in recs:
    i += 1
    autaff = False
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #article ID
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #authors and affiliations
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([ meta['content'] ])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            #volume and issue
            if meta['name'] == 'citation_issue':
                if jnl in ['cip', 'eureka']:
                    rec['issue'] = meta['content']
            if meta['name'] == 'citation_volume':
                if jnl == 'cip':
                    rec['vol'] = meta['content']
    #year as volume
    if jnl == 'eureka':
        rec['vol'] = re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])
    #authors, 2nd possibility
    if not rec['autaff']:
        for div in artpage.body.find_all('div', attrs = {'id' : 'authorBio'}):
            for p in div.find_all('p'):
                for em in p.find_all('em'):
                    rec['autaff'].append([ em.text ])
                    em.replace_with('')
                aff = p.text.strip()
                if aff != 'normally':
                    rec['autaff'][-1].append(re.sub('[\n\t\r]', ' ', aff))
    #keywords aftermath
    if len(rec['keyw']) == 1:
        rec['keyw'] = re.split(', ', rec['keyw'][0])
    #abstract
    divs = artpage.body.find_all('div', attrs = {'id' : 'articleAbstract'})
    if not divs:
        divs = artpage.body.find_all('div', attrs = {'class' : 'abstract'})
    for div in divs:
        for p in div.find_all('p'):
            if not rec.has_key('abs'):
                rec['abs'] = p.text
                break
        if not rec.has_key('abs'):
            for div2 in div.find_all('div'):
                rec['abs'] = div2.text
    #license
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['licence'] = {'url' : a['href']}
    #references
    if jnl == 'pip':
        reflink = False
        #reflink = re.sub('(.*)\/(.*)', r'https://www.papersinphysics.org/papersinphysics/article/download/\2/ref\2?inline=1', rec['artlink'])
        for a in artpage.body.find_all('a', attrs = {'class' : 'obj_galley_link file'}):
            if re.search('REFERENCES', a.text):
                reflink = re.sub('view', 'download', a['href'])
        if reflink:
            print reflink
            refpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(reflink))
            for a in refpage.body.find_all('a'):
                if a.has_attr('href') and re.search('doi.org', a['href']):
                    rdoi = re.sub('.*doi.org\/', '', a['href'])
                    a.replace_with(', DOI: %s' % (rdoi))
            allrefs = re.sub('[\n\t\r]', ' ', refpage.body.text.strip())
            allrefs = re.sub('  +', ' ', allrefs)
            allrefs = re.sub('\. *, DOI:', ', DOI:', allrefs)        
            for ref in re.split('\[\d+\] +', allrefs):
                rec['refs'].append([('x', ref)])
        else:
            print '   no references!'    
    elif jnl in ['cip', 'eureka']:
        for div in artpage.body.find_all('div', attrs = {'id' : 'articleCitations'}):
            for p in div.find_all('p'):
                rec['refs'].append([('x', p.text.strip())])
    print [(k, len(k)) for k in rec.keys()]

                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
