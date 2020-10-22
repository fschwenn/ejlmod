# -*- coding: utf-8 -*-
#harvest theses (with english titles) from Osaka U.
#FS: 2020-08-31

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Osaka U. '

jnlfilename = 'THESES-OSAKA_U-%s' % (stampoftoday)

rpp = 200
pages = 2
hdr = {'User-Agent' : 'Magic Browser'}

#first get links of year pages
masterurl = 'https://ir.library.osaka-u.ac.jp/repo/ouka/thesis/?lang=1'
req = urllib2.Request(masterurl, headers=hdr)
masterpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
tocurls = {}
for div in masterpage.body.find_all('div', attrs = {'class' : 'menu_none'}):
    for a in div.find_all('a'):
        parts = re.split(' \/ ', a.text.strip())
        if len(parts) == 3:
            tocurl = 'https://ir.library.osaka-u.ac.jp/repo/ouka/thesis' + a['href'][1:] + '&disp_cnt=' + str(rpp)
            if parts[1] in tocurls.keys():
                if parts[2] in tocurls[parts[1]].keys():
                    if not tocurl in tocurls[parts[1]][parts[2]]:
                        tocurls[parts[1]][parts[2]].append(tocurl)
                else:
                    tocurls[parts[1]][parts[2]] = [tocurl]
            else:
                tocurls[parts[1]] = {parts[2] : [tocurl]}
time.sleep(1)

#check indiviual TOC for each year
recs = []
artlinks = []
for dep in ['Graduate School of Science']:
    for year in [str(now.year), str(now.year-1)]:
        if dep in tocurls.keys():
            if year in tocurls[dep].keys():
                for tocurl in tocurls[dep][year]:
                    print '==={ %s }==={ %s }==={ %s }===' % (dep, year, tocurl)
                    req = urllib2.Request(tocurl, headers=hdr)
                    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
                    for table in tocpage.body.find_all('table', attrs = {'class' : 'slist'}):
                        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
                        for span in table.find_all('span', attrs = {'class' : 'tit_name'}):
                            for a in span.find_all('a'):
                                rec['artlink'] = re.sub('.*\/all\/(.*)\/.*', r'https://ir.library.osaka-u.ac.jp/repo/ouka/all/\1/?lang=1', a['href'])
                                if not rec['artlink'] in artlinks:
                                    rec['tit'] = a
                                    recs.append(rec)
                                    artlinks.append(rec['artlink'])
                    print '    %i records so far' % (len(recs))
                    time.sleep(5)


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
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
            #language
            if meta['name'] == 'DC.language':
                if meta['content'] != 'English':
                    rec['language'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = re.sub('.*?(10.*)', r'\1', meta['content'])
            #HDL
            elif meta['name'] == 'DC.identifier':
                if re.search('hdl.handle.net', meta['content']):
                    rec['hdl'] = re.sub('.*hdl.handle.net\/', '', meta['content'])
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
    #FFT
    for table in tocpage.body.find_all('table', attrs = {'class' : 'detailURL'}):
        for tr in table.find_all('tr'):
            for td in tr.find_all('td', attrs = {'class' : 'flintro'}):
                if re.search('Dissertation', td.text):
                    for td2 in tr.find_all('td', attrs = {'class' : 'filenm'}):
                        for a in td2.find_all('a'):
                            rec['hidden'] = re.sub('(.*)\/.*', r'\1', rec['artlink']) + a['href'][2:]
    rec['autaff'][-1].append(publisher)
    print rec.keys()
    
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
    
