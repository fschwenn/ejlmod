# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest an individual book from CUP
# FS 2020-06-17


import sys
import os
import ejlmod2
import re
import urllib2,cookielib
import urlparse
import codecs
import time
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'Cambridge University Press'

toclink = sys.argv[1]

jnlfilename = 'cambridge'+re.sub('\W', '', re.sub('.*books\/', '', toclink))
        
if not os.path.isfile('/tmp/%s.0.toc' % (jnlfilename)):
    os.system('wget -O /tmp/%s.0.toc "%s"' % (jnlfilename, toclink))
tocf = open('/tmp/%s.0.toc' % (jnlfilename), 'r')
tocpage = BeautifulSoup(''.join(tocf.readlines()), features="lxml")
tocf.close()

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
recs = []
#main entry for book
rec = {'tc' : 'B', 'jnl' : 'BOOK', 'autaff' : [], 'isbns' : [], 'p1' : '1'}
for meta in tocpage.head.find_all('meta'):
    if meta.attrs.has_key('name'):
        #title
        if meta['name'] == 'citation_title':
            rec['tit'] = meta['content']
        #DOI
        elif meta['name'] == 'citation_doi':
            rec['doi'] = meta['content']
        #authors
        elif meta['name'] == 'citation_editor':
            rec['autaff'].append([meta['content'].title() + ' (Ed.)'])
        elif meta['name'] == 'citation_editor_institution':
            rec['autaff'][-1].append(meta['content'])
        elif meta['name'] == 'citation_editor_email':
            email = meta['content']
            rec['autaff'][-1].append('EMAIL:%s' % (email))
        elif meta['name'] == 'citation_editor_orcid':
            orcid = re.sub('.*\/', '', meta['content'])
            rec['autaff'][-1].append('ORCID:%s' % (orcid))
        #date
        elif meta['name'] == 'citation_online_date':
            rec['date'] = meta['content']
        #keywords
        elif meta['name'] == 'citation_keywords':
            rec['keyw'] += re.split(' *; *', meta['content'])
        #ISBN
        elif meta['name'] == 'citation_isbn':
            rec['isbns'].append([('a', meta['content'])])
recs.append(rec)

note = False
for h5 in tocpage.body.find_all('h5'):
    for a in h5.find_all('a', attrs = {'class' : 'part-link'}):
        rec = {'refs' : [], 'tc' : 'S',
               'autaff' : [], 'keyw' : [], 'jnl' : 'BOOK'}
        rec['tit'] = a.text.strip()
        if not rec['tit'] in ['Frontmatter', 'Contents', 'List of Contributors', 'Index']:
            rec['artlink'] = 'https://www.cambridge.org' + a['href']
            print rec['artlink']
            req = urllib2.Request(rec['artlink'], headers=hdr)
            try:
                artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
                time.sleep(10)
            except:
                print 'wait 3 minutes befor trying  again'
                time.sleep(180)
                req = urllib2.Request(rec['artlink'], headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
            time.sleep(2)
            for meta in artpage.head.find_all('meta'):
                if meta.attrs.has_key('name'):
                    #title
                    if meta['name'] == 'citation_title':
                        rec['tit'] = meta['content']
                    #pubnote
                    elif meta['name'] == 'citation_firstpage':
                        rec['p1'] = meta['content']
                    elif meta['name'] == 'citation_lastpage':
                        rec['p2'] = meta['content']
                        recs[0]['p2'] = meta['content']
                    elif meta['name'] == 'citation_publication_date':
                        rec['year'] = meta['content'][:4]
                    #DOI
                    elif meta['name'] == 'citation_doi':
                        rec['doi'] = meta['content']
                    #authors
                    elif meta['name'] == 'citation_author':
                        rec['autaff'].append([meta['content'].title()])
                    elif meta['name'] == 'citation_author_institution':
                        rec['autaff'][-1].append(meta['content'])
                    elif meta['name'] == 'citation_author_email':
                        email = meta['content']
                        rec['autaff'][-1].append('EMAIL:%s' % (email))
                    elif meta['name'] == 'citation_author_orcid':
                        orcid = re.sub('.*\/', '', meta['content'])
                        rec['autaff'][-1].append('ORCID:%s' % (orcid))
                    #date
                    elif meta['name'] == 'citation_online_date':
                         rec['date'] = meta['content']
                    #keywords
                    elif meta['name'] == 'citation_keywords':
                         rec['keyw'] += re.split(' *; *', meta['content'])
            #ISBN
            for isbn in recs[0]['isbns']:
                rec['motherisbn'] = isbn[0][1]
            #abstract
            for div in artpage.body.find_all('div', attrs = {'class' : 'abstract'}):
                for tit in div.find_all('title'):
                    tit.replace_with('')
                rec['abs'] = div.text.strip()
                rec['abs'] = re.sub('[\n\t\r]', ' ', rec['abs'])
                rec['abs'] = re.sub('  +', ' ', rec['abs'])
            #references (only with DOI)
            for div in artpage.body.find_all('div', attrs = {'id' : 'references'}):
                for child in div.children:
                    try:
                        child.name
                    except:
                        continue
                    if child.name == 'div':
                        reference = child.text.strip()
                    elif child.name == 'ul':
                        for a in child.find_all('a'):
                            if a.text == 'CrossRef':
                                refdoi = re.sub('.*doi.org.', '', a['href'])
                                reference += ', DOI: ' + refdoi
                    elif child.name == 'hr':
                        rec['refs'].append([('x', reference)])
                #(new/other) references
                if not rec['refs']:
                    for div2 in div.find_all('div', attrs = {'class' : 'ref'}):
                        rec['refs'].append([('x', div2.text.strip())])
            #licence
            for div in artpage.body.find_all('div', attrs = {'class' : 'description'}):
                for div2 in div.find_all('div', attrs = {'class' : 'margin-top'}):
                    div2text = div2.text.strip()
                    if re.search('creativecommons.org', div2text):
                        rec['licence'] = {'url' : re.sub('.*(http.*?creativecommons.*?0).*', r'\1', div2text)}
                        for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                            rec['FFT'] = meta['content']
            if rec['autaff']:
                if note: rec['note'] = [note]
                print '  ', rec.keys()
                recs.append(rec)
            else:
                print '  skip', rec['tit']
                note = rec['tit']
                
        
        
        
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
