# -*- coding: UTF-8 -*-
#program to harvest journals from the EDP journals
# FS 2016-10-05


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
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'EDP Sciences'
tc = 'P'
jnl = sys.argv[1]
year = sys.argv[2]
issue = sys.argv[3]
if len(sys.argv) > 4:
    cnum = sys.argv[4]
    tc = 'C'

if   (jnl == 'epjconf'): 
    jnlname = 'EPJ Web Conf.'
    #urltrunk = 'http://www.epj-conferences.org/index.php?option=com_toc&url=/articles/epjconf/abs'
    urltrunk = 'http://www.epj-conferences.org/articles/epjconf/abs/'
    tc = 'C'
elif (jnl == 'ljpc'): 
    jnlname = 'J.Phys.Colloq.'
    urltrunk = 'http://jphyscol.journaldephysique.org/articles/jphyscol/abs/'
    tc = 'C'
elif (jnl == 'easps'): 
    jnlname = 'EAS Publ.Ser.'
    urltrunk = 'http://www.eas-journal.org/articles/eas/abs/'
    tc = 'C'
elif (jnl == 'aanda'):
    jnlname = 'Astron.Astrophys.'
    urltrunk = 'http://www.aanda.org/index.php?option=com_toc&url=/articles/aa/abs/'
    tc = 'P'
elif (jnl == 'aandas'):
    jnlname = 'Astron.Astrophys.Suppl.Ser.'
    urltrunk = 'https://aas.aanda.org/articles/aas/abs/'
    tc = 'P'
elif (jnl == '4open'):
    jnlname = '4open'
    urltrunk = 'https://www.4open-sciences.org/articles/fopen/abs/'
    tc = 'P'


if (jnl == '4open'):
    jnlfilename = "%s%s.%s_%s" % (jnl, year, issue, stampoftoday)
    toclink = "%s%s/%02i/contents/contents.html" % (urltrunk, year, int(issue))
else:
    jnlfilename = "%s%s.%s" % (jnl, year, issue)
    toclink = "%s%s/%s/contents/contents.html" % (urltrunk, year, issue)

print "get table of content..."

try:
    tocpage = BeautifulSoup(urllib2.urlopen(toclink))
except:
    print "wait 5 minutes, retry %s" % (toclink)
    time.sleep(300)
    tocpage = BeautifulSoup(urllib2.urlopen(toclink))


recs = []
i = 0
articleas = tocpage.find_all('a', attrs = {'class' : 'article_title'}) 
for a in articleas:
    i += 1
    rec = {'jnl' : jnlname, 'tc' : tc, 'year' : year, 'note' : [], 'autaff' : []}
    if len(sys.argv) > 4:
        rec['tc'] = 'C'
        rec['cnum'] = cnum
    #title
    rec['tit'] = a.text.strip()
    artlink = re.sub('(.*\.org)\/.*', r'\1', toclink) + a['href']
    #check article page
    time.sleep(10)
    try:
        artpage = BeautifulSoup(urllib2.urlopen(artlink))
    except:
        print "wait 5 minutes, retry %s" % (artlink)
        time.sleep(300)
        artpage = BeautifulSoup(urllib2.urlopen(artlink))
    autaff = False
    #check metatags
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            elif meta['name'] == 'citation_doi':
                rec['doi'] = re.sub('^doi:', '', meta['content'])
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content']
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = re.sub('\/', '-', meta['content'])
            elif meta['name'] == 'prism.issueName':
                rec['note'].append(meta['content'])
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'fr':
                    rec['language'] = 'French'
            elif meta['name'] in ['citation_keywords', 'citation_keyword']:
                if rec.has_key('keyw'):
                    rec['keyw'].append(meta['content'])
                else:
                    rec['keyw'] = [ meta['content'] ]
            elif meta['name'] == 'citation_collaboration':
                collaboration = re.sub('^[tT]he ', '', meta['content'])
                rec['col'] = re.sub(' Collaboration', '', collaboration)
            elif meta['name'] == 'prism.section':
                rec['note'].append(meta['content'])
            #autaff
            elif meta['name'] == 'citation_author':
                if autaff:
                    rec['autaff'].append(autaff)
                autaff = [ meta['content'] ]
            elif meta['name'] == 'citation_author_institution':
                autaff.append(meta['content'])
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                autaff.append('ORCID:%s' % (orcid))
            elif meta['name'] == 'citation_author_email':
                email = meta['content']
                autaff.append('EMAIL:%s' % (email))    
    if autaff:
        rec['autaff'].append(autaff)
    if rec.has_key('issue'):
        print '-- %i/%i -- %s %s (%s), no. %s, %s' % (i, len(articleas), jnlname, rec['vol'], rec['year'], rec['issue'], rec['p1'])
    elif rec.has_key('vol'):
        print '-- %i/%i -- %s %s (%s), %s' % (i, len(articleas), jnlname, rec['vol'], rec['year'], rec['p1'])
    else:
        print '-- %i/%i -- %s (%s), %s' % (i, len(articleas), jnlname, rec['year'], rec['p1'])
    #abstract 
    for div in artpage.body.find_all('div', attrs = {'id' : 'article'}):
        for p in div.find_all('p', attrs = {'align' : 'LEFT'}):
            rec['abs'] = p.text.strip()
            rec['abs'] = re.sub('^abstract *:? *', '', rec['abs'])
        if not rec.has_key('abs'):
            for div2 in div.find_all('div', attrs = {'id' : 'head'}):
                rec['abs'] = re.sub('.*Abstract', '', re.sub('\n', '', div2.text)).strip()
    #strip issue from page number ? 
    if jnl in ['ljpc']:
        if rec.has_key('p1'):
            rec['p1'] = re.sub('.*\-', '', rec['p1'])
        if rec.has_key('p2'):
            rec['p2'] = re.sub('.*\-', '', rec['p2'])
    #number of pages
    if not rec.has_key('p2'):
        for tr in artpage.body.find_all('tr'):
            nop = False
            for th in tr.find_all('th'):
                if re.search('Number of page', th.text):
                    nop = True
            if nop:
                for td in tr.find_all('td'):
                    pages = td.text.strip()
                    if re.search('^\d+$', pages):
                        rec['pages'] = pages
    #licence and PDF
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['licence'] = {'url' : a['href']}
        if re.search('creativecommons', a['href']):
            #look for fulltext
            for meta in artpage.head.find_all('meta', attrs = {'name': 'citation_pdf_url'}):
                rec['FFT'] = meta['content']
            if not rec.has_key('FFT'):
                for a2 in artpage.body.find_all('a'):
                    if a2.has_key('title') and re.search('^PDF', a2['title']):
                        if a2.has_key('href') and re.search('pdf$', a2['href']):
                            rec['FFT'] = a2['href']
        #edpj gives incomplete links to PDF
        if not re.search('www', rec['FFT']):
            pdflink = re.sub('.*articles', '/articles', rec['FFT'])
            rec['FFT'] = re.sub('(.*?www.*?)\/.*', r'\1', urltrunk) + pdflink            
    #references
    for a in artpage.body.find_all('a', attrs = {'title' : 'References'}):
        reflink = re.sub('(.*\.org)\/.*', r'\1', toclink) + a['href']
        time.sleep(10)
        try:
            refpage = BeautifulSoup(urllib2.urlopen(reflink))
        except:
            print '%s not found' % (reflink)
            break
        list = refpage.body.find_all('ol', attrs = {'class' : 'references'})
        if not list:
            list = refpage.body.find_all('ul', attrs = {'class' : 'references'})
        for ol in list:
            rec['refs'] = []
            for li in ol.find_all('li'):
                reference = re.sub('[\t\n]+', ' ', li.text).strip()
                reference = re.sub(' +', ' ', reference)
                reference = re.sub('\[NASA ADS\]', '', reference)
                reference = re.sub('\[CrossRef\]', '', reference)
                reference = re.sub('\[Google.Scholar\]', '', reference)
                reference = re.sub('\[PubMed\]', '', reference)
                reference = re.sub('\[EDP Sciences\]', '', reference)
                for a2 in li.find_all('a'):
                    if re.search('\[CrossRef\]', a2.text):
                        rdoi = a2['href']
                        rdoi = re.sub('http.*.doi.org.', ', DOI: ', rdoi)
                        reference += rdoi
                rec['refs'].append([('x', reference)])
    if rec['autaff']:
        recs.append(rec)
    else:
        print 'no authors ?!'


  
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
