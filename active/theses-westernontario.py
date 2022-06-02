# -*- coding: utf-8 -*-
#harvest Western Ontario U. theses
#FS: 2022-03-05


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

publisher = 'Western Ontario U.'

pages = 2

jnlfilename = 'THESES-WesternOntario-%s' % (stampoftoday)

basetocurl = 'https://ir.lib.uwo.ca/etd/index.'
tocextension = 'html'

boring = ['Educational Psychology', 'Art History', 'Communication',
          'African and African Diaspora Studies', 'Anthropology', 'Architecture',
          'Atmospheric Science', 'Biological Sciences', 'Economics',
          'Biomedical and Health Informatics', 'Biostatistics', 'Chemistry',
          'Communication Sciences and Disorders', 'Biomedical Sciences'
          'Engineering', 'English', 'Freshwater Sciences', 'Geosciences',
          'Health Care Informatics', 'Health Sciences', 'History',
          'Information Studies', 'Kinesiology', 'Linguistics', 'Management Science',
          'Music', 'Nursing', 'Occupational Therapy', 'Political Science', 'Psychology',
          'Public Health', 'Social Welfare', 'Sociology', 'Urban Education',
          'Curriculum and Instruction', 'Environmental Health Sciences',
          'Epidemiology', 'Geography', 'Management', 'Administrative Leadership',
          'Africology', 'Art Education', 'Art', 'Biomedical Sciences',
          'Business Administration', 'Engineering', 'Environmental & Occupational Health',
          'Information Technology Management', 'Library and Information Science',
          'Medical Informatics', 'Performing Arts', 'Social Work', 'Urban Planning',
          'Mechanical and Materials Engineering', 'Art and Visual Culture',
          'Biochemistry', 'Biology', 'Biomedical Engineering',
          'Civil and Environmental Engineering', 'Education',
          'Orthodontics', 'Pathology and Laboratory Medicine', 'Physiology and Pharmacology',
          'Health and Rehabilitation Sciences', 'Comparative Literature',
          'Epidemiology and Biostatistics', 'Geophysics', 'Health Information Science',
          'Health Promotion', 'Media Studies', 'Physical Therapy', 'Theory and Criticism',
          'Gender, Sexuality & Women’s Studies', 'Law', 'Library & Information Science',
          'Microbiology and Immunology', 'Anatomy and Cell Biology', 'Medical Biophysics',
          'Electrical and Computer Engineering', 'Philosophy', 'Statistics and Actuarial Sciences',
          'Computer Science', 'Geology', 'Neuroscience', 'Business',
          'Family Medicine', 'French', 'Gender, Sexuality & Women’s Studies',
          'Hispanic Studies', 'Library & Information Science', 'Visual Arts',
          "Women's Studies and Feminist Research",
          'Chemical and Biochemical Engineering', 'Urban Studies']
boring += ['Master of Arts', 'Master of Science', 'Master of Music', 'Master of Fine Arts',
           'Master of Clinical Dentistry', 'Master of Engineering Science',
           'Master of Laws', 'Master of Clinical Science',
           'Master of Library and Information Science', 'Master of Urban Planning']

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

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
                    rec = {'jnl' : 'BOOK', 'tc' : 'T', 'date' : date, 'note' : [], 'supervisor' : []}
                    for a in child.find_all('a'):
                        if not re.search('(viewcontent.cgi|proquest.com)', a['href']):
                            rec['tit'] = a.text.strip()
                            rec['link'] = a['href']
                            a.replace_with('')
                            if not rec['link'] in uninterestingDOIS:
                                prerecs.append(rec)
    print '  ', len(prerecs)
    tocextension = '%i.html' % (i+2)

recs = []
i = 0
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #abstract
            if meta['name'] == 'description':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #thesis type
            elif meta['name'] == 'bepress_citation_dissertation_name':
                rec['note'] = [ meta['content'] ]
                if meta['content'] in boring:
                    print '    skip "%s"' % (meta['content'])
                    keepit = False
                elif meta['content'] != 'Doctor of Philosophy':
                    rec['note'].append(meta['content'])
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
    for div in artpage.body.find_all('div', attrs = {'id' : 'advisor3'}):
        for p in div.find_all('p'):
            rec['supervisor'].append( [re.sub('^Dr. ', '', p.text.strip())] )
    if not rec.has_key('doi'):
        rec['doi'] = '30.3000/WesternOntario/' + re.sub('\W', '', re.sub('.*ca', '', rec['link']))
        rec['link'] = rec['link']
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
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
    #department
    for div in artpage.body.find_all('div', attrs = {'id' : 'department'}):
        for p in div.find_all('p'):
            department = p.text.strip()
            if department in boring:
                print '    skip "%s"' % (department)
                keepit = False
            else:
                rec['note'].append(department)
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['link'])


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
