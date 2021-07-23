# -*- coding: utf-8 -*-
#harvest theses from Brwon U.
#FS: 2020-08-10


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

boringsubjects = ['Biophysics', 'Bacteriology', 'Extrasolar planets', 'ocean modeling', 'DNA', 'picosecond ultrasonics',
                  'Nanotechnology', 'Liquid crystals', 'Acoustic microscopy<', 'nanofabrication']

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Brown U.'

rpp = 2
pages = 1

jnlfilename = 'THESES-BROWN-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for page in range(pages):
    tocurl = 'https://repository.library.brown.edu/studio/collections/id_355/?selected_facets=rel_type_facet_ssim%3ADoctoral+Dissertation&page=' + str(page+1) + '&sort=date_d&per_page=' + str(rpp)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'results-normal'}):
        for div2 in div.find_all('div', attrs = {'class' : 'panel-default'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
            keepit = True
            #title
            for h4 in div2.find_all('h4'):
                rec['tit'] = h4.text.strip()
            #link
            for div3 in div2.find_all('div', attrs = {'class' : 'full-record-link'}):
                for a in div3.find_all('a'):
                    rec['artlink'] = 'https://repository.library.brown.edu' + a['href']
            for dl in div2.find_all('dl'):
                for child in dl.children:
                    try:
                        child.name
                    except:
                        continue
                    if child.name == 'dt':
                        dtt = child.text
                    elif child.name == 'dd':
                        #year
                        if dtt == 'Year:':
                            rec['year'] = child.text.strip()
                            rec['date'] = child.text.strip()
                        #contributors
                        elif dtt == 'Contributor:':
                            ddt = child.text.strip()
                            if re.search('\([Cc]reator', ddt):
                                rec['autaff'] = [[ re.sub(' *\(.*', '', child.text.strip()), publisher ]]                                
                            if re.search('\([Aa]dvisor', ddt):
                                rec['supervisor'] = [[ re.sub(' *\(.*', '', child.text.strip()) ]]
                        #Subjects
                        elif dtt == 'Subject:':
                            ddt = child.text.strip()
                            rec['note'].append(ddt)
                            if ddt in boringsubjects:
                                print '  skip', ddt
                                keepit = False
            if keepit:
                recs.append(rec)
    time.sleep(2)        


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
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
            rec['doi'] = '20.2000/BROWN/' + re.sub('\D', '', rec['artlink'])
            continue
    for dl in artpage.body.find_all('dl'):
        for child in dl.children:
            try:
                child.name
            except:
                continue
            if child.name == 'dt':
                dtt = child.text
            elif child.name == 'dd':
                #pages
                if dtt == 'Extent:':
                    ddt = child.text.strip()
                    if re.search('\d\d', ddt):
                        rec['pages'] = re.sub('\D*(\d+).*', r'\1', ddt)
                #DOI
                elif dtt == 'DOI':
                    rec['doi'] = re.sub('.*doi.org\/(.*)', r'\1', child.text.strip())
                #abstract
                elif dtt == 'Abstract:':
                    rec['abs'] = child.text.strip()
    #fulltext
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'list-inline'}):
        for li in ul.find_all('li'):
            for span in li.find_all('span'):
                if re.search('Download PDF', span.text):
                    for a in li.find_all('a'):
                        rec['hidden'] = 'https://repository.library.brown.edu' + a['href']
    #pseudDOI
    if not 'doi' in rec.keys():
        rec['link'] = rec['artlink']
        rec['doi'] = '20.2000/BROWN/' + re.sub('\D', '', rec['link'])
    print '  ', rec.keys()
                    










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
