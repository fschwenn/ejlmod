# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Andromeda-journals
# FS 2015-02-11

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
pdfdir = '/afs/desy.de/group/library/publisherdata/pdf'
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

publisher = 'Andromda'
typecode = 'P'

jnl = sys.argv[1]
issuenumber = sys.argv[2]

if jnl == 'lhep':
    jnlname = 'LHEP'
    tocurl = 'http://journals.andromedapublisher.com/index.php/LHEP/issue/view/' + issuenumber
elif jnl == 'jmlfs':
    jnlname = 'JMLFS'
    tocurl = 'http://journals.andromedapublisher.com/index.php/JMLFS/issue/view/' + issuenumber
elif jnl == 'jais':
    jnlname = 'JAIS'
    tocurl = 'http://journals.andromedapublisher.com/index.php/JAIS/issue/view/' + issuenumber
elif jnl == 'acp':    
    jnlname = 'BOOK'
    tocurl = ' http://main.andromedapublisher.com/ACP/' + issuenumber
    typecode = 'C'

print tocurl
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")

recs = []
for div in tocpage.find_all('div', attrs = {'class' : 'title'}):
    for a in div.find_all('a'):
        rec = {'jnl': jnlname, 'tc' : typecode, 'autaff' : [], 'keyw' : []}
        rec['tit'] = a.text.strip()
        rec['artlink'] = a['href']
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        print rec['artlink']
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'] )
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #PBN
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content'] 
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content'] 
            #elif meta['name'] == 'citation_firstpage':
            #    rec['p1'] = meta['content'] 
            #elif meta['name'] == 'citation_lastpage':
            #    rec['p2'] = meta['content'] 
            elif meta['name'] == 'DC.Identifier' and re.search('^\d{1,5}', meta['content']):
                rec['p1'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                if re.search(', .*, ', meta['content']):
                    rec['keyw'] += re.split(', ', meta['content'])
                else:
                    rec['keyw'].append(meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.Description':
                rec['abs'] = meta['content']
            #license
            elif meta['name'] == 'DC.Rights':
                rec['license'] = {'url' : meta['content']}
    #year as volume for LHEP and JAIS
    if not 'vol' in rec.keys() and jnl in ['lhep', 'jais']:
        rec['vol'] = re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])
    #licence
    if not 'license' in rec.keys():
        for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
            rec['license'] = {'url' : a['href']}
    #references
    for div in artpage.body.find_all('div', attrs = {'class' : 'item references'}):
        rec['refs'] = []
        for div2 in div.find_all('div'):
            for br in div2.find_all('br'):
                br.replace_with('_TRENNER_')
            div2t = re.sub('\. *\[(\d+)\] ', r'._TRENNER_[\1] ', div2.text)
            for ref in re.split('_TRENNER_', div2t):
                rec['refs'].append([('x', ref)])    
    #get PDF to extract DOI !!!
    if not 'doi' in rec.keys():
        if not os.path.isfile('/tmp/%s.%s.%i.pdf' % (rec['jnl'], stampoftoday ,i)):
            os.system('wget -O /tmp/%s.%s.%i.pdf "%s"' % (rec['jnl'], stampoftoday ,i, rec['FFT']))
        os.system('pdftotext /tmp/%s.%s.%i.pdf /tmp/%s.%s.%i.txt' % (rec['jnl'], stampoftoday, i, rec['jnl'], stampoftoday ,i))
        inf = open('/tmp/%s.%s.%i.txt' % (rec['jnl'], stampoftoday ,i), 'r')
        for line in inf.readlines():
            if re.search('DOI.*(10\.31526\/)', line) and not rec.has_key('doi'):
                rec['doi'] = re.sub('.*?(10\.31526\/.*)', r'\1', line.strip())
                rec['doi'] = re.sub(' .*', '', rec['doi'])
                os.system('cp /tmp/%s.%s.%i.pdf %s/10.31526/%s' % (rec['jnl'], stampoftoday ,i, pdfdir, re.sub('\/', '_', rec['doi'])))
        inf.close()
    print rec.keys()


if recs:
    if 'issue' in rec.keys():
        jnlfilename = '%s%s.%s_%s' % (jnl, rec['vol'], rec['issue'], stampoftoday)
    else:
        jnlfilename = '%s%s_%s' % (jnl, rec['vol'], stampoftoday)
elif jnl in ['acp']:
    recs = []
    jnlfilename = '%s%s_%s' % (jnl, issuenumber, stampoftoday)
    for div in tocpage.find_all('div', attrs = {'class' : 'col-md-8'}):
        for div2 in div.find_all('div', attrs = {'class' : 'container'}):
            rec = {'jnl': jnlname, 'tc' : typecode, 'auts' : [], 'aff' : []}
            #year
            rec['year'] = sys.argv[3]
            #cnum
            if len(sys.argv) > 4:
                rec['cnum'] = sys.argv[4]
            #title
            for h2 in div2.find_all('h2', attrs = {'class' : 'text-primary'}):
                rec['tit'] = h2.text.strip()
            #abstract
            for div3 in div2.find_all('div', attrs = {'class' : 'collapse'}):
                for p in div3.find_all('p'):
                    rec['abs'] = p.text.strip()
                div3.decompose()
            #authors
            for h2 in div2.find_all('h2', attrs = {'class' : 'text-secondary'}):
                for sup in h2.find_all('sup'):
                    aff = sup.text
                    sup.replace_with(', =Aff%s, ' % (aff))
                for aut in re.split(' *, *', re.sub('[\n\t\r]', ' ', h2.text.strip())):
                    if re.search('\w', aut):
                        rec['auts'].append(aut)
            #affiliations
            for p in div2.find_all('p'):
                for sup in p.find_all('sup'):
                    aff = sup.text
                    sup.replace_with(' XXX Aff%s= ' % (aff))
                rec['aff'] = re.split(' +XXX +', re.sub('[\n\t\r]', ' ', p.text))[1:]
            #fulltext
            for a in div2.find_all('a'):
                if a.has_attr('href') and re.search('\.pdf', a['href']):
                    rec['FFT'] = 'http://main.andromedapublisher.com' + a['href'].strip()
                    rec['link'] = 'http://main.andromedapublisher.com' + a['href'].strip()
                    rec['doi'] = '20.2000/Andromeda/' + re.sub('\W', '', a['href'].strip()[10:])
            if rec['auts']:
                print rec.keys()
                recs.append(rec)
                    
                    
                
            
                                     

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
 
