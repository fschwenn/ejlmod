# -*- coding: utf-8 -*-
#harvest theses from Colorado U.
#FS: 2021-04-16

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

publisher = 'U. Colorado, Boulder'
rpp = 10
departments = [('Physics', 'Colorado U.', 'PHYSICS', 2),
               ('Mathematics', 'U. Colorado, Boulder', 'MATHEMATICS', 1)]
urltrunc = 'https://scholar.colorado.edu'
hdr = {'User-Agent' : 'Magic Browser'}

for (affurl, aff, affname, pages) in departments:    
    jnlfilename = 'THESES-COLORADO-%s-%s' % (stampoftoday, affname)
    recs = []
    for page in range(pages):
        tocurl = urltrunc + '/catalog?f%5Bacademic_affiliation_sim%5D%5B%5D=' + affurl + '&f%5Bresource_type_sim%5D%5B%5D=Dissertation&locale=en&per_page=' + str(rpp) + '&sort=system_create_dtsi+desc&page=' + str(page+1)
        print '---{ %s %i/%i }---{ %s }------' % (affname, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for li in tocpage.body.find_all('li', attrs = {'class' : 'document'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [affname]}
            for h4 in li.find_all('h4', attrs = {'class' : 'search-result-title'}):
                for a in h4.find_all('a'):
                    rec['link'] = urltrunc + a['href']
                    rec['doi'] = '20.2000/ColoradoU/' + re.sub('.*\/', '', a['href'])
                    rec['tit'] = a.text.strip()
            if not rec['doi'] in ['20.2000/ColoradoU/6m311p316', '20.2000/ColoradoU/5138jd902']:                
                recs.append(rec)
    time.sleep(10)

    j = 0
    for rec in recs:
        j += 1
        print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['link'])
        try:
            req = urllib2.Request(rec['link'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
            time.sleep(7)
        except:
            print 'wait 10 minutes'
            time.sleep(600)
            req = urllib2.Request(rec['link'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'], aff]]
                #PDF
                elif meta['name'] == 'citation_pdf_url':
                    if meta['content']:
                        rec['pdf_url'] = meta['content']
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
        for dl in artpage.find_all('dl'):
            for child in dl.children:
                try:
                    dn = child.name
                except:
                    dn = ''
                if dn == 'dt':
                    dt = child.text.strip()
                elif dn == 'dd':
                    #abstract
                    if dt == 'Abstract':
                        rec['abs'] = child.text.strip()
                    #date
                    elif dt == 'Date Issued':
                        rec['date'] = child.text.strip()
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
                    elif dt in ['Keyword', 'Subject']:
                        rec['keyw'] = []
                        for li in child.find_all('li'):
                            rec['keyw'].append(li.text.strip())
                    #date
                    elif dt == 'Date of publication':
                        rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', child.text.strip())
                    dt = ''
        #FFT
        if not 'pdf_url' in rec.keys():
            for a in artpage.find_all('a', attrs = {'title' : 'Download'}):
                rec['pdf_url'] = a['href']

        
        
        #supervisor
        #for dd in artpage.body.find_all('dd', attrs = {'class' : 'custom-dd-contributor'}):
        #    rec['supervisor'] = []
        #    for a in dd.find_all('a'):
        #        at = a.text.strip()
        #        if re.search('Supervisor', at):
        #            rec['supervisor'].append([re.sub(' *\(.*', '', at)])
        #abstract
        #for dd in artpage.body.find_all('dd', attrs = {'class' : 'custom-dd-abstract'}):
        #    for div in dd.find_all('div', attrs = {'class' : 'panel'}):
        #        for h5 in div.find_all('h5'):
        #            if re.search('English', h5.text):
        #                h5.replace_with('')
        #                rec['abs'] = div.text.strip()
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons', a['href']):
                rec['license'] = {'url' : urltrunc + a['href']}
        #PDF
        if 'pdf_url' in rec.keys():
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



    pages = 2
