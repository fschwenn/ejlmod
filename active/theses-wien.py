# -*- coding: utf-8 -*-
#harvest theses from Wien U.
#FS: 2021-03-17

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

startyear = now.year - 1

hdr = {'User-Agent' : 'Magic Browser'}

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

for (publisher, fac, facnum) in [('Vienna U., Dept. Math. ', 'math', '56'), ('Vienna U.', 'phys', '51')]:
    jnlfilename = 'THESES-WIEN_%s-%s' % (fac, stampoftoday)
    prerecs = []
    tocurl = 'http://othes.univie.ac.at/view/fakultaet/A%s.date.html' % (facnum)
    print '==={ %s }==={ %s }===' % (fac, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    for p in tocpage.body.find_all('p'):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        if fac == 'math':
            rec['fc'] = 'm'
        for aut in p.find_all('span', attrs = {'class' : 'person_name'}):
            rec['autaff'] = [[ aut.text.strip(), publisher ]]
            for a in p.find_all('a'):
                rec['artlink'] = a['href']
                a.replace_with('XXXX')
            pt = re.sub('[\n\t\r]', '', p.text.strip())
            if not re.search('Diplomarbeit', pt) and not re.search('Masterarbeit', pt):
                pt = re.sub('XXXX.*', '', pt)
                if re.search('\(\d\d\d\d\)', pt):
                    rec['year'] = re.sub('.*\(([12]\d\d\d).*', r'\1', pt)
                    if int(rec['year']) >= startyear:
                        if not rec['artlink'] in uninterestingDOIS:
                            prerecs.append(rec)
                            uninterestingDOIS.append(rec['artlink'])

    recs = []
    i = 0
    for rec in prerecs:
        i += 1
        keepit = True
        print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            time.sleep(3)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            except:
                print "no access to %s" % (rec['link'])
                continue
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #author
                if meta['name'] == 'eprints.title':
                    rec['tit'] = meta['content']
                #thesis type
                elif meta['name'] == 'eprints.thesis_type':
                    if meta['content'] in ['master', 'bachelor', 'dipl', 'magister', 'magister_ulg']:
                        print ' skip', meta['content']
                        keepit = False
                    else:
                        rec['note'].append(meta['content'])
                #pages
                elif meta['name'] == 'eprints.pages':
                    if re.search('\d\d\d', meta['content']):
                        rec['pages'] = re.sub('.*?(\d\d\d).*', r'\1', meta['content'])
                #full_text_status
                elif meta['name'] == 'eprints.full_text_status':
                    rec['full_text_status'] = meta['content']
                #eprints.document_url
                elif meta['name'] == 'eprints.document_url':
                    rec['document_url'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    rec['keyw'] += re.split(' \/ ', re.sub('^\d\d\.\d\d ', '', meta['content']))
                #abstract
                elif meta['name'] == 'DC.description':
                    if re.search(' the ', meta['content']):
                        rec['abs'] = meta['content']
                    else:
                        rec['absde'] = meta['content']
                #DC.rights
                elif meta['name'] == 'DC.rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['license'] = {'url' : meta['content']}
                    rec['note'].append(meta['content'])

        #fulltext
        if 'document_url' in rec.keys():
            if 'full_text_status' in rec.keys() and rec['full_text_status'] == 'public':
                if 'licence' in rec.keys():
                    rec['FFT'] = rec['document_url']
                else:
                    rec['hidden'] = rec['document_url']

        #PIDs
        for div in artpage.find_all('div'):
            for a in div.find_all('a'):
                if a.has_attr('href'):
                    if re.search('doi.org\/10', a['href']):
                        rec['doi'] = re.sub('.*doi.org\/', '', a['href'])
                    elif re.search('resolver.obvsg.at', a['href']):
                        rec['urn'] = re.sub('.*resolver.obvsg.at.', '', a['href'])

        for tr in artpage.find_all('tr'):
            tht = ''
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td', attrs = {'valign' : 'top'}):
                #language
                if tht in ['Language:', 'Sprache']:
                    if td.text.strip() == 'ger ... Deutsch':
                        rec['language'] = 'German'
                #supervisor
                elif tht in ['Supervisor:', 'BetreuerIn:']:
                    rec['supervisor'].append([td.text.strip()])

        if not 'abs' in rec.keys() and 'absde' in rec.keys():
            rec['abs'] = rec['absde']
        if not 'doi' in rec.keys() and not 'urn' in rec.keys():
            rec['doi'] = '20.2000/Wien/' + re.sub('\D', '', rec['artlink'])
            rec['link'] = rec['artlink']
        if keepit:
            recs.append(rec)
            print ' ', rec.keys()
        else:
            newuninterestingDOIS.append(rec['artlink'])

    #closing of files and printing
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, 'r').read()
    line = jnlfilename+'.xml'+ '\n'
    if not line in retfiles_text:
        retfiles = open(retfiles_path, 'a')
        retfiles.write(line)
        retfiles.close()


ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()
