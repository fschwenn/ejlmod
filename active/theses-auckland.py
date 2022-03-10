# -*- coding: utf-8 -*-
#harvest theses from Auckland U.
#FS: 2022-03-07

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
rpp = 50
pages = 8

publisher = 'Auckland U.'

jnlfilename = 'THESES-AUCKLAND-%s' % (stampoftoday)
boring = ['Mechanical Engineering', 'Politics', 'Biology', 'Chemistry', 'Urban Planning',
          'Anthropology', 'Chemical Sciences', 'Civil Engineering', 'Engineering',
          'General Practice and Primary Health Care', 'Marine Science', 'Marketing',
          'Chemical and Materials Engineering', 'Civil and Environmental Engineering',
          'Computer Systems Engineering', 'Economics', 'Education', 'Health Sciences', 
          'Electrical, Computer and Software Engineering', 'Geology', 'Information Systems',
          'Management and International Business', 'Material Engineering',
          'Media and Communication', 'Operations Research', 'Ophthalmology', 'Philosophy',
          'Politics and International Relations', 'Sociology', 'Statistics',
          'Accounting', 'Applied Language Studies and Linguistics', 'Asian Studies',
          'Biological Sciences', 'Biological Science', 'Biomedical Science',
          'Chemical and Material Engineering', 'Computer Science', 'Environmental Science',
          'Finance', 'Fine Arts', 'General Practice', 'History', 'Mathematics Education',
          'Medicine', 'Molecular Medicine and Pathology', 'Optometry and Vision Science',
          'Pharmaceutics', 'Pharmacy', 'Population Health', 'Psychiatry', 'Psychology',
          'Anaesthesiology', 'Anatomy and medical imaging', 'Anatomy', 'Ancient History',
          'Applied Linguistics', 'Architecture and Planning', 'Architecture', 'Art History',
          'Bioengineering', 'Biomedical Engineering', 'Cardio-renal Physiology',
          'Chemical Science', 'Chinese Linguistics', 'Clinical Psychology',
          'Community Health', 'Comparative Literature', 'ComputerScience', 
          'Critical Studies in Education', 'Dance Studies', 'Development Studies',
          'Discipline of Nutrition', 'Education and Social Work', 'Social Work', 
          'Education (Applied Linguistics and TESOL)', 'Electrical and Computer Engineering',
          'Electrical and Electronic Engineering', 'Electrical Engineering',
          'Engineering Science', 'English Literature', 'English', 'Exercise Sciences',
          'Food Science', 'Forensic Science', 'Geography', 'Geophysics', 'Gepphysics',
          'Health Psychology', 'International Business', 'Law', 'Linguistics', 'Management',
          'Marine Science/Computer Science', 'Mechatronics Engineering', 'Music', 
          'Media, Film and Television', 'Medical and Health Sciences', 'Molecular Medicine',
          'Nursing', 'Nutrition and Dietetics', 'Optometry', 'Perinatal Sciences',
          'Perinatal Science', 'Physiology', 'Planning', u'Public Health (Māori Health)',
          'Software Engineering', 'Speech Science', 'Surgery', 'Urban Design',
          'Audiology', 'Behavioural Science', 'Biochemistry', 'Biomedical Sciences',
          'Chemical & Materials Engineering', 'Commercial Law', 'Composition',
          'Computer Sciences', 'Dance Studies, Creative Arts & Industries', 'DMA',
          'Earth Science', 'Educational Technology', 'Education (Applied Linguistics & TESOL)',
          'Electrical and Electronics Engineering', 'EngineeringScience', 'English and Psychology',
          'Film, Media and Television', 'Italian', 'Marine Sciences', 'Media and Communications',
          'Medical Imaging', 'Medical Sciences', 'Microbiology', 'Music Education',
          'Obstetrics and Gynaecology', 'OperationsResearch', 'Pacific Studies', 'Paediatrics',
          'Paediatrics?', 'Pharmacology', 'Property', 'Theology', 'Anatomy and Radiology',
          'Art Histry', 'Biology and Environmental Science', 'Biology Sciences',
          'Business and Economics', 'Chemicals &amp; Materials Engineering', 'chemistry',
          'Commerce', 'Computer System Engineering', 'Criminology', 'Educational Psychology',
          'Education and English', 'Education (Applied Linguistics)', 'Electrical and Computer',
          'Electrical and Computing Engineering', 'English (Drama)', 'Environmental Engineering',
          'Environmental Management', 'Environmental Studies', 'Epidemiology',
          'Fine Arts and Dance Studies', 'French', 'German', 'Healthcare Quality',
          'Health Sciences and Medicine', 'Health Science', 'Māori and Pacific Health', 
          'Information Systems and Operations Management', 'Latin', 'Maori and Pacific Health',
          'Marine Biology', 'Mechatronics', 'Media, Film and Television Studies', 'Medical History',
          'Medical Science', 'Musical Arts', 'Nutrition', 'Oncology', 'Paediatric Endocrinology', 
          'Operations and Supply Chain Management', 'Operations Research,', 'Paediatric Medicine',
          'Pharmacology and Clinical Pharmacology', 'Political Studies', 'Psychological Medicine',
          'Public Health', 'Social work', 'Statistics and Marine Science', 'Translation Studies',
          'Accounting and Finance', 'Anatomy and Medical Imaging', 'Applied Chinese Linguistics',
          'Bioinformatics', 'Chemical Engineering', 'Education and Population Health',
          'Exercise Science', 'Film, Television and Media Studies', 'Film, Television and Media',
          'Information System and Operations Management', 'Language Teaching and Learning',
          'Medical and Health Science', 'Medical Education', 'Molecular Medicine Pathology',
          'Chemical and Mateirals Engineering', 'Musicology', 'PhD Education',
          'Obstetrics', 'Phamacy', 'Sport and Exercise Science', 'Translation and Interpretin']
recs = []
prerecs = []
for page in range(pages):        
    tocurl = 'https://researchspace.auckland.ac.nz/handle/2292/2/discover?rpp=' + str(rpp) + '&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        time.sleep(4)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'keyw' : [], 'note' : []}
                rec['tit'] = a.text.strip()
                rec['link'] = 'https://researchspace.auckland.ac.nz' + a['href']
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                prerecs.append(rec)

i = 0
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']+'?show=full'), features="lxml")
        time.sleep(4)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']+'?show=full'), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            elif meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'] += re.split('; ', meta['content'])
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']

    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        tdt = ''
        for td in tr.find_all('td'):
            if td.has_attr('class') and 'label-cell' in td['class']:
                tdt = td.text.strip()
            else:
                if tdt == 'dc.contributor.advisor':
                    sv = td.text.strip()
                    if sv != 'en':
                        rec['supervisor'].append([sv])
                elif tdt == 'thesis.degree.discipline':
                    disc = td.text.strip()
                    if disc in boring:
                        keepit = False
                    else:
                        rec['note'].append(disc)
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
