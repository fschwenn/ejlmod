# -*- coding: utf-8 -*-
#harvest theses from Buenos Aires
#FS: 2022-05-16

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Buenos Aires'
jnlfilename = 'THESES-BuenosAiresU-%s' % (stampoftoday)

years = 2

hdr = {'User-Agent' : 'Magic Browser'}

recs = []
artlinks = []
for (fc, dep, aff) in [('c', '5', 'U. Buenos Aires'), ('m', '11', 'U. Buenos Aires'), ('', '8', 'Buenos Aires U.')]:
    starturl = 'https://bibliotecadigital.exactas.uba.ar/collection/tesis/browse/CL5/' + dep
    print '==={ %s }===' % (starturl)
    req = urllib2.Request(starturl, headers=hdr)
    startpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in startpage.body.find_all('div', attrs = {'class' : 'flex-row'}):
        for span in div.find_all('span'):
            spant = span.text.strip()
            if re.search('^\d+$', spant):
                if int(spant) > now.year - years:
                    for a in div.find_all('a'):
                        tocurl = 'https://bibliotecadigital.exactas.uba.ar' + a['href']
                        print ' =={ %s }==={ %s }===' % (spant, tocurl)
                        req = urllib2.Request(tocurl, headers=hdr)
                        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
                        for div2 in tocpage.body.find_all('div', attrs = {'class' : 'childrenlist'}):
                            for a2 in div2.find_all('a')[1:]:
                                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
                                rec['link'] = 'https://bibliotecadigital.exactas.uba.ar' + a2['href']
                                rec['affiliation'] = aff
                                rec['date'] = spant
                                if fc: rec['fc'] = fc
                                if not rec['link'] in artlinks:
                                    recs.append(rec)
                                    artlinks.append(rec['link'])
                        time.sleep(10)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'], rec['affiliation'] ]]
                #title
                elif meta['name'] == 'citation_title':
                    if meta.has_attr('lang'):
                        if meta['lang'] == 'en':
                            rec['titen'] = meta['content']
                        elif meta['lang'] == 'es':
                            rec['tites'] = meta['content']
                        else:
                            rec['tit'] = meta['content']
                #language
                elif meta['name'] == 'citation_language':
                    if meta['content'] == u'Español':
                        rec['language'] = 'Spanish'
                #keywords
                elif meta['name'] == 'citation_keywords':
                    for keyw in re.split(' *; *', meta['content']):
                        if not keyw in rec['keyw']:
                            rec['keyw'].append(keyw)
                #abstract
                elif meta['name'] == 'citation_abstract':
                    if meta.has_attr('lang' ):
                        if meta['lang'] == 'es':
                            rec['abses'] = meta['content']
                        else:
                            rec['abs'] = meta['content']
                    else:
                        if re.search(' the ', meta['content']):
                            rec['abs'] = meta['content']
                        else:
                            rec['abses'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['citation_pdf_url'] = meta['content']
                #Rights
                elif meta['name'] == 'DC.rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['license'] = {'url' : meta['content']}
    for table in artpage.find_all('table'):
        profdict = {}
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) == 2:
                tht = tds[0].text.strip()
                #supervisor
                if tht in ['Director:']:
                    rec['supervisor'].append([tds[1].text.strip()])
                #handle
                elif tht == 'Handle:':
                    rec['hdl'] = re.sub('.*ndle.net\/', '', tds[1].text.strip())
    #title
    if 'language' in rec.keys():
        if 'tites' in rec.keys():
            rec['tit'] = rec['tites']
            if 'titen' in rec.keys():
                rec['transtit'] = rec['titen']
        elif 'titen' in rec.keys():
            rec['tit'] = rec['titen']
    else:
        if 'titen' in rec.keys():
            rec['tit'] = rec['titen']
            if 'tites' in rec.keys():
                rec['transtit'] = rec['tites']            
    #abstract
    if not 'abs' in rec.keys() and 'abses' in rec.keys():
        rec['abs'] = rec['abses']
    #fulltext
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    print '  ', rec.keys()    
    if not 'hdl' in rec.keys():
        rec['doi'] = '20.2000/BuenosAires/' + re.sub('.*\/', '', rec['link'])


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
