# -*- coding: utf-8 -*-
#harvest Florida Intl. U.
#FS: 2021-12-10

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

publisher = 'Florida Intl. U.'

pages = 2

jnlfilename = 'THESES-FloridaIntlU-%s' % (stampoftoday)

basetocurl = 'https://digitalcommons.fiu.edu/etd/index.'
tocextension = 'html'

boringdepartments = ['English', 'Electrical Engineering', 'International Relations', 'International Studies',
                     'Civil Engineering', 'Adult Education and Human Resource Development', 'Biochemistry',
                     'Biology', 'Biomedical Engineering', 'Biomedical Sciences', 'Business Administration',
                     'Chemistry', 'Computer Engineering', 'Construction Management',
                     #'Computer Science',
                     'Creative Writing', 'Curriculum and Instruction', 'Dietetics and Nutrition',
                     'Earth Systems Science', 'Economics', 'Educational Administration and Supervision',
                     'Electrical and Computer Engineering', 'Engineering Management', 'Environmental Studies',
                     'Exceptional Student Education', 'Forensic Science', 'Global and Sociocultural Studies',
                     'Higher Education', 'History', 'Hospitality Management', 'International Crime and Justice',
                     'Materials Science and Engineering', 'Mechanical Engineering', 'Music Education', 'Nursing',
                     'Political Science', 'Psychology', 'Public Affairs', 'Public Health', 'Social Welfare',
                     'Comparative Sociology', 'Earth and Environment', 'Geosciences',
                     'Higher Education Administration', 'Management Information Systems', 'Music',
                     'Public Administration', 'Religious Studies', 'Social Work',
                     'Accounting', 'Adult Education', 'Athletic Training', 'Early Childhood Education',
                     'Educational Leadership', 'Environmental Engineering', 'Finance', 'International Business',
                     'Latin American and Caribbean Studies', 'Medicine', 'Special Education',
                     'Spanish', 'Speech-Language Pathology', 'Teaching and Learning']
boringdegrees = ['Master of Arts (MA)', 'Master of Fine Arts (MFA)',
                 'Master of Science (MS)', 'Doctor of Education (EdD)',
                 'Master of Music (MM)']

prerecs = []
date = 9999
for i in range(pages):
    tocurl = basetocurl + tocextension
    print '==={ %i/%i }==={ %s }===' % (i+1, pages, tocurl)
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'id' : 'series-home'}):
        for child in div.children:
            try:
                name = child.name
            except:
                continue
            if name == 'h4':
                for span in child.find_all('span'):
                    date = span.text.strip()
            elif name == 'p':
                if child.has_attr('class') and 'article-listing' in child['class']:
                    #year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
                    if int(date) >= now.year - 1:
                        rec = {'jnl' : 'BOOK', 'tc' : 'T', 'date' : date, 'note' : []}
                        for a in child.find_all('a'):                    
                            rec['tit'] = a.text.strip()
                            rec['artlink'] = a['href']
                            a.replace_with('')
                            prerecs.append(rec)
    print '  ', len(prerecs)
    tocextension = '%i.html' % (i+2)

recs = []
i = 0
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #abstract
            if meta['name'] == 'description':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #author
            elif meta['name'] == 'bepress_citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #fulltext
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['pdf_url'] = meta['content']
            #DOI
            elif meta['name'] == 'bepress_citation_doi':
                rec['doi'] = re.sub('^ht.*?\/10', '10', meta['content'])
            #date
            elif meta['name'] == 'bepress_citation_date':
                rec['date'] = meta['content']
    #degree
    for div in artpage.body.find_all('div', attrs = {'id' : 'thesis_degree_name'}):
        for p in div.find_all('p'):
            degree = p.text.strip()
            rec['note'].append(degree)
            if degree in boringdegrees:
                print '    skip "%s"' % (degree)
                keepit = False                
    #peusoDOI
    if not rec.has_key('doi'):
        rec['doi'] = '20.2000/FloridaNatlU/' + re.sub('\W', '', re.sub('.*edu', '', rec['artlink']))
        rec['link'] = rec['artlink']
    #ORCID
    for div in artpage.body.find_all('div', attrs = {'id' : 'orcid_id'}):
        for p in div.find_all('p'):
            rec['autaff'][-1].append('ORCID:'+re.sub('.*org\/', '', p.text.strip()))
    rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    #discipline    
    for div in artpage.body.find_all('div', attrs = {'id' : 'thesis_degree_discipline'}):
        for p in div.find_all('p'):
            department = p.text.strip()
            rec['note'].append(department)                
            if department in boringdepartments:
                print '    skip "%s"' % (department)
                keepit = False
    if keepit:
        print ' ' , rec.keys()
        recs.append(rec)

    
    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
