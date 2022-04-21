# -*- coding: utf-8 -*-
#harvest theses from Potsdam
#FS: 2022-04-20

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

publisher = 'Potsdam U.'
jnlfilename = 'THESES-POTSDAM-%s' % (stampoftoday)

rpp = 20
pages = 1

hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for (fc, dep) in [('m', '17100'), ('', '17102')]:
    for page in range(pages):
        tocurl = 'https://publishup.uni-potsdam.de/solrsearch/index/search/searchtype/collection/id/' + dep + '/start/' + str(rpp*page) + '/rows/' + str(rpp) + '/doctypefq/doctoralthesis/sortfield/year/sortorder/desc'
        print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for div in tocpage.body.find_all('div', attrs = {'class' : 'result_box'}):
            for div2 in div.find_all('div', attrs = {'class' : 'results_title'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : [], 'supervisorprelim' : []}
                if fc:
                    rec['fc'] = fc
                for a in div2.find_all('a'):
                    rec['artlink'] = 'https://publishup.uni-potsdam.de' + a['href']
                    recs.append(rec)
        time.sleep(10)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
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
                #author
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'] ]]
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'citation_date':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'citation_keywords':
                    for keyw in re.split(' *; *', meta['content']):
                        if not keyw in rec['keyw']:
                            rec['keyw'].append(keyw)
                #abstract
                elif meta['name'] == 'dcterms.abstract':
                    if meta.has_attr('lang' ):
                        if meta['lang'] == 'de':
                            rec['abs_de'] = meta['content']
                        else:
                            rec['abs'] = meta['content']
                    else:
                        if re.search(' the ', meta['content']):
                            rec['abs'] = meta['content']
                        else:
                            rec['abs_de'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['citation_pdf_url'] = meta['content']
                #Rights
                elif meta['name'] == 'DC.rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['license'] = {'url' : meta['content']}
    for table in artpage.find_all('table', attrs = {'class' : 'result-data'}):
        profdict = {}
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                #author
                if tht == 'Author details:':
                    for a in td.find_all('a', attrs = {'class' : 'orcid-link'}):
                        rec['autaff'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                    for a in td.find_all('a', attrs = {'class' : 'gnd-link'}):
                        gndlink = a['href']
                #URN
                elif tht == 'URN:':
                    rec['urn'] = td.text.strip()
                #DOI
                elif tht == 'DOI:':
                    rec['doi'] = re.sub('.*doi.org\/', '', td.text.strip())
                #reviewers
                elif tht in ['Reviewer(s):']:
                    prof = ''
                    for a in td.find_all('a'):
                        if re.search('solrsearch', a['href']):
                            prof = a.text.strip()
                        elif re.search('orcid.org', a['href']):
                            profdict[prof] = re.sub('.*orcid.org\/', 'ORCID:', a['href'])
                #supervisor
                elif tht in ['Supervisor(s):']:
                    for a in td.find_all('a'):
                        if re.search('solrsearch', a['href']):
                            rec['supervisorprelim'].append([a.text.strip()])
                        elif re.search('orcid.org', a['href']):
                            rec['supervisorprelim'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                        elif re.search('nv.info.gnd', a['href']):
                            gnd = a['href']
                    if not rec['supervisorprelim']:
                        for sv in re.split(', ', td.text.strip()):
                            rec['supervisorprelim'].append([sv])
                #language
                elif tht == 'Language:':
                    if td.text.strip() == 'German':
                        rec['language'] = 'German'
                #aff
                elif tht == 'Granting Institution:':
                    rec['autaff'][-1].append('%s, Bochum, Germany' % (td.text.strip()))
                #pages
                elif tht == 'Number of pages:':
                    if re.search('\d\d', td.text):
                        rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', td.text.strip())
    #check profdict
    for sv in rec['supervisorprelim']:
        if len(sv) == 1 and sv[0] in profdict.keys():
            rec['supervisor'].append([sv[0], profdict[sv[0]]])
            rec['note'].append('%s -> %s' % (sv[0], profdict[sv[0]]))
        else:
            rec['supervisor'].append(sv)
    #abstract
    if not 'abs' in rec.keys() and 'abs_de' in rec.keys():
        rec['abs'] = rec['abs_de']
    #fulltext
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    print '  ', rec.keys()
    rec['autaff'][-1].append(publisher)
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/Potsdam/' + re.sub('.*\/', '', rec['artlink'])
        rec['link'] = rec['artlink']

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
