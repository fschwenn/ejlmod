# -*- coding: utf-8 -*-
#harvest journal "AAPPS Bull."
#FS: 2020-11-11

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"+'_special'

year = sys.argv[1]
iss = sys.argv[2]

publisher = 'Association of Asia Pacific Physical Societies'


hdr = {'User-Agent' : 'Magic Browser'}
recs = []
starturl = 'http://aappsbulletin.org/'
print '==={ %s }===' % (starturl)
req = urllib2.Request(starturl, headers=hdr)
startpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
for option in startpage.find_all('option'):
    if option.has_attr('value'):
        if re.search('%s Number %s' % (year, iss), option.text):
            tocurl = option['value']
            break

recs = []
if tocurl:
    print '==={ %s }===' % (tocurl)
    req = urllib2.Request(tocurl)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.find_all('div', attrs = {'id' : 'featurearticles'}):
        for a in div.find_all('a'):
            if a.has_attr('href') and re.search('Board=featurearticles', a['href']):
                rec = {'tc' : '', 'jnl' : 'AAPPS Bull.', 'note' : [], 'refs' : [],
                       'year' : year, 'issue' : iss, 'auts' : [], 'aff' : []}
                if re.search('http', a['href']):
                    rec['artlink'] = a['href']
                else:
                    rec['artlink'] = 'http://aappsbulletin.org' + a['href']
                recs.append(rec)

j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'])
        artpage = BeautifulSoup(re.sub('<metaname', '<meta name', urllib2.urlopen(req).read()), features="lxml")
        time.sleep(2)
    except:
        print 'wait 10 minutes'
        time.sleep(600)
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(re.sub('<metaname', '<meta name', urllib2.urlopen(req).read()), features="lxml")
            time.sleep(30)
        except:
            continue
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #valume
            if meta['name'] == 'citation_volume':
                rec['vol'] = re.sub('\-.*', '', meta['content'])
            #pages
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
    #DOI / references
    references = False
    for p in artpage.find_all('p', attrs = {'class' : 'references'}):
        if re.search('DOI.*10.22661', p.text) and not 'doi' in rec.keys():
            rec['doi'] = re.sub('.*(10.22661.*)', r'\1', p.text.strip())
            references = True
        elif references:
            for br in p.find_all('br'):
                br.replace_with(' XXX ')
            refs = re.sub('[\n\t\r]', '', p.text.strip())
            for ref in re.split(' XXX ', refs):
                rec['refs'].append([('x', ref)])
    if not 'doi' in rec.keys():
        for td  in artpage.find_all('td'):
            for div in td.find_all('div'):
                if re.search('DOI.*10.22661', div.text) and not 'doi' in rec.keys():
                    rec['doi'] = re.sub('.*(10.22661.*)', r'\1', div.text.strip())
                    references = True
    #author
    for p in artpage.find_all('p', attrs = {'class' : 'NAME'}):
        for br in p.find_all('br'):
            br.replace_with(' XXX ')
        for sup in p.find_all('sup'):
            newsupt = ''            
            for aff in re.split(',', sup.text.strip()):
                newsupt += ', =Aff' + aff
            sup.replace_with(newsupt)
        parts = re.split(' XXX ', re.sub('[\n\t\r]', '', p.text.strip()))
        for aut in re.split(', *', parts[0]):
            if aut:
                if re.search('@', aut):
                    aut = re.sub('^\W*', 'EMAIL:', aut)
                    rec['aff'].append(aut)
                else:
                    rec['auts'].append(aut)
        for part in parts[1:]:
            rec['aff'].append(re.sub(', =Aff(\d+)', r'Aff\1= ', part))
    #abstract
    abstract = False
    for p in artpage.find_all('p'):
        if abstract:
            rec['abs'] = p.text.strip()
            abstract = False
        elif re.search('ABSTRACT', p.text):
            abstract = True
    #File
    for td in artpage.find_all('td'):
        if re.search('File', td.text):
            for a in td.find_all('a'):
                if a.has_attr('href') and re.search('\.pdf', a['href']):
                    rec['hidden'] = 'http://aappsbulletin.org' + a['href']
    if not rec['vol']: rec['vol'] = str(int(rec['year']) - 1990)
    print '  ', rec.keys()

if tocurl:
    jnlfilename = 'aappsb%s.%s' % (rec['vol'], rec['issue'])

    #closing of files and printing
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writeXML(recs, xmlfile, publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
