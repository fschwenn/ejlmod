# -*- coding: utf-8 -*-
#harvest Stanford U.
#FS: 2020-02-20


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

publisher = 'Stanford U.'
hdr = {'User-Agent' : 'Magic Browser'}

pages = 1
recordsperpage = 50

recs = []
jnlfilename = 'THESES-STANFORD-%s' % (stampoftoday)
for page in range(pages):
    tocurl = 'https://searchworks.stanford.edu/?f[genre_ssim][]=Thesis%2FDissertation&f[stanford_dept_sim][]=Department+of+Physics&page=' + str(page) + '&per_page=' + str(recordsperpage)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for div in tocpage.find_all('div', attrs = {'class' : 'document'}):
        for h3 in div.find_all('h3'):
            for a in h3.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'artlink' : 'https://searchworks.stanford.edu' + a['href'], 'note' : []}
                rec['tit'] = re.sub(' \[electronic resource\]', '', a.text.strip()                )
                rec['doi'] = '20.2000/Stanford/' + re.sub('\D', '', a['href'])
            for span in h3.find_all('span', attrs = {'class' : 'main-title-date'}):
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                rec['date'] = rec['year']
            for a in div.find_all('a'):
                if a.has_attr('href') and re.search('purl.stanford', a['href']):
                    rec['link'] = a['href']
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(5)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print 'no access to %s' % (rec['artlink'])
            continue
    #author and supervisor
    for div in artpage.body.find_all('div', attrs = {'id' : 'contributors'}):
        for dd in div.find_all('dd'):
            for a in dd.find_all('a'):
                person = re.sub(' *,$', '', a.text.strip())
                person = re.sub(', [12]\d.*', '', person) 
                person = re.sub(' \(.*', '', person) 
                #a.replace_with('')
            if re.search('author', dd.text):
                rec['autaff'] = [[ person ]]
            elif re.search('upervisor', dd.text):
                rec['supervisor'] = [[ person ]]
    #author2
    if not 'autaff' in rec.keys():
        for div in artpage.body.find_all('div', attrs = {'id' : 'contributors'}):
            for dl in div.find_all('dl'):
                for child in dl.children:
                    try:
                        child.name
                    except:
                        continue
                    if child.name == 'dt':
                        dtt = child.text
                    elif child.name == 'dd':
                        ddt = re.sub('([a-z][a-z])\.', r'\1', child.text.strip())
                        ddt = re.sub('[\n\t\r]', '', ddt)
                        if ddt:
                            if re.search('[aA]uthor', dtt):
                                rec['autaff'] = [[ ddt ]]
                            elif re.search('[sS]upervisor', dtt) or re.search('rimary [Aa]dvisor', dtt):
                                rec['supervisor'] = [[ ddt ]]
    print rec['autaff']
    #abstract
    for div in artpage.body.find_all('div', attrs = {'id' : 'contents-summary'}):
        for dd in div.find_all('dd'):
            rec['abs'] = dd.text.strip()
    #purl
    if 'link' in rec.keys():
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        #license
        for div in artpage.body.find_all('div', attrs = {'id' : 'access-conditions'}):
            for a in div.find_all('a'):
                if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                    rec['license'] = {'url' : a['href']}
    else:
        rec['link'] = rec['artlink']
    
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


