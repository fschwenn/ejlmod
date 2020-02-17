# -*- coding: utf-8 -*-
#harvest theses from McGill U.
#FS: 2020-02-07

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
irrelevantsubjects = []

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'McGill U., Montreal (main)'
articlesperpage = 20
pages = 1
departments = [('Department+of+Physics', 'McGill U.', 'PHYSICS'),
               ('Department+of+Mathematics+and+Statistics', 'McGill U., Math. Stat.', 'MATHEMATICS')]
urltrunc = 'https://escholarship-test.mcgill.ca'

hdr = {'User-Agent' : 'Magic Browser'}

for (affurl, aff, affname) in departments:
    recs = []
    jnlfilename = 'THESES-MCGILL-%s-%s' % (stampoftoday, affname)
    for page in range(pages):
        tocurl = urltrunc + '/catalog?f%5Bdegree_sim%5D%5B%5D=Doctor+of+Philosophy&f%5Bdepartment_sim%5D%5B%5D=' + affurl + '&f%5Brtype_sim%5D%5B%5D=Thesis&locale=en&page=' + str(page+1) + '&per_page=' + str(articlesperpage) + '&sort=system_create_dtsi+desc'
        print '---{ %s }---{ %i/%i }---{ %s }------' % (affname, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for li in tocpage.body.find_all('li', attrs = {'class' : 'document'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK'}
            for h4 in li.find_all('h4', attrs = {'class' : 'search-result-title'}):
                for a in h4.find_all('a'):
                    rec['artlink'] = urltrunc + a['href']
                    rec['tit'] = a.text.strip()
            for dd in li.find_all('dd'):
                ddt = dd.text.strip()
                if re.search('^[12]\d\d\d', ddt):
                    rec['date'] = ddt
                    rec['year'] = re.sub('.*(\d\d\d\d).*', r'\1', ddt)
                    if int(rec['year']) > now.year - 15:
                        recs.append(rec)
        print '   %i theses so far' % (len(recs))
        time.sleep(5)

    j = 0
    for rec in recs:
        j += 1
        print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['artlink'])
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req))
            time.sleep(20)
        except:
            print 'wait 10 minutes'
            time.sleep(600)
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req))
            time.sleep(30)
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'], aff]]
                #PDF
                elif meta['name'] == 'citation_pdf_url':
                    rec['pdf_url'] = meta['content']
        #supervisor
        for dd in artpage.body.find_all('dd', attrs = {'class' : 'custom-dd-contributor'}):
            rec['supervisor'] = []
            for a in dd.find_all('a'):
                at = a.text.strip()
                if re.search('Supervisor', at):
                    rec['supervisor'].append([re.sub(' *\(.*', '', at)])
        #abstract
        for dd in artpage.body.find_all('dd', attrs = {'class' : 'custom-dd-abstract'}):
            for div in dd.find_all('div', attrs = {'class' : 'panel'}):
                for h5 in div.find_all('h5'):
                    if re.search('English', h5.text):
                        h5.replace_with('')
                        rec['abs'] = div.text.strip()
        #link
        for dd in artpage.body.find_all('dd', attrs = {'class' : 'custom-dd-identifier'}):
            for a in dd.find_all('a'):
                rec['link'] = a['href']
                rec['doi'] = '20.2000/McGill/' + re.sub('.*\/(.+)', r'\1', a['href'])
        #license
        for dd in artpage.body.find_all('dd', attrs = {'class' : 'custom-dd-rights'}):
            for a in dd.find_all('a'):
                if re.search('creativecommons', a['href']):
                    rec['license'] = {'url' : a['href']}
        #PDF
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
        print '  ', rec.keys()

    #closing of files and printing
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writeXML(recs,xmlfile,publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()

