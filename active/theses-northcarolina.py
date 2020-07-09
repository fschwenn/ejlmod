# -*- coding: utf-8 -*-
#harvest theses from UNC, Chapel Hill
#FS: 2020-07-07

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
irrelevantsubjects = []

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'UNC, Chapel Hill'
rpp = 50
startyear = now.year - 1
stopyear = now.year + 1
departments = [('Department+of+Physics+and+Astronomy', 'North Carolina U.', 'PHYSICS'),
               ('Department+of+Mathematics', 'North Carolina U., Math. Dept.', 'MATHEMATICS')]
urltrunc = 'https://cdr.lib.unc.edu'
hdr = {'User-Agent' : 'Magic Browser'}

for (affurl, aff, affname) in departments:
    recs = []
    jnlfilename = 'THESES-UNC-%s-%s' % (stampoftoday, affname)
    tocurl = urltrunc + '/catalog?f[affiliation_label_sim][]=' + affurl + '&f[resource_type_sim][]=Dissertation&locale=en&per_page=' + str(rpp) + '&range[date_issued_isim][begin]=' + str(startyear) + '&range[date_issued_isim][end]=' + str(stopyear) + '&search_field=dummy_range&sort=date_issued_sort_dtsi+desc&view=list'
    print '---{ %s }---{ %s }------' % (affname, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for li in tocpage.body.find_all('li', attrs = {'class' : 'document'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
        for h4 in li.find_all('h4', attrs = {'class' : 'search-result-title'}):
            for a in h4.find_all('a'):
                rec['artlink'] = urltrunc + a['href']
                rec['tit'] = a.text.strip()
        for dd in li.find_all('dd'):
            ddt = dd.text.strip()
            if re.search('^[12]\d\d\d', ddt):
                rec['date'] = ddt
                rec['year'] = re.sub('.*(\d\d\d\d).*', r'\1', ddt)
        recs.append(rec)
    time.sleep(10)

    j = 0
    for rec in recs:
        j += 1
        print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['artlink'])
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
            time.sleep(7)
        except:
            print 'wait 10 minutes'
            time.sleep(600)
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'], aff]]
                #PDF
                elif meta['name'] == 'citation_pdf_url':
                    rec['pdf_url'] = meta['content']
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
        for dl in artpage.find_all('dl', attrs = {'class' : 'dissertation'}):
            for child in dl.children:
                try:
                    dn = child.name
                except:
                    dn = ''
                    dt = ''
                if dn == 'dt':
                    dt = child.text.strip()
                elif dn == 'dd':
                    #abstract
                    if dt == 'Abstract':
                        rec['abs'] = child.text.strip()
                    #DOI
                    elif dt == 'DOI':
                        rec['doi'] = re.sub('.*?(10.176.*)', r'\1', child.text.strip())
                    #Rights statement
                    elif dt == 'Rights statement':
                        rec['note'].append(child.text.strip())
                    #supervisor
                    elif dt == 'Advisor':
                        rec['supervisor'] = []
                        for li in child.find_all('li'):
                            rec['supervisor'].append([li.text.strip()])
                        if not rec['supervisor']:
                            rec['supervisor'].append([child.text.strip()])
                    #keywords
                    elif dt == 'Keyword':
                        rec['keyw'] = []
                        for li in child.find_all('li'):
                            rec['keyw'].append(li.text.strip())
                    #date
                    elif dt == 'Date of publication':
                        rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', child.text.strip())
                    #
                    elif dt == '':
                        rec[''] = child.text.strip()

        
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
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons', a['href']):
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

