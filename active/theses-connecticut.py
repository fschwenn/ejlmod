# -*- coding: utf-8 -*-
#harvest Connecticut U. theses
#FS: 2021-12-17


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
from inspire_utils.date import normalize_date

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Connecticut U.'

pages = 3 #+ 30

jnlfilename = 'THESES-CONNECTICUT-%s' % (stampoftoday)

basetocurl = 'https://opencommons.uconn.edu/dissertations/index.'
tocextension = 'html'

boringdepartments = ['Biomedical Science', 'Kinesiology', 'Communication Sciences',
                     'Psychology', 'Nursing', 'Business Administration', 'Philosophy',
                     'Agricultural and Resource Economics', 'Animal Science', 'Anthropology',
                     'Biomedical Engineering', 'Chemical Engineering', 'Chemistry',
                     'Civil Engineering', 'Curriculum and Instruction',
                     'Ecology and Evolutionary Biology', 'Economics', 'Educational Leadership (Ed.D.)',
                     'Educational Psychology', 'Electrical Engineering', 'English',
                     'Genetics and Genomics', 'Geography', 'Geological Sciences', 'German', 'History',
                     'Human Development and Family Studies', 'Italian',
                     'Learning, Leadership, and Education Policy', 'Linguistics',
                     'Literatures, Languages, and Cultures', 'Materials Science and Engineering',
                     'Materials Science', 'Mechanical Engineering', 'Medieval Studies',
                     'Molecular and Cell Biology', 'Natural Resources: Land, Water, and Air',
                     'Nutritional Science', 'Oceanography', 'Pharmaceutical Science',
                     'Physiology and Neurobiology', 'Plant Science', 'Political science',
                     'Polymer Science', 'Social Work', 'Sociology', 'Education Administration',
                     'Adult Learning', 'Biochemistry', 'Cell Biology',
                     'Comparative Literary and Cultural Studies', 'Educational Technology',
                     'Environmental Engineering', 'French', 'Microbiology', 'Music',
                     'Natural Resources: Land, Water, and Air', 'Pathobiology', 'Public Health',
                     'Spanish', 'Special Education', 'Structural Biology and Biophysics',
                     'Speech, Language, and Hearing Sciences', 'Statistics']

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
                if int(date) >= now.year - 1*10:
                    rec = {'jnl' : 'BOOK', 'tc' : 'T', 'date' : date, 'note' : []}
                    for a in child.find_all('a'):
                        if not re.search('(viewcontent.cgi|proquest.com|network.bepress.com)', a['href']):
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
                rec['pdf_url'] = meta['content']
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
        rec['doi'] = '20.2000/Connecticut/' + re.sub('\W', '', re.sub('.*edu', '', rec['artlink']))
        rec['link'] = rec['artlink']
    #keywords
    for div in artpage.body.find_all('div', attrs = {'id' : 'subject_area'}):
        for p in div.find_all('p'):
            rec['keyw'] = re.split(', ', p.text.strip())
    #embargo
    for div in artpage.body.find_all('div', attrs = {'id' : 'embargo_date'}):
        for p in div.find_all('p'):
            rec['embargo'] = normalize_date(p.text.strip())
    if 'pdf_url' in rec.keys():
        if 'embargo' in rec.keys():
            if rec['embargo'] > stampoftoday:
                print '    embargo until %s' % (rec['embargo'])
            else:
                rec['FFT'] = rec['pdf_url']
        else:
            rec['FFT'] = rec['pdf_url']
    #depatrment
    for div in artpage.body.find_all('div', attrs = {'id' : 'department'}):
        for p in div.find_all('p'):
            department = p.text.strip()
            if department in boringdepartments:
                print '    skip "%s"' % (department)
            else:
                rec['note'].append(department)
                print '  ', rec.keys()
                recs.append(rec)



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
