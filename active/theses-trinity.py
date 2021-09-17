# -*- coding: utf-8 -*-
#harvest theses from TCD, Dublin 
#FS: 2020-09-02

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
years = [now.year-1, now.year]
rpp = 50
pages = 20
numberofrecords = rpp*pages

publisher = 'TCD, Dublin'


boringschools = ['Biochemistry & Immunology', 'Business', 'Chemistry',
                 'Computer Science & Statistics', 'Creative Arts', 'Dental Sciences',
                 'Ecumenics', 'Education', 'Engineering', 'English',
                 'Histories & Humanities', 'Lang, Lit', 'Law',
                 'Linguistic Speech & Comm Sci', 'Medicine', 'Natural Sciences',
                 'Nursing & Midwifery', 'Pharmacy & Pharma', 'Psychology',
                 'Social Sciences & Philosophy', 'Social Work & Social Policy']

hdls = []
for year in years:
    prerecs = []
    jnlfilename = 'THESES-TrinityCollegeDublin-%s_%i' % (stampoftoday, year)
    for section in ['76240', '221', '171']:
        realpages = pages
        for page in range(pages):
            if page*rpp < numberofrecords:
                tocurl = 'http://www.tara.tcd.ie/handle/2262/' + section + '/discover?rpp=' + str(rpp) + '&page=' + str(page+1) + '&group_by=none&etal=0&filtertype_0=dateIssued&filtertype_1=type&filter_0=[' + str(year) + '+TO+' + str(year) + ']&filter_relational_operator_1=equals&filter_1=Thesis&filter_relational_operator_0=equals'
                print '==={ %i }==={ %s }==={ %i/%i }===' % (year, section, page+1, realpages)
                try:
                    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
                    time.sleep(3)
                except:
                    print "retry %s in 180 seconds" % (tocurl)
                    time.sleep(180)
                    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
                if page == 0:
                    for p in tocpage.body.find_all('p', attrs = {'class' : 'pagination-info'}):
                        if re.search('\d of \d+', p.text):
                            numberofrecords = int(re.sub('.*of (\d+).*', r'\1', p.text.strip()))
                            print '  %i theses in query' % (numberofrecords)
                            realpages = (numberofrecords-1) / rpp + 1
                for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
                    for a in div.find_all('a'):
                        for h4 in a.find_all('h4'):
                            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'keyw' : [], 'note' : []}
                            rec['tit'] = a.text.strip()
                            rec['artlink'] = 'http://www.tara.tcd.ie' + a['href'] + '?show=full'
                            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                            if rec['hdl'] in hdls or rec['hdl'] in ['2262/82940']:
                                print '  HDL:%s already from other collection' % (rec['hdl'])
                            else:
                                prerecs.append(rec)
                                hdls.append(rec['hdl'])
    
    i = 0
    recs = []
    for rec in prerecs:
        keepit = True
        i += 1
        print '---{ %i }---{ %i/%i (%i) }---{ %s }------' % (year, i, len(prerecs), len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                if meta['name'] == 'citation_authors':
                    rec['autaff'] = [[ meta['content'], publisher ]]
                elif meta['name'] == 'DCTERMS.issued':
                    rec['date'] = meta['content']
                elif meta['name'] == 'DCTERMS.abstract':
                    rec['abs'] = meta['content']
                elif meta['name'] == 'DC.subject':
                    rec['keyw'] += re.split(', ', meta['content'])
                #elif meta['name'] == 'DC.contributor':
                #    rec['supervisor'].append([meta['content']])
                elif meta['name'] == 'DC.publisher':
                    if re.search('School of', meta['content']):
                        rec['school'] = re.sub('.*School of (.*?)\..*', r'\1', meta['content'])
                    else:
                        rec['note'].append(meta['content'])
        if 'school' in rec.keys():
            if rec['school'] == 'Mathematics':
                rec['autaff'][-1].append('Trinity Coll., Dublin')
                rec['fc'] = 'm'
            elif rec['school'] in boringschools:
                print '   skip School of %s' % (rec['school'])
                keepit = False
        #license
        for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
            if re.search('creativecommons.or', a['href']):
                rec['license'] = {'url' : a['href']}
        #fulltext
        for div in artpage.body.find_all('div', attrs = {'class' : 'simple-item-view-download'}):
            for a in div.find_all('a'):
                if 'license' in rec.keys():
                    rec['FFT'] = a['href']
                else:
                    rec['hidden'] = a['href']
        #supervisor
        for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
            tdt = ''
            for td in tr.find_all('td'):
                if td.has_attr('label-cell'):
                    tdt = td.text.strip()
                else:
                    if tdt == 'dc.contributor.advisor':
                        rec['supervisor'].append(td.text.strip())
                    
        if keepit:
            recs.append(rec)
    if recs:
        #closing of files and printing
        xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
                    
