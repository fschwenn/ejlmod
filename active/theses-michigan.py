# -*- coding: utf-8 -*-
#harvest theses from Michigan
#FS: 2019-10-28


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
irrelevantsubjects = []

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Michigan U.'
numofpages = 10
rpp = 25

jnlfilename = 'THESES-MICHIGAN-b-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
allrecs = []
for i in range(numofpages):
    #tocurl = 'https://deepblue.lib.umich.edu/handle/2027.42/39366/recent-submissions?offset=%i' % (20*i)
    tocurl = 'https://deepblue.lib.umich.edu/handle/2027.42/39366/browse?order=DESC&rpp=' + str(rpp) + 'sort_by=3&etal=-1&offset=' + str(i*rpp) + '&type=dateissued'
    print '---{ %i/%i }---{ %s }------' % (i+1, numofpages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(10)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK'}
            rec['artlink'] = 'https://deepblue.lib.umich.edu' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('\/handle\/', '', a['href'])
            rec['tit'] = a.text.strip()
            if not rec['hdl'] in ['2027.42/145174']:
                allrecs.append(rec)

j = 0
recsbysubject = {}
for rec in allrecs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(allrecs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'])
        artpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(30)
    except:
        print 'wait 10 minutes'
        time.sleep(600)
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req))
            time.sleep(30)
        except:
            continue
    tabelle = {}
    subject = ''
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content']]]
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #PDF
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'data-cell'}):
            if label in tabelle.keys():
                tabelle[label].append(td.text.strip())
            else:
                tabelle[label] = [ td.text.strip() ]
    if 'dc.subject' in tabelle.keys():
        for keyw in tabelle['dc.subject']:
            rec['keyw'] = tabelle['dc.subject']
    if 'dc.description.thesisdegreediscipline' in tabelle.keys():
        subject = tabelle['dc.description.thesisdegreediscipline'][0]
    if 'dc.subject.hlbtoplevel' in tabelle.keys():
        subject = tabelle['dc.subject.hlbtoplevel'][0]
    if 'dc.identifier.orcid' in tabelle.keys():
        rec['autaff'][-1].append('ORCID:%s' % (tabelle['dc.identifier.orcid'][0]))
    rec['autaff'][-1].append(publisher)
    if 'dc.description.thesisdegreename' in tabelle.keys():
        if tabelle['dc.description.thesisdegreename'][0] in ['Ph.D.', 'PHD']:
            if subject in recsbysubject.keys():
                recsbysubject[subject].append(rec)
            else:
                recsbysubject[subject] = [rec]
        else:
            print '  skip "%s"' % (tabelle['dc.description.thesisdegreename'][0])
    print '   ', len(recsbysubject.keys()), [len(recsbysubject[s]) for s in recsbysubject.keys()]

for subject in recsbysubject.keys():
    if subject in ['Arts', 'Health Sciences', 'Humanities', 'Government Information and Law',
                   'Engineering', 'Business and Economics', 'Social Sciences', 'Education',
                   'Business', 'Government  Politics and Law']:
        print 'skip', subject
    else:
        recs = recsbysubject[subject]
        jnlfilename = 'THESES-MICHIGAN-%s-b-%s' % (stampoftoday, re.sub('\W', '_', subject))
        #closing of files and printing
        xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
        ejlmod2.writeXML(recs,xmlfile,publisher)
        xmlfile.close()
        #retrival
        retfiles_text = open(retfiles_path,"r").read()
        line = jnlfilename+'.xml'+ "\n"
        if not line in retfiles_text: 
            retfiles = open(retfiles_path,"a")
            retfiles.write(line)
            retfiles.close()


