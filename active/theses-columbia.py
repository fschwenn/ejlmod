# -*- coding: utf-8 -*-
#harvest theses from Columbia U. 
#FS: 2020-03-23


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Columbia U.'
jnlfilename = 'THESES-COLUMBIA-%s' % (stampoftoday)

rpp = 10
deps = ['Applied+Physics+and+Applied+Mathematics', 'Mathematics', 'Physics']

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for dep in deps:
    tocurl = 'https://academiccommons.columbia.edu/search?f%5Bdegree_grantor_ssim%5D%5B%5D=%28%22Columbia+University%22+OR+%22Teachers+College%2C+Columbia+University%22+OR+%22Union+Theological+Seminary%22+OR+%22Mailman+School+of+Public+Health%2C+Columbia+University%22%29&f%5Bdegree_level_name_ssim%5D%5B%5D=Doctoral&f%5Bdepartment_ssim%5D%5B%5D=' + dep + '&f%5Bgenre_ssim%5D%5B%5D=Theses&per_page=' + str(rpp) + '&sort=Published+Latest'
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for h3 in tocpage.body.find_all('h3', attrs = {'class' : 'index_title'}):
        for a in h3.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'supervisor' : []}
            rec['link'] = 'https://academiccommons.columbia.edu' + a['href']
            rec['note'].append(re.sub('\W', ' ', dep))
            if dep == 'Mathematics':
                rec['fc'] = 'm'
            recs.append(rec)

#check individual thesis pages
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
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
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
                rec['year'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'description':
                rec['abs'] = meta['content']
    rec['autaff'][-1].append(publisher)
    #PDF
    for li in artpage.body.find_all('li', attrs = {'class' : 'list-group-item'}):
        for span1 in li.find_all('span', attrs = {'class' : 'mimetype'}):
            if span1.text.strip() == 'application/pdf':
                for span2 in li.find_all('span', attrs = {'class' : 'download'}):
                    for a in span2.find_all('a'):
                        rec['FFT'] = 'https://academiccommons.columbia.edu' + a['href']
    #supervisor
    for dl in artpage.body.find_all('dl'):
        for child in dl.children:
            try:
                child.name
            except:
                continue
            if child.name == 'dt':
                dtt = child.text.strip()
            elif child.name == 'dd' and dtt == 'Thesis Advisors':
                rec['supervisor'].append([child.text.strip()])
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href'):
            if re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
    print '    ', rec.keys()
    
#closing of files and printing
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


