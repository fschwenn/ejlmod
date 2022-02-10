# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest journals from OSA publishing
# FS 2018-09-20

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

publisher = 'OSA Publishing'
typecode = 'P'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]
cnum = False
if (jnl == 'oe'): 
    jnlname = 'Opt.Express'
elif (jnl == 'ao'): 
    jnlname = 'Appl.Opt.'
elif (jnl == 'ol'):
    jnlname = 'Opt.Lett.'
elif (jnl == 'josaa'): 
    jnlname = 'J.Opt.Soc.Am.'
    vol = 'A' + sys.argv[2]
elif (jnl == 'josab'): 
    jnlname = 'J.Opt.Soc.Am.'
    vol = 'B' + sys.argv[2]
elif (jnl == 'optica'):
    jnlname = 'Optica'
else:
    print ' do not know "%s"' % (jnl)
    sys.exit(0)
    
jnlfilename = 'OSA_%s%s.%s' % (jnl, vol, issue)
if len(sys.argv) > 4:
    cnum = sys.argv[4]
    jnlfilename += '_' + cnum
    typecode = 'C'


urltrunk = 'https://www.osapublishing.org/%s/issue.cfm?volume=%s&issue=%s' % (jnl, vol, issue)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk), features="lxml")
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk),features="lxml" )


done = ['https://www.osapublishing.org/josab/abstract.cfm?uri=josab-36-7-E112']
(level0note, level1note) = (False, False)
recs = []
year = False
for h2 in tocpage.find_all('h2', attrs = {'class' : 'heading-block-header'}):
    if re.search(' 20\d\d', h2.text):
        year = re.sub('.* (20\d\d).*', r'\1', re.sub('[\n\t\r]', '', h2.text.strip()))
divs = tocpage.body.find_all('div', attrs = {'class' : 'osap-accordion'})
if not divs:
    divs = tocpage.find_all('body')
for div in divs:
    for label in div.find_all('label'):
        level0note = label.text.strip()
    for div2 in div.find_all('div', attrs = {'class' : 'row'}):
        for h2 in div2.find_all('h2'):
            level1note = h2.text.strip()
        for p in div2.find_all('p', attrs = {'class' : 'article-title'}):
            rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'tc' : typecode,
                   'note' : [], 'keyw' : [], 'autaff' : [], 'refs' : []}
            if cnum:
                rec['cnum'] = cnum
            if level0note:
                rec['note'].append(level0note)
            if level1note:
                rec['note'].append(level1note)
            if year:
                rec['year'] = year
            for a in p.find_all('a'):
                rec['tit'] = p.text.strip()
                rec['artlink'] = 'https://www.osapublishing.org' + a['href']
            if not rec['artlink'] in done:                
                recs.append(rec)
                done.append(rec['artlink'])
        #pages
        for p in div2.find_all('p', attrs = {'style' : 'color: #999'}):
            pt = re.sub('[\n\t\r]', '', p.text.strip()) 
            if re.search('\), \d+\-\d+', pt):
                rec['p1'] = re.sub('.*\), (\d+)\-.*', r'\1', pt)
                rec['p2'] = re.sub('.*\), \d+\-(\d+).*', r'\1', pt)
        #authors
        for p in div2.find_all('p', attrs = {'class' : 'article-authors'}):
            rec['auts'] = []
            for aut in re.split('(,| and) ', p.text.strip()):
                rec['auts'].append(re.sub('^and ', '', aut))

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(5)
    except:
        print "retry %s in 180 seconds" % (artlink)
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    print '   read meta tags'
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            print meta['name']
            if meta['name'] == 'dc.description':
                rec['abs'] = meta['content']
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            elif meta['name'] == 'dc.subject':
                rec['keyw'].append(meta['content'])
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
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            elif meta['name'] == 'citation_online_date':
                rec['date'] = meta['content']
            elif meta['name'] == 'citation_publication_date':
                rec['year'] = meta['content'][:4]
            elif meta['name'] == 'citation_pdf_url':
                if jnl in ['oe', 'boe', 'optica', 'ome', 'osac']:
                    rec['FFT'] = meta['content']
    #references
    j = 0
    for ol in artpage.find_all('ol', attrs = {'id' : 'referenceById'}):
        lis = ol.find_all('li')
        print '   read %i references' % (len(lis))
        for li in lis:
            j += 1
            for a in li.find_all('a'):
                if re.search('Crossref', a.text):
                    alink = a['href']
                    a.replace_with(re.sub('.*doi.org\/', ', DOI: ', alink))
                elif not re.search('osa\.org\/abstract', a['href']):
                    a.replace_with('')
            ref = re.sub('[\n\t]', ' ', li.text.strip())
            ref = '[%i] %s' % (j, re.sub('\. *, DOI', ', DOI', ref))
            rec['refs'].append([('x', ref)])
    if not rec['autaff']:
        del rec['autaff']
    print '  ', rec.keys()





                                       
#closing of files and printing
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
 
