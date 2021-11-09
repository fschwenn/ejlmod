# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Nucl.Phys.Rev.
# FS 2021.11.01

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special/'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" + '_special'

def tfstrip(x): return x.strip()

publisher = 'Chinese Academy of Sciences'
year = sys.argv[1]
iss = sys.argv[2]

jnlfilename = 'npreview%s.%s' % (year, iss)

hdr = {'User-Agent' : 'Mozilla/5.0'}

starturl = 'http://www.npr.ac.cn/en/article/%s/%s' % (year, iss)
prerecs = []



###clean formulas in tag
def cleanformulas(output):
    #change html-tags into LaTeX
    output = re.sub('<em>', '$', output)
    output = re.sub('</em>', '$', output)
    output = re.sub('<sub>', '$_{', output)
    output = re.sub('</sub>', '}$', output)
    output = re.sub('<sup>', '$^{', output)
    output = re.sub('</sup>', '}$', output)
    output = re.sub('\$\$', '', output)
    return output



print starturl
req = urllib2.Request(starturl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
note = False
for div in tocpage.find_all('div', attrs = {'class' : 'articleListBox'}):
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'div' and child.has_attr('class'):
            if 'article-list-journalg' in child['class']:
                note = child.text.strip()
                print ' -', note
            elif 'article-list' in child['class']:
                for divart in child.find_all('div', attrs = {'class' : 'article-list-right'}):
                    rec = {'jnl' : 'Nucl.Phys.Rev.', 'tc' : 'P', 'year' : year,
                           'keyw' : []}
                    if note:
                        rec['note'] = [ note ]
                    for divtit in divart.find_all('div', attrs = {'article-list-title'}):
                        for a in divtit.find_all('a'):
                            rec['tit'] = cleanformulas(a.text.strip())
                            rec['artlink'] = a['href']
                    if note and not note in ['content']:
                        prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(prerecs), rec['artlink'])
    #get detailed page
    artffilename = '/tmp/npreview.%s' % (re.sub('\/', '_', rec['artlink'][36:]))
    if not os.path.isfile(artffilename):
        time.sleep(3)
        os.system('wget -T 300 -t 3 -q -O %s "%s"' % (artffilename, rec['artlink']))
    inf = codecs.EncodedFile(codecs.open(artffilename, mode='r'), 'utf8')
    page = BeautifulSoup(''.join(inf.readlines()), features="lxml")
    inf.close()
#    try:        
#        time.sleep(3)
#        artreq = urllib2.Request(rec['artlink'], headers=hdr)
#        page = BeautifulSoup(urllib2.urlopen(artreq), features="lxml")
#    except:
#        print '   ... wait 15 minutes'
#        time.sleep(900)
#        artreq = urllib2.Request(rec['artlink'], headers=hdr)
#        page = BeautifulSoup(urllib2.urlopen(artreq), features="lxml")
    for meta in page.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #keywords
            if meta['name'] == 'dc.subject':
                rec['keyw'].append( cleanformulas(meta['content']) )
            #date
            elif meta['name'] == 'dc.date':
                rec['date'] = meta['content']
            #fulltext (points just to the article page)
            #elif meta['name'] == 'citation_pdf_url':
            #    rec['citation_pdf_url'] = meta['content']
            #license
            elif meta['name'] == 'dc.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
            #publication note
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content']
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                if re.search('^10\.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
            #abstract
            elif meta['name'] == 'dc.description':
                rec['abs'] = cleanformulas(meta['content'])
            #language
            elif meta['name'] == 'dc.language':
                if meta['content'] == 'zh':
                    rec['language'] = 'Chinese'                    
    #Fulltext
    for footer in page.body.find_all('footer'):
        for a in footer.find_all('a'):
            if re.search('PDF', a.text):
                rec['citation_pdf_url'] = 'http://www.npr.ac.cn' + a['href']
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    #authors    
    for ul in page.body.find_all('ul', attrs = {'class' : 'article-author'}):
        if not 'auts' in rec.keys():
            rec['auts'] = []
            for li in ul.find_all('li'):
                affs = []
                for sup in li.find_all('sup'):
                    for span in sup.find_all('span', attrs = {'class' : 'com-num'}):
                        affs = re.split(',', span.text.strip())
                    sup.decompose()
                for a in li.find_all('a'):
                    author = re.sub('(.*) ([A-Z][A-Z].*)', r'\2, \1', a.text.strip()).title()
                    if a.has_attr('data-relate') and re.search('@', a['data-relate']):
                        author += ', EMAIL:%s' % (a['data-relate'])
                    rec['auts'].append(author)
                for aff in affs:
                    rec['auts'].append('=Aff%s' % (aff))
    #affiliations
    for ul in page.body.find_all('ul', attrs = {'class' : 'about-author'}):
        if not 'aff' in rec.keys():
            rec['aff'] = []
            for li in ul.find_all('li'):
                for span in li.find_all('span'):
                    spant = re.sub('\.', '', span.text.strip())
                    span.replace_with('Aff%s= ' % (spant))
                rec['aff'].append(re.sub('[\n\t\r]', ' ', li.text.strip()).strip())
    #references
    for table in page.body.find_all('table', attrs = {'class' : 'reference-tab'}):
        if not 'refs' in rec.keys():
            rec['refs'] = []
            for tr in table.find_all('tr'):
                rdoi = False
                for a in tr.find_all('a'):
                    if a.has_attr('href') and re.search('doi.org\/10', a['href']):
                        rdoi = re.sub('.*doi.org\/', 'doi:', a['href'])
                if rdoi:
                    for td in table.find_all('td', attrs = {'valign' : 'top'}):
                        refnum = re.sub('\D', '', td.text.strip())
                ref = re.sub('  +', ' ', re.sub('[\n\t\r]', '', tr.text.strip()))
                if rdoi:
                    rec['refs'].append([('o', refnum), ('a', rdoi), ('x', ref)])
                else:
                    rec['refs'].append([('x', ref)])                
    #original title
    if 'language' in rec.keys():
        try:
            time.sleep(3)
            artcnreq = urllib2.Request(re.sub('\/en', '', rec['artlink']), headers=hdr)
            pagecn = BeautifulSoup(urllib2.urlopen(artcnreq), features="lxml")
            for meta in pagecn.head.find_all('meta', attrs = {'name' : 'dc.title'}):
                rec['transtit'] = rec['tit']
                rec['tit'] =  cleanformulas(meta['content'])
        except:
            print '   could not get Chinese title from', re.sub('\/en', '', rec['artlink'])
    if not 'doi' in rec.keys() or not rec['doi']:
        if not 'auts' in rec.keys() or not rec['auts']:
            continue
    if 'language' in rec.keys():
        print '     skip articles completely in Chinese'
        continue
    recs.append(rec)
    print '  ', rec.keys()


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

