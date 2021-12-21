# -*- coding: utf-8 -*-
#harvest theses from Arizona U.
#FS: 2021-03-20

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Arizona U.'
jnlfilename = 'THESES-ARIZONA_U-%s' % (stampoftoday)

#~ 500 pro Jahr
rpp = 50
pages = 4

boring = ['Ecology & Evolutionary Biology', 'Pharmaceutical Sciences', 'Accounting',
          'Anthropology', 'Biomedical Engineering', 'Chemistry', 'Geography',
          'Electrical & Computer Engineering', 'Environmental Health Sciences',
          'Information', 'Language, Reading & Culture', 'Management', 'Medical Sciences',
          'Neuroscience', 'Pharmacology & Toxicology', 'Philosophy', 'Psychology',
          'Public Health', 'Sociology', 'East Asian Studies', 'Geosciences', 'Nursing',
          'American Indian Studies', 'Biosystems Engineering', 'Cancer Biology',
          'Epidemiology', 'Linguistics', 'Middle Eastern and North African Studies',
          'Molecular & Cellular Biology', 'Physiological Sciences', 'Communication',
          'Agricultural & Biosystems Engineering', 'Civil Engineering', 'Engineering',
          'Family & Consumer Sciences', 'Gender & Women\'s Studies',
          'Gender & Women’s Studies', 'Genetics', 'Immunobiology', 'Plant Pathology',
          'Spanish', 'Entomology and Insect Science', 'Natural Resources',
          'Second Language Acquisition and Teaching', 'Management Information Systems',
          'English', 'Biochemistry', 'Civil Engineering & Engineering Mechanics',
          'German Studies', 'Hydrometeorology', 'Library & Information Science',
          'Materials Science and Engineering', 'Special Education & Rehabilitation',
          'Systems and Industrial Engineering', 'Cellular and Molecular Medicine',
          'Civil Engineering and Engineering Mechanics', 'Materials Science & Engineering',
          'Nutritional Sciences', 'Rhetoric, Composition & the Teaching of English',
          'Aerospace Engineering', 'Animal Sciences', 'Gender & Women’s Studies',
          'Soil, Water and Environmental Science', 'Teaching & Teacher Education',
          'Middle Eastern & North African Studies', 'Agricultural & Biosystems Engineering',
          'Anthropology & Linguistics', 'Art History & Education', 'Atmospheric Sciences',
          'Biostatistics',
          #'Computer Science',
          'Educational Psychology', 'Music',
          'Environmental Engineering', "Gender & Women's Studies", 'History', 'Hydrology',
          'Mechanical Engineering', 'Rhetoric, Composition and Teaching of English',
          'School Psychology', 'Soil, Water & Environmental Science', 'Chemical Engineering',
          'Speech, Language and Hearing Sciences', 'Arid Lands Resource Sciences',
          'Clinical Translational Sciences', 'Economics', 'Educational Leadership & Policy',
          'Entomology & Insect Science', 'Health Behavior Health Promotion', 'Higher Education',
          'Mexican American Studies', 'Systems & Industrial Engineering', 'Medical Pharmacology',
          'Planetary Sciences', 'Plant Science', 'Second Language Acquisition & Teaching',
          'Arid Land Resource Science', 'Art History and Education', 'French',
          'Comparative Cultural & Literary Studies', 'Educational Policy Studies and Practice',
          'Geography & Development', 'Microbiology & Immunology', 'Public Administration',
          'Special Education, Rehabilitation and School Psychology', "Virchow's triad",
          "Women's Studies", 'Teaching, Learning and Sociocultural Studies',
          'Transcultural German Studies', 'Business Administration', 'Engineering Mechanics',
          'Rhetoric, Composition, and the Teaching of English', 'Audiology', 'Pathobiology',
          'Art Education', 'Biochemistry & Molecular Biophysics', 'Chemistry and Biochemistry',
          'Gender & Women’s Studies', 'History & Theory of Art', 'Near Eastern Studies',
          'Cell Biology & Anatomy', 'Statistics', 'Microbiology', 'Rehabilitation',
          'Mining Geological & Geophysical Engineering', 'Special Education', 'Political Science',
          'Educational Leadership',
          'Information Resources & Library Science', 'Insect Science', 'Art', 'Entomology',
          'Natural Resources and the Environment', 'Natural Resources Studies', 'Plant Sciences',
          'Government and Public Policy', 'Optical Sciences', 'Speech, Language, & Hearing Sciences']

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for j in range(pages):
    tocurl = 'https://repository.arizona.edu/handle/10150/129652/browse?order=DESC&rpp=' + str(rpp) + '&sort_by=2&etal=-1&offset=' + str(j*rpp) + '&type=dateissued'
    print '==={ %i/%i }==={ %s }===' % (j+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    relevant = 0
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
        for a in div.find_all('a'):
            rec['link'] = 'https://repository.arizona.edu' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)
    time.sleep(15)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    for tr in artpage.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            word = td.text.strip()
            #supervisor
            if label == 'dc.contributor.advisor':
                rec['supervisor'].append([word])
            #discipline
            elif label == 'thesis.degree.discipline':
                if word != 'Graduate College':
                    if word in boring:
                        print '    skip', word
                        keepit = False
                    else:
                        rec['note'].append('DISCIPLINE: %s' % (word))
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
