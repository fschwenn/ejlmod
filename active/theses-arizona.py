# -*- coding: utf-8 -*-
#harvest theses from Arizona State U., Tempe 
#FS: 2019-12-12


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

publisher = 'Arizona State U., Tempe'

rpp = 20

hdr = {'User-Agent' : 'Magic Browser'}
for department in ['Physics', 'Mathematics', 'Astrophysics']:
    tocurl = 'https://repository.asu.edu/collections/7?sub=' + department + '&sort=md_created_sort+desc&page=&per_page=' + str(rpp)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    recs = []
    prerecs = []
    divs = tocpage.body.find_all('div', attrs = {'class' : 'result-description'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://repository.asu.edu' + a['href'] #+ '?show=full'
            rec['tit'] = a.text.strip()
            if department == 'Mathematics':
                rec['fc'] = 'm'
            elif department == 'Astrophysics':
                rec['fc'] = 'a'
            prerecs.append(rec)
    time.sleep(30)

    i = 0
    for rec in prerecs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (department, i, len(prerecs), rec['artlink'])
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
                #pages
                if meta['name'] == 'DCTERMS.extent':
                    if re.search('\d+ pages', meta['content']):
                        rec['pages'] = re.sub('\D*(\d+) page.*', r'\1', meta['content'])
                #date
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    rec['abs'] = meta['content']
                #handle
                elif meta['name'] == 'DC.identifier':
                    if re.search('^hdl:', meta['content']):                
                        rec['hdl'] = re.sub('^hdl:', '', meta['content'])
                #pdf
                elif meta['name'] == 'citation_pdf_url':
                    rec['citation_pdf_url'] = 'https://repository.asu.edu' + meta['content']
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                if 'citation_pdf_url' in rec.keys():
                    rec['FFT'] = rec['citation_pdf_url']
        #hiddenPDF
        if not 'license' in rec.keys() and 'citation_pdf_url' in rec.keys():
            rec['hidden'] = rec['citation_pdf_url']
        #pseudo doi needed?
        if not 'hdl' in rec.keys():
            rec['doi'] = '20.2000/ARIZONA_STATE/' + re.sub('\W', '', rec['artlink'][10:])
            rec['link'] = rec['artlink']
                        
        for tr in artpage.body.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                if tht == 'Contributor':
                    for span in td.find_all('span'):
                        spant = re.split(' *\(', span.text.strip())
                        if len(spant) == 2:
                            #author
                            if re.search('Author', spant[1]):
                                rec['autaff'] = [[ spant[0], publisher ]]
                            #supervisor
                            elif re.search('Advisor', spant[1]):
                                rec['supervisor'].append([ spant[0], publisher ])
                #keywords
                elif tht == 'Subject':
                    for span in td.find_all('span'):
                        rec['keyw'].append(span.text.strip())
                #language
                elif tht == 'Language':
                    for a in td.find_all('a'):
                        if a.text.strip() != 'English':
                            rec['language'] = a.text.strip()
                #Reuse Permissions
                elif tht == 'Reuse Permissions':
                    print td.text.strip()
                #thesis type
                elif tht == 'Note':
                    rec['note'] = [ td.text.strip() ]
                    if not re.search('Master', td.text.strip()):
                        recs.append(rec)
        print '  ', rec.keys()
    jnlfilename = 'THESES-ARIZONA_STATE-%s_%s' % (stampoftoday, re.sub('\W', '', department))


    #closing of files and printing
    xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
