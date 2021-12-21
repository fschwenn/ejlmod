# -*- coding: utf-8 -*-
#harvest theses from Porot
#FS: 2021-02-24

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
import json
import unicodedata

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Porto U.'
jnlfilename = 'THESES-PORTO-%s' % (stampoftoday)

rpp = 20
pages = 2

boringdeps = ['Quimica', 'Biological sciences', 'Ciencias biologicas', 'Ciencias da educacao',
              'Educational sciences',
              #'Computer and information sciences',
              'Ciencias da terra e ciencias do ambiente', 'Earth and related Environmental sciences']

def akzenteabstreifen(string):
    if not type(string) == type(u'unicode'):
        string = unicode(string,'utf-8', errors='ignore')
        if not type(string) == type(u'unicode'):
            return string
        else:
            return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')
    else:
        return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')


hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://repositorio-aberto.up.pt/handle/10216/9537/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(rpp*(page+2)) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'headers' : 't2'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'note' : [], 'oa' : False}
            for a in td.find_all('a'):
                rec['artlink'] = 'https://repositorio-aberto.up.pt' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '',  a['href'])
                prerecs.append(rec)
    time.sleep(7)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue

    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                else:
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'].append([ author ])
            #rights
            elif meta['name'] == 'DC.rights':
                if meta['content'] == 'openAccess':
                    rec['oa'] = True
                else:
                    rec['note'].append(meta['content'])
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'por':
                    rec['language'] = 'Portuguese'
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #department
            elif meta['name'] == 'DC.subject':
                dep = akzenteabstreifen(meta['content'])
                if dep in boringdeps:
                    print  '   skip', dep
                    keepit = False
                    continue
                else:
                    rec['note'].append(dep)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    if len(rec['autaff']) == 1:
        rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            rec['oa'] = True
    if 'pdf_url' in rec.keys():
        if rec['oa']:
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    if keepit:
        print '  ', rec.keys()
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
