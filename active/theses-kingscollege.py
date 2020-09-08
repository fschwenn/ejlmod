# -*- coding: utf-8 -*-
#harvest theses from King's Coll. London 
#FS: 2020-08-31

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

publisher = "King's Coll. London"

jnlfilename = 'THESES-KINGS_COLLEGE-%s' % (stampoftoday)

rpp = 50
pages = 1
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
#first get links of year pages
for page in range(pages):
    tocurl = 'https://kclpure.kcl.ac.uk/portal/en/theses/search.html?search=theses&ordering=studentThesisOrderByAwardYear&pageSize=' + str(rpp) + '&page=' + str(page) + '&type=%2Fdk%2Fatira%2Fpure%2Fstudentthesis%2Fstudentthesistypes%2Fstudentthesis%2Fdoc%2Fdsc&type=%2Fdk%2Fatira%2Fpure%2Fstudentthesis%2Fstudentthesistypes%2Fstudentthesis%2Fdoc%2Fphd&descending=true'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    year = False
    for ol in tocpage.body.find_all('ol', attrs = {'class' : 'portal_list'}):
        for li in ol.find_all('li'):
            if li.has_attr('class'):
                if 'portal_list_item_group' in li['class']:
                    year = li.text.strip()
                elif 'portal_list_item' in li['class']:
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'supervisor' : []}
                    for h2 in li.find_all('h2'):
                        for a in h2.find_all('a'):
                            rec['link'] = a['href']
                            rec['tit'] = a.text.strip()
                            rec['year'] = year
                            rec['date'] = year
                            rec['doi'] = '20.2000/KINGsCOLLEGE/' + re.sub('.*\/(.*).html', r'\1', a['href'])[-60:]
                    recs.append(rec)
    time.sleep(5)


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
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for tr in artpage.body.find_all('tr'):
        for th in tr.find_all('th'):
            tht = th.text.strip()
        for td in tr.find_all('td'):
            #supervisor
            if tht == 'Supervisors/Advisors':
                for span in td.find_all('span'):
                    rec['supervisor'].append([span.text.strip()])
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'textblock'}):
        rec['abs'] = div.text.strip()
    #author
    for p in artpage.body.find_all('p', attrs = {'class' : 'persons'}):
        rec['autaff'] = [[ p.text.strip(), publisher ]]
    #FFT
    for li in artpage.body.find_all('li', attrs = {'class' : 'available'}):
        for a in li.find_all('a'):
            rec['hidden'] = a['href']
    print '     ', rec.keys()
    
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
    
