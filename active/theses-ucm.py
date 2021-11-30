# -*- coding: utf-8 -*-
#harvest theses from UCM, Somosaguas
#FS: 2021-11-30

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'UCM, Somosaguas'

hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-UniversidadComplutenseDeMadrid-%s' % (stampoftoday)
years = 1

deps = [('216', 'Madrid U.', ''),
        ('219', 'UCM, Madrid, Dept. Phys.', 'a'),
        ('222', 'UCM, Madrid, Dept. Phys.', ''),
        ('217', 'UCM, Madrid, Dept. Phys.', ''),
        ('6', 'UCM, Madrid, Dept. Phys.', ''),
        ('256', 'UCM, Madrid, Dept. Math.', 'm'),
        ('255', 'UCM, Madrid, Dept. Math.', 'm'),
        ('257', 'UCM, Madrid, Dept. Math.', 'm'),
        ('9132', 'UCM, Madrid, Dept. Math.', 'm'),
        ('9', 'UCM, Madrid, Dept. Math.', 'm'),
        ('252', 'UCM, Madrid, Dept. Math.', 'a'),
        ('9149', 'ICMAT, Madrid', 'm'),
        ('9150', 'UCM, Somosaguas', 'm'),
        ('9141', 'UCM, Somosaguas', '')]

links = []
recs = []
for (depnr, aff, fc) in deps:
    tocurl = 'https://eprints.ucm.es/view/divisions/%s.html' % (depnr)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(5)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'ep_view_page'}):
        h2t = ''
        for child in div.children:
            try:
                child.name
            except:
                continue
            if child.name == 'h2':
                h2t = child.text
            if child.name == 'p' and h2t in ['Thesis', 'Tesis']:
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
                rec['affiliation'] = aff
                if fc:
                    rec['fc'] = fc
                for a in child.find_all('a'):
                    rec['link'] = a['href']
                    rec['doi'] = '30.3000/UniversidadComplutenseDeMadrid/' + re.sub('\D', '', a['href'])
                    a.decompose()
                pt = re.sub('[\n\t\r]', '', child.text.strip())
                if re.search('\([12]\d\d\d\)', pt):
                    rec['date'] = re.sub('.*\(([12]\d\d\d)\).*', r'\1', pt)
                if not rec['link'] in links:
                    if 'date' in rec.keys():
                        if int(rec['date']) >= now.year-years:
                            recs.append(rec)
                    else:
                        recs.append(rec)
                    links.append(rec['link'])
        print len(recs)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'DC.date':
                rec['date'] = meta['content']
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'es':
                    rec['language'] = 'Spanish'
            #FFT
            elif meta['name'] == 'DC.identifier':
                if re.search('\.pdf$', meta['content']):
                    rec['hidden'] = meta['content']
            #author
            elif meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], rec['affiliation'] ]]
            #supervisor
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([meta['content']])
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DC.description':
                rec['abs'] = meta['content']
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
