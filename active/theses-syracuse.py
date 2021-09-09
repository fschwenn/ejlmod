# -*- coding: utf-8 -*-
#harvest Syracuse U. theses
#FS: 2021-08-13


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

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Syracuse U.'

pages = 1

jnlfilename = 'THESES-SYRACUSE-%s' % (stampoftoday)

basetocurl = 'https://surface.syr.edu/etd/index.'
tocextension = 'html'

boringdepartments = ['Biology', 'Mechanical and Aerospace Engineering', 'Chemistry',
                     'Electrical Engineering and Computer Science', 'Psychology',
                     'Teaching and Leadership', 'Political Science', 'Design',
                     'Cultural Foundations of Education', 'Reading and Language Arts',
                     'Mass Communications', 'Earth Sciences', 'Anthropology',
                     'School of Information Studies', 'Religion', 'Philosophy',
                     'Marriage and Family Therapy', 'Human Development and Family Science',
                     'Geography', 'Counseling and Human Services', 'Sociology',
                     'Social Sciences', 'History', 'Entrepreneurship and Emerging Enterprises',
                     'English', 'Communication Sciences and Disorders', 'Writing Program',
                     'Higher Education', 'Finance', 'Business Administration',
                     'Biomedical and Chemical Engineering', 'Economics',
                     'Civil and Environmental Engineering', 'Public Administration',
                     'Child and Family Studies', 'Instructional Design, Development and Evaluation',
                     'Media Studies', 'Science Teaching', 'Communication and Rhetorical Studies',
                     'African American Studies', 'Public Relations', 'Accounting',
                     'Information Science and Technology', 'Exercise Science',
                     'Nutrition Science and Dietetics', 'Marketing', 'Communications Management',
                     'Information Management and Technology', 'Management', 
                     'Languages, Literatures, and Linguistics', 'Supply Chain Management']

prerecs = []
date = False
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
            #thesis type
            #elif meta['name'] == 'bepress_citation_dissertation_name':
            #    rec['note'] = [ meta['content'] ]
            #    if meta['content'] == "Ph.D.":
            #        rec['MARC'] = [('502', [('d', date), ('c', 'Wayne State U., Detroit'), ('b', 'PhD')])]
            #author
            elif meta['name'] == 'bepress_citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #fulltext
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['FFT'] = meta['content']
            #DOI
            elif meta['name'] == 'bepress_citation_doi':
                rec['doi'] = re.sub('^ht.*?\/10', '10', meta['content'])
            #date
            elif meta['name'] == 'bepress_citation_date':
                rec['date'] = meta['content']
    #supervisor
    for div in artpage.body.find_all('div', attrs = {'id' : 'advisor1'}):
        for p in div.find_all('p'):
            rec['supervisor'] = [[ re.sub('^Dr. ', '', p.text.strip()) ]]
    for div in artpage.body.find_all('div', attrs = {'id' : 'advisor2'}):
        for p in div.find_all('p'):
            rec['supervisor'].append( [re.sub('^Dr. ', '', p.text.strip())] )
    if not rec.has_key('doi'):
        rec['doi'] = '20.2000/Syracuse' + re.sub('\W', '', re.sub('.*edu', '', rec['artlink']))
        rec['link'] = rec['artlink']
    #depatrment
    for div in artpage.body.find_all('div', attrs = {'id' : 'department'}):
        for p in div.find_all('p'):
            department = p.text.strip()
            if department in boringdepartments:
                print '    skip "%s"' % (department)
            else:
                rec['note'].append(department)
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
