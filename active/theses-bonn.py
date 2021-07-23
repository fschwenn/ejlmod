# -*- coding: utf-8 -*-
#harvest Uni Bonn Theses
#FS: 2020-02-19


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Bonn (main)'
hdr = {'User-Agent' : 'Magic Browser'}

year = sys.argv[1]

recs = []
jnlfilename = 'THESES-BONN-%s_%s' % (stampoftoday, year)

tocurl = 'http://hss.ulb.uni-bonn.de/fakultaet/math-nat/%s.htm' % (year)
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
time.sleep(2)
for a in tocpage.find_all('a'):
    if a.has_attr('href') and re.search('hss.ulb.uni-bonn.de\/\d', a['href']):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : a['href'], 'note' : [], 'year' : year, 'date' : year, 'date' : year}
        rec['tit'] = a.text.strip()
        #rec['doi'] = '20.2000/' + re.sub('\D', '', a['href'])
        rec['link'] = a['href']
        if not rec['link'] in ['http://hss.ulb.uni-bonn.de/2011/2478/_2478.htm', 'http://hss.ulb.uni-bonn.de/2013/3310/3310.htm',
                               'http://hss.ulb.uni-bonn.de/2016/4435/__4435.htm', 'http://hss.ulb.uni-bonn.de/2015/4196/__4196.htm',
                               'http://hss.ulb.uni-bonn.de/2016/4438/__4438.htm']:
            recs.append(rec)
            
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(10)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print 'no access to %s' % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.Creator.PersonalName':
                rec['autaff'] = [[ meta['content'] ]]
            #keywords
            elif meta['name'] == 'DC.Subject':
                if meta.has_attr('scheme') and meta['scheme'] == 'DDC-Sachgruppe':
                    rec['note'].append(meta['content'])
                else:
                    rec['keyw'] = re.split('[;,] ', meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #language
            elif meta['name'] == 'DC.Language':
                if meta['content'] != 'eng':
                    if meta['content'] == 'ger':
                        rec['language'] = 'german'
                    else:
                        rec['language'] = meta['content']
            #URN
            elif meta['name'] == 'DC.Identifier':
                if re.search('^urn', meta['content']):
                    rec['urn'] = meta['content']
            #license
            elif meta['name'] == 'DC.Rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
    for tr in artpage.body.find_all('tr'):
        for th in tr.find_all('th'):
            tht = th.text.strip()
        for td in tr.find_all('td'):
            if tht == 'Abstract':
                rec['abs'] = td.text.strip()
            if tht == 'Autor':
                rec['autaff'] = [[ td.text.strip() ]]
            for a in td.find_all('a'):
                if a.has_attr('href') and re.search('pdf$', a['href']):
                    if 'license' in rec.keys():
                        rec['FFT'] = re.sub('(.*)\/.*', r'\1/', rec['link']) + a['href']
                    else:
                        rec['hidden'] = re.sub('(.*)\/.*', r'\1/', rec['link']) + a['href']                    
    rec['autaff'][-1].append(publisher)
    print '  ', rec.keys()
                
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path,'a')
    retfiles.write(line)
    retfiles.close()


