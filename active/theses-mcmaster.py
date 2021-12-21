# -*- coding: utf-8 -*-
#harvest theses McMaster U.
#FS: 2021-01-08

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
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'McMaster U.'
jnlfilename = 'THESES-MCMASTER-%s' % (stampoftoday)

rpp = 100
pages = 2

boringdeps = ['Global Health', 'Religion', 'Biology', 'Electrical and Computer Engineering', 'Medical Sciences',
              'Biomedical Engineering', 'Chemical Engineering', 'Chemistry and Chemical Biology', 'Chemistry',
              'Classics', 'Earth and Environmental Sciences', 'Geography', 'Health Research Methodology',
              'Christian Studies', 'Christian Theology', 'Education', 'Geochemistry', 'Geography and Geology',
              'Geology', 'Health Care Research Methods',
              'Health Sciences', 'Kinesiology', 'Labour Studies', 'Mechanical Engineering', 'Religious Studies',
              'Anthropology', 'Biochemistry and Biomedical Sciences', 'Biochemistry', 'Civil Engineering',
              'Clinical Epidemiology/Clinical Epidemiology & Biostatistics', 'eHealth', 'Health Policy',
              'Cognitive Science of Language', 'Statistics',
              #'Computational Engineering and Science', 'Computing and Software',
              'Engineering Physics', 'French', 'Geography and Earth Sciences', 'Health and Aging',
              'Materials Science and Engineering', 'Materials Science', 'Neuroscience', 'Philosophy',
              'Biomechanics', 'Classical Studies', 'Communications Management', 'Environmental Science', 
              'Political Science - International Relations', 'Political Science', 'Social Work', 'Sociology',
              'Medical Sciences (Blood and Cardiovascular)', 'Medical Sciences (Cell Biology and Metabolism)',
              'Medical Sciences (Division of Physiology/Pharmacology)', 'Rehabilitation Science',
              'Medical Sciences (Molecular Virology and Immunology Program)', 'Nursing', 'Psychology',
              'Business', 'Chemical Biology', 'Clinical Epidemiology/Clinical Epidemiology & Biostatistics',
              'Clinical Health Sciences (Health Research Methodology)',
              #'Computer Science',
              'Electrical Engineering', 'English and Cultural Studies', 'Health Science Education', 'History',
              'Radiation Sciences (Medical Physics/Radiation Biology)', 'Software Engineering',
              'Adapted Human Biodynamics', 'Astrophysics', 'Behavioural Endocrinology',
              'Biblical Studies, Religion', 'Church History/Christian Interpretation', 'Church History',
              'Clinical Health Sciences (Nursing)', 'Divinity College', 'Health Geography', 'Health',
              'Literature', 'Management Science/Information Systems', 'Management Science/Systems',
              'Medical Sciences, Division of Physiology/Pharmacology', 'Physiology and Pharmacology', 
              'Medical Sciences (Neuroscience and Behavioral Science)', 'Political Economy',
              'Romance Languages', 'Roman Studies', 'School of the Arts',
              'Molecular Immunology, Virology and Inflammation', 'Music Criticism', 'Music', 'Neurosciences', 
              'Business Administration', 'Earth Sciences', 'Economics', 'Engineering', 'English',
              'Health and Radiation Physics', 'Materials Engineering', 'Medical Physics', 'Religious Sciences',
              'Medical Sciences (Growth and Development)', 'Medical Sciences (Neurosciences)', 'Medicine',
              'Engineering Physics and Nuclear Engineering', 'Finance', 'Metallurgy and Materials Science',
              'Mechanical and Manufacturing Engineering', 'School of Geography and Geology', 'Work and Society',
              'Medical Sciences (Clinical Epidemiology and Health Care Research)',
              'Medical Sciences (Thrombosis & Haemostasis & Atherosclerosis)', 'Humanities']

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://macsphere.mcmaster.ca/handle/11375/272/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(page*rpp) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    try:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    except:
        print ' try again in 20s...'
        time.sleep(20)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    divs = tocpage.body.find_all('td', attrs = {'headers' : 't2'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://macsphere.mcmaster.ca' + a['href']
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)
    time.sleep(5)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(2)
    except:
        try:
            print "   retry %s in 15 seconds" % (rec['artlink'])
            time.sleep(15)
            req = urllib2.Request(rec['artlink'], headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        except:
            print "   no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
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
    if not 'date' in rec.keys():
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'DCTERMS.dateAccepted'}):
            rec['date'] = meta['content']
            rec['note'].append('date from DCTERMS.dateAccepted')
    if not 'autaff' in rec.keys():
        rec['autaff'] = [[ 'Doe, John' ]]
    rec['autaff'][-1].append(publisher)
    for tr in artpage.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
            tdfl = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue'}):
            #supervisor
            if re.search('Advisor', tdfl):
                for a in td.find_all('a'):
                    rec['supervisor'].append([a.text.strip()])
            elif re.search('Department', tdfl):
                dep = td.text.strip()
                if dep in boringdeps:
                    keepit = False
                else:
                    rec['note'].append(dep)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            for div in artpage.find_all('div', attrs = {'class' : 'panel-info'}):
                divt = re.sub('[\n\t\r]', ' ', div.text.strip())
                if re.search('Open Access', divt):
                    rec['hidden'] = rec['pdf_url']
    if keepit:
        recs.append(rec)
        print '   ', rec.keys()

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
