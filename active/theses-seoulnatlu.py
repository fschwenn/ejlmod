# -*- coding: utf-8 -*-
#harvest theses from Seoul Natl. U.
#FS: 2020-11-19

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Seoul Natl. U.'

rpp = 20
pages = 1
departments = [('PHYS', '17020'), ('MATH', '17007'), ('ASTRO', '16967')]
hdr = {'User-Agent' : 'Magic Browser'}

for (subj, dep) in departments:
    prerecs = []
    jnlfilename = 'THESES-SeoulNatlU-%s-%s' % (stampoftoday, subj)
    for page in range(pages):
        tocurl = 'http://s-space.snu.ac.kr/handle/10371/' + dep + '?page=' + str(page+1) + '&offset=' + str(rpp*page)
        print '==={ %s %i/%i }==={ %s }===' % (subj, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(3)
        for tr in tocpage.body.find_all('tr'):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
            for a in tr.find_all('a'):
                if a.has_attr('href') and re.search('handle\/', a['href']):
                    rec['artlink'] = 'http://s-space.snu.ac.kr/' + a['href'] 
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    prerecs.append(rec)

    i = 0
    recs = []
    for rec in prerecs:
        i += 1
        print '---{ %s }---{ %i/%i (%i) }---{ %s }---' % (subj, i, len(prerecs), len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            time.sleep(5)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['artlink'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            except:
                print "no access to %s" % (rec['link'])
                continue
        (author, altauthor) = (False, False)
        keepit = True
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'DC.creator':
                    author = meta['content']
                #supervisor / english name
                elif meta['name'] == 'DC.contributor':
                    if meta.has_attr('qualifier'):
                        if meta['qualifier'] == 'advisor':
                            rec['supervisor'].append([meta['content']])
                        elif meta['qualifier'] == 'AlternativeAuthor':
                            altauthor = meta['content']
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'DCTERMS.issued':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    if meta.has_attr('qualifier') and meta['qualifier'] == 'ddc':
                        rec['ddc'] = meta['content']
                        rec['note'].append('DDC=%s' % (meta['content']))
                        if rec['ddc'][:2] in ['54', '55', '56', '57', '58', '59']:
                            keepit = False
                            print '  skip DDC=', rec['ddc']
                    else:
                        for keyw in re.split(' *; *', meta['content']):
                            rec['keyw'].append(keyw)
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['hidden'] = meta['content']
                #DDC
                elif meta['name'] == 'DCTERMS.extent':
                    if re.search('\d\d', meta['content']):
                        rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', meta['content'])
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if re.search(' the ', meta['content']):
                        rec['abs'] = meta['content']
        #author
        if altauthor:
            if author:
                rec['MARC'] = [('100', [('a', author), ('q', altauthor), ('v', publisher)])]
            else:
                rec['autaff'] = [[ altauthor, publisher ]]
        else:
            rec['autaff'] = [[ author, publisher ]]
        if keepit:
            recs.append(rec)
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
        
