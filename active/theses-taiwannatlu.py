# -*- coding: utf-8 -*-
#harvest theses from Taiwan, Natl. Taiwan U.
#FS: 2021-11-14

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Taiwan, Natl. Taiwan U.'
jnlfilename = 'THESES-TaiwanNatlU-%s' % (stampoftoday)

rpp = 20
pages = 5
departments = [('PHYS', '65'), ('PHYS', '69'), ('MATH', '64'), ('MATH', '66'), ('ASTRO', '62')]
hdr = {'User-Agent' : 'Magic Browser'}
timespan = 2

departmentdict = {u'應用物理研究所' : 'Institute of Applied Physics',
                  u'應用物理所' : 'Institute of Applied Physics',
                  u'物理研究所' : 'Institute of Physics',
                  u'物理學研究所' : 'Institute of Physics',
                  u'應用數學科學研究所' : 'Institute of Applied Mathematics',
                  u'數學研究所' : 'Institute of Mathematics',
                  u'天文物理研究所' : 'Institute of Astrophysics'}

j = 0
prerecs = []
recs = []
for (subj, dep) in departments:
    if dep == '69':
        pages = 63
    elif dep == '66':
        pages = 23
    else:
        pages = 9
    j += 1
    for page in range(pages):
        tocurl = 'https://tdr.lib.ntu.edu.tw/handle/123456789/' + dep + '?offset=' + str(rpp*page) + '&locale=en'
        print '==={ %s %i/%i }==={ %s }===' % (subj, page+1 + (j-1)*pages, pages*len(departments), tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(6)
        #for td in tocpage.find_all('td', attrs = {'headers', 't2'}):
        for td in tocpage.find_all('tr'):
            year = 9999
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [],
                   'aff' : [publisher], 'refs' : []}
            for em in td.find_all('em'):
                emt = em.text.strip()
                if re.search('^\d\d\d\d$', emt):
                    year = int(emt)
            if year >= now.year-timespan:
                if subj == 'MATH':
                    rec['fc'] = 'm'
                elif subj == 'ASTRO':
                    rec['fc'] = 'a'
                for a in td.find_all('a'):
                    if a.has_attr('href') and re.search('handle\/', a['href']):
                        rec['link'] = 'https://tdr.lib.ntu.edu.tw' + a['href']  + '?mode=full&locale=en'
                        rec['doi'] = '20.2000/TaiwanNatlU/' + re.sub('.*handle\/', '', a['href'])
                        prerecs.append(rec)
            else:
                print '   %i too old' % (year)

i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    (author, altauthor, zhtitle, entitle) = (False, False, False, False)
    keepit = True
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if meta.has_attr('xml:lang') and meta['xml:lang'] == 'zh_TW':
                    altauthor = meta['content']
                else:
                    author = meta['content']
            #title
            elif meta['name'] == 'DC.title':
                if meta.has_attr('xml:lang'):
                    if meta['xml:lang'] == 'zh_TW':
                        zhtitle =  meta['content']
                    elif  meta['xml:lang'] == 'en':
                        entitle = meta['content']
                else:
                    rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'] += re.split(',', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = re.sub('\/jspui', '', meta['content'])
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('^10\.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta.has_attr('xml:lang') and meta['xml:lang'] == 'en':
                    rec['abs'] = meta['content']
            #pages
            elif meta['name'] == 'DC.relation':
                rec['pages'] = meta['content']
    #author
    if altauthor:
        author += ', CHINESENAME: %s' % (altauthor)
    rec['auts'] = [ author ]
    #more metadata
    for table in artpage.body.find_all('table', attrs = {'class' : 'panel-body'}):
        for tr in table.find_all('tr'):
            for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
                label = td.text.strip()
            for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue', 'headers' : 's2'}):
                #references
                if label == 'dc.identifier.citation':
                    for br in td.find_all('br'):
                        br.replace_with('BRBRBR')
                    for ref in re.split('BRBRBR', td.text.strip()):
                        rec['refs'].append([('x', ref)])
                #supervisor
                if label == 'dc.contributor.advisor':
                    if td.text.strip():
                        rec['supervisor'].append([re.sub('.*\((.*)\)', r'\1', td.text.strip())])
                #language
                if label == 'dc.language.iso':
                    if td.text.strip() == 'en':
                        if entitle:
                            rec['tit'] = entitle
                        if zhtitle:
                            rec['transtit'] = zhtitle
                    elif td.text.strip():
                        if td.text.strip() in ['zh_TW', 'zh-TW']:
                            rec['language'] = 'Chinese'
                        else:
                            rec['note'].append('LANGUAGE=%s' % (td.text.strip()))
                        if zhtitle:
                            rec['otits'] = [ zhtitle ]
                        if entitle:
                            rec['tit'] = entitle
                #degree
                elif label == 'dc.description.degree':
                    degree = td.text.strip()
                    if not degree == u'博士':
                        if degree == u'碩士':
                            print '   skip master thesis'
                            keepit = False
                        elif degree:
                            rec['note'].append('unknown degree: %s' % (degree))
                #department
                elif label == 'dc.contributor.author-dept':
                    department = td.text.strip()
                    if department:
                        if department in departmentdict.keys():
                            rec['note'].append('DEPARTMENT=%s' % (departmentdict[department]))
                        else:
                            rec['note'].append('DEPARTMENT=%s' % (department))
    if keepit:
        recs.append(rec)
        print '  ', ', '.join(['%s(%i)' % (k, len(rec[k])) for k in rec.keys()])

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

