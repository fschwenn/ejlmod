# -*- coding: utf-8 -*-
#harvest Hong Kong U. Sci. Tech. theses
#FS: 2021-12-21

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
from inspire_utils.date import normalize_date

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Hong Kong U. Sci. Tech.'

pages = 1

jnlfilename = 'THESES-HongKongUSciTech-%s' % (stampoftoday)

recs = []
for (dep, fc) in [('Computer+Science', 'c'), ('Physics', ''), ('Mathematics', 'm')]:
    for i in range(pages):
        tocurl = 'http://lbezone.ust.hk/rse/?paged=' + str(i+1) + '&s=%2A&sort=pubyear&order=desc&fq=degree_cc_Ph.D._ss_department_cc_' + dep + '&scopename=electronic-theses&show_result_ui=list'
        print '==={ %s %i/%i }==={ %s }===' % (dep, i+1, pages, tocurl)
        try:
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (tocurl)
            time.sleep(180)
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        for li in tocpage.body.find_all('li', attrs = {'class' : 'thumbnails_li'}):
            for a in li.find_all('a'):
                rec = {'jnl' : 'BOOK', 'tc' : 'T', 'note' : [], 'supervisor' : [], 'keyw' : []}
                rec['artlink'] = a['href']
                rec['doi'] = '30.3000/HongKongUSciTech/' + re.sub('\W', '', a['href'][10:])
                if fc:
                    rec['fc'] = fc
                recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    #informations at top of page
    for div in artpage.body.find_all('div', attrs = {'id' : 'content-full'}):
        #title
        for h3 in div .find_all('h3', attrs = {'class' : 'post-title'}):
            rec['tit'] = h3.text.strip()
            h3.decompose()
        #author
        for h3 in div .find_all('h3'):
            if not 'autaff' in rec.keys():
                rec['autaff'] = [[ h3.text.strip(), publisher ]]
    #abstract
    for div2 in artpage.body.find_all('div', attrs = {'class' : 'abstract_content'}):
        for strong in div2.find_all('strong'):
            if strong.text == 'Abstract':
                strong.decompose()
        rec['abs'] = re.sub(' *\[ *Hide abstract.*', '', div2.text.strip())
        div2.replace_with('XXXABSTRACTXXX')
    #information at bottom of page
    for table in artpage.body.find_all('table', attrs = {'class' : 'table-striped'}):
        for tr in table.find_all('td'):
            for child in tr.children:
                try:
                    child.name
                except:
                    pass
                if child.name == 'strong':
                    ult = child.text.strip()
                elif child.name == 'ul':
                    #supervisor
                    if ult == 'Supervisors':
                        for li in child.find_all('li'):
                            rec['supervisor'].append([ li.text.strip() ])
                    #keywords
                    elif ult == 'Subjects':
                        for li in child.find_all('li'):
                            rec['keyw'].append(li.text.strip())
                    #language
                    elif ult == 'Language':
                        language = child.text.strip()
                        if language != 'English':
                            rec['language'] = language
                    #DOI
                    elif ult == 'DOI':
                        rec['doi'] = child.text.strip()
    #pages, year
    divt = re.sub('[\n\t\r]', ' ', div.text.strip())
    divt = re.sub('XXXABSTRACTXXX.*', '', divt)
    rec['date'] = re.sub('.*THESIS *([12]\d\d\d).*', r'\1', divt)
    if re.search('\d pages', divt):
        rec['pages'] = re.sub('.*?(\d+) pages.*', r'\1', divt)                                                                  
    print '  ', rec.keys()

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
