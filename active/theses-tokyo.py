# -*- coding: utf-8 -*-
#harvest theses (with english titles) from Tokyo U.
#FS: 2020-06-22

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

publisher = 'Tokyo U. '

jnlfilename = 'THESES-TOKYO_U-%s' % (stampoftoday)

rpp = 100
pages = 3

hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for page in range(pages):
    tocurl = 'https://repository.dl.itc.u-tokyo.ac.jp/index.php?action=pages_view_main&active_action=repository_view_main_item_snippet&index_id=280&pn=' + str(page+1) + '&count=' + str(rpp) + '&order=16&lang=english&page_id=41&block_id=85'
    print '==={ %s/%s }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'item_title'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK'}
        for a in div.find_all('a'):
            at = a.text.strip()
            if re.search('[a-zA-Z]+ [a-zA-Z]+', at):
                rec['artlink'] = a['href'] + '&lang=english'
                rec['tit'] = at
                recs.append(rec)
            else:
                print '  skip completely Japanese title'
    time.sleep(5)

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
            continue
    #FFT
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
        rec['FFT'] = meta['content']
    for table in artpage.body.find_all('table', attrs = {'class' : 'full'}):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = re.sub('[\n\t\r]', '', th.text.strip())
                for td in tr.find_all('td'):
                    tdt = re.sub('[\n\t\r]', '', td.text.strip()).strip()
                    #DOI
                    if re.search('DOI', tht):
                        rec['doi'] = re.sub('.*?(10.15083.*)', r'\1', tdt)
                        rec['doi'] = re.sub('info.doi\/', '', rec['doi'])
                    #author
                    elif re.search('reator', tht):
                        if  re.search('[a-zA-Z]+', tdt):
                            author = re.sub('(.*) (.*)', r'\1, \2', tdt)
                            rec['autaff'] = [[ author, publisher ]]
                    #date
                    elif re.search('Date', tht):
                        rec['date'] = tdt
    #DOI?
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/TOKYO/' + re.sub('.*item_id=(\d+).*', r'\1', rec['artlink'])
        rec['link'] = rec['artlink']
    print '   ', rec.keys()

    if i % 100 == 0:
        jnlfilename = 'THESES-TOKYO_U-%s_%03i' % (stampoftoday, i/100)
    
        #closing of files and printing
        xmlf = os.path.join(xmldir, jnlfilename+'.xml')
        xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
        ejlmod2.writeXML(recs[i-100:i], xmlfile, publisher)
        xmlfile.close()
        #retrival
        retfiles_text = open(retfiles_path, "r").read()
        line = jnlfilename+'.xml'+ "\n"
        if not line in retfiles_text:
            retfiles = open(retfiles_path,"a")
            retfiles.write(line)
            retfiles.close()
