# -*- coding: utf-8 -*-
#harvest theses from Manchester
#FS: 2020-09-24

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

publisher = 'U. Manchester (main)'

pages = 3
jnlfilename = 'THESES-MANCHESTER-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for (org, aff) in [('99043517', 'Manchester U.'), ('99043404', 'U. Manchester (main)')]:
    for page in range(pages):
        tocurl = 'https://www.research.manchester.ac.uk/portal/en/theses/search.html?lastName=&search=&organisationName=&affiliationStatus=&organisations=' + org + '&documents=&language=%20&type=%20&uri=&logicalname=ResearchInstitutes_Networks_Beacons&page=' + str(page)
        print '---{ %s }---{ %i/%i }---{ %s }---' % (org, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(2)
        for li in tocpage.body.find_all('li', attrs = {'class' : 'portal_list_item'}):
            for span in li.find_all('span', attrs = {'class' : 'type_classification'}):
                degree = span.text.strip()
                if degree in ['Master of Philosophy', 'Master of Science by Research']:
                    print '  skip "%s"' % (degree)
                else:
                    for h2 in li.find_all('h2', attrs = {'class' : 'title'}):
                        for a in h2.find_all('a'):
                            rec = {'tc' : 'T', 'note' : [degree], 'jnl' : 'BOOK', 'supervisor' : []}
                            rec['link'] = a['href']
                            rec['doi'] = '20.2000/Manchester/' + re.sub('\W', '', re.sub('.*\/', '', a['href'][-50:-4]))
                            rec['tit'] = a.text.strip()
                            rec['authoraffiliation'] = aff
                            for span2 in li.find_all('span', attrs = {'class' : 'file_attachment'}):
                                for a2 in span2.find_all('a'):
                                    rec['hidden'] = a2['href']
                            recs.append(rec)
                            
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'persons'}):
        #print ul.text
        #author
        if re.search('Authors:', ul.text):
            for li in ul.find_all('li'):
                rec['autaff'] = [[ li.text.strip(), rec['authoraffiliation'] ]]        
        #supervisor
        else:
            for li in ul.find_all('li'):
                if re.search('Supervisor', li.text):
                    for span in li.find_all('span'):
                        rec['supervisor'].append([span.text.strip()])
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'textblock'}):
        rec['abs'] = div.text.strip()
    #date
    for span in artpage.body.find_all('span', attrs = {'class' : 'date'}):
        rec['date'] = span.text.strip()
        rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])
    print'  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
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

    
