# -*- coding: utf-8 -*-
#harvest theses from Royal Holloway, U. of London
#FS: 2021-11-30

import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+"_special"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'THESES-RoyalHolloway-%s' % (stampoftoday)

startyear = now.year-1
publisher = 'Royal Holloway, U. of London'



hdr = {'User-Agent' : 'Magic Browser'}
deps = [('department-of-physics(54da7e90-0544-4dbe-bd6d-4e85fa8f7465)', ''),
        ('department-of-mathematics(7ff3623d-1e5a-45d1-8ab1-6929b58c0f0b)', 'm')]
recs = []
for (dep, fc) in deps:
    tocurl = 'https://pure.royalholloway.ac.uk/portal/en/organisations/' + dep + '/publications.html?query=&organisationName=&organisations=&type=%2Fdk%2Fatira%2Fpure%2Fresearchoutput%2Fresearchoutputtypes%2Fthesis%2Fdoc&language=+&publicationYearsFrom=' + str(startyear) + '&publicationYearsTo=' + str(now.year) + '&publicationcategory=&peerreview=&openAccessPermissionStatus='
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for h2 in tocpage.body.find_all('h2'):
        for a in h2.find_all('a'):
            rec = {'tc' : 'T', 'note' : [], 'jnl' : 'BOOK', 'supervisor' : []}
            rec['link'] = a['href']
            rec['tit'] = a.text.strip()
            if fc:
                rec['fc'] = fc
            if re.search('\(....+\)', a['href']):
                rec['doi'] = '20.2000/RoyalHolloway/' + re.sub('.*\((.*)\).*', r'\1', a['href'])
            else:
                rec['doi'] = '20.2000/RoyalHolloway/' + re.sub('\W', '', re.sub('.*\/', '', a['href'])[:-4])
            recs.append(rec)
    time.sleep(5)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), re.sub('.*\/', '../', rec['link']))
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
    #author
    for ul in artpage.find_all('ul', attrs = {'class' : 'relations persons'}):
        rec['autaff'] = [[ ul.text.strip(), publisher ]]
    for tr in artpage.find_all('tr'):
        tht = ''
        for th in tr.find_all('th'):
            tht = th.text.strip()
        for td in tr.find_all('td'):
            #supervisor
            if tht == 'Supervisors/Advisors':
                for strong in td.find_all('strong'):
                    rec['supervisor'].append([strong.text.strip()])
            #date
            if tht == 'Award date':
                for span in td.find_all('span'):
                    rec['date'] = span.text.strip()
    #license
    for div in artpage.find_all('div', attrs = {'class' : 'creative_commons_license'}):
        for a in div.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
    #PDF
    for ul in artpage.find_all('ul', attrs = {'class' : 'relations documents'}):
        for a in ul.find_all('a'):
            if a.has_attr('href') and re.search('\.pdf$', a['href']):
                if 'license' in rec.keys():
                    rec['FFT'] = a['href']
                else:
                    rec['hidden'] = a['href']
    #abstract
    for div in artpage.find_all('div', attrs = {'class' : 'textblock'}):
        rec['abs'] = div.text.strip()
    #pages
    for div in artpage.find_all('div', attrs = {'class' : 'publication_view_title'}):
        divt = re.sub('[\n\t\r]', ' ', div.text.strip())
        if re.search('[12]\d\d\d\. *\d\d+ p\.', divt):
            rec['pages'] = re.sub('.*[12]\d\d\d\. *(\d\d+) p\..*', r'\1', divt)
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
