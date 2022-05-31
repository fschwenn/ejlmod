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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Michigan U.'
numofpages = 10
rpp = 25
boringsubjects = ['Arts', 'Health Sciences', 'Humanities', 'Government Information and Law',
                  'College of Education, Health, & Human Services',
                  'Doctor of Nurse Anesthesia Practice',
                  'Industrial and Systems Engineering',
                  #'College of Engineering & Computer Science',
                  #'Industrial and Systems Engineering, College of Engineering & Computer Science',
                  'Engineering', 'Business and Economics', 'Social Sciences', 'Education',
                  'School for Environment and Sustainability', 'Manufacturing Engineering',
                  'Business', 'Government  Politics and Law', 'Physical Therapy']
boringdegrees = ['MSE', 'MS', "Master's Thesis", 'Ed.D.', 'Doctor of Anesthesia Practice (DAP)']

jnlfilename = 'THESES-MICHIGAN-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = ['2027.42/145174']
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

allrecs = []
for i in range(numofpages):
    #tocurl = 'https://deepblue.lib.umich.edu/handle/2027.42/39366/recent-submissions?offset=%i' % (20*i)
    tocurl = 'https://deepblue.lib.umich.edu/handle/2027.42/39366/browse?order=DESC&rpp=' + str(rpp) + 'sort_by=3&etal=-1&offset=' + str(i*rpp) + '&type=dateissued'
    print '==={ %i/%i }==={ %s }======' % (i+1, numofpages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(10)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
            rec['artlink'] = 'https://deepblue.lib.umich.edu' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('\/handle\/', '', a['href'])
            rec['tit'] = a.text.strip()
            if not rec['hdl'] in uninterestingDOIS:
                allrecs.append(rec)

j = 0
recs = []
for rec in allrecs:
    keepit = True
    restricted = False
    j += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (j, len(allrecs), len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'])
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(20)
    except:
        print 'wait 10 minutes'
        time.sleep(600)
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
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
                for dd in artpage.body.find_all('dd', attrs = {'class' : 'word-break'}):
                    if re.search('Restricted', dd.text):
                        restricted = True
                if not restricted:
                    rec['hidden'] = meta['content']
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*doi.org.', '', meta['content'])
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : ['data-cell', 'word-break']}):
            if label in tabelle.keys():
                tabelle[label].append(td.text.strip())
            else:
                tabelle[label] = [ td.text.strip() ]
    #keywords
    if 'dc.subject' in tabelle.keys():
        for keyw in tabelle['dc.subject']:
            rec['keyw'] = tabelle['dc.subject']
    #Department
    if 'dc.description.thesisdegreediscipline' in tabelle.keys():
        subject = tabelle['dc.description.thesisdegreediscipline'][0]
    if 'dc.subject.hlbtoplevel' in tabelle.keys():
        subject = tabelle['dc.subject.hlbtoplevel'][0]
    if subject:
        if subject in boringsubjects:
            print '   skip "%s"' % (subject)
            keepit = False
        else:
            rec['note'].append('SUBJECT=%s' % (subject))
    #PDF
    if 'dc.description.bitstreamurl' in tabelle.keys():
        for dd in artpage.body.find_all('dd', attrs = {'class' : 'word-break'}):
            if re.search('Restricted', dd.text):
                restricted = True
        if not restricted:
            rec['hidden'] =  tabelle['dc.description.bitstreamurl'][0]
    #ORCID
    if 'dc.identifier.orcid' in tabelle.keys():
        rec['autaff'][-1].append('ORCID:%s' % (re.sub('.*orcid.org.', '', tabelle['dc.identifier.orcid'][0])))
    rec['autaff'][-1].append(publisher)
    #Degree
    if not 'dc.description.thesisdegreename' in tabelle.keys():
        if 'dc.description' in tabelle.keys():
            for dd in  tabelle['dc.description']:
                if re.search('Master', dd):
                    tabelle['dc.description.thesisdegreename'] = [dd]
    if 'dc.description.thesisdegreename' in tabelle.keys():
        if tabelle['dc.description.thesisdegreename'][0] in boringdegrees or re.search('Master', tabelle['dc.description.thesisdegreename'][0]):
            print '   skip "%s"' % (tabelle['dc.description.thesisdegreename'][0])
            keepit = False
        elif tabelle['dc.description.thesisdegreename'][0] in ['Ph.D.', 'PHD', 'PhD']:
            pass
        else:
            rec['note'].append('DEGREE=%s' % (tabelle['dc.description.thesisdegreename'][0]))
    else:
        rec['note'] = ['NO DEGREE TYPE?!']
    if keepit:
        print '   ', rec.keys()
        recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['hdl'])

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

ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()


