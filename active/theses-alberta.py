# -*- coding: utf-8 -*-
#harvest theses from Alberta U.
#FS: 2020-05-13

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

publisher = 'Alberta U.'
pages = 20

boringdegrees = ['Master of Science', 'Master of Arts/Master of Library and Information Studies',
                 'Master of Arts', 'Master of Education', 'Master of Nursing', 'Master of Laws',
                 'Master of Library and Information Studies', 'Masters of Science']
boringdepartments = ['Department of Civil and Environmental Engineering',
                     'Comparative Literature', 'Neuroscience', 'Department of Anthropology',
                     'Department of Biological Sciences', 'Department of Educational Psychology',
                     'Department of Computing Science', 'Department of East Asian Studies',
                     'Department of Linguistics', 'Department of Music', 'Department of Sociology',
                     'Department of Surgery', 'Digital Humanities', 'Department of English and Film Studies',
                     'Faculty of Pharmacy and Pharmaceutical Sciences', 'Faculty of Rehabilitation Medicine',
                     'Department of Physiology', 'Department of Agricultural, Food, and Nutritional Science',
                     'Department of Biochemistry', 'Department of Cell Biology',
                     'Department of Chemical and Materials Engineering', 'Department of Chemistry',
                     'Department of Earth and Atmospheric Sciences', 'Department of Economics',
                     'Department of Educational Policy Studies', 'Department of Mechanical Engineering',
                     'Department of Electrical and Computer Engineering', 'Department of Elementary Education',
                     'Department of History and Classics', 'Department of Laboratory Medicine and Pathology',
                     'Department of Medical Microbiology and Immunology', 'Department of Medicine',
                     'Department of Modern Languages and Cultural Studies', 'Department of Pharmacology',
                     'Department of Political Science', 'Department of Psychology',
                     'Department of Public Health Sciences', 'Department of Renewable Resources',
                     'Department of Resource Economics and Environmental Sociology',
                     'Department of Secondary Education', 'Department of Secondary Education',
                     'Faculty of Business', 'Faculty of Kinesiology, Sport, and Recreation',
                     'Faculty of Nursing', 'Medical Sciences-Laboratory Medicine and Pathology',
                     'Department of Biological Sciences Department of Chemical and Materials Engineering',
                     'Department of Chemical and Materials Engineering Department of Laboratory Medicine and Pathology',
                     'Department of Oncology', 'Department of Philosophy', 'Faculty of Law',
                     'School of Public Health', 'Medical Sciences-Paediatrics',
                     'Department of Biomedical Engineering', 'Centre for Neuroscience',
                     'Department of Chemical and Materials Engineering Department of Biomedical Engineering Department of Biomedical Engineering',
                     'Department of Chemical and Materials Engineering Department of Biomedical Engineering',
                     'Department of Chemical and Materials Engineering Department of Human Ecology',
                     'Department of Earth and Atmospheric Sciences Medical Sciences-Paediatrics',
                     'Department of Educational Studies', 'Department of Human Ecology',
                     'Department of Secondary Education Faculty of Extension',
                     'Faculty of Kinesiology, Sport, Recreation', 'Religious Studies',
                     'Faculty of Physical Education and Recreation Department of Drama',
                     'Faculty of Physical Education and Recreation', 'Kinesiology, Sport and Recreation',
                     'Laboratory Medicine and Pathology', 'Medical Sciences-Dentistry',
                     'Medical Sciences-Medical Genetics', 'Physical Education and Recreation',
                     'Department of Elementary Education School of Library and Information Studies',
                     'Department of Modern Languages and Cultural Studies Department of Anthropology',
                     'Department of Psychiatry', 'Department of Sociology Department of Art and Design',
                     'Medical Sciences-Orthodontics', 'Medical Sciences-Shantou in Laboratory Medicine and Pathology',
                     'School of Library and Information Studies',
                     'Department of Agricultural, Food, and Nutritional Science Department of Public Health Sciences',
                     'Department of History and Classics Department of Modern Languages and Cultural Studies',
                     'Medical Sciences- Laboratory Medicine and Pathology',
                     'Centre for Neuroscience Physical Education and Recreation',
                     'Faculty of Nursing Department of Public Health Sciences',
                     'School Public Health Sciences', 'Drama Department',
                     'Medical Sciences-Biomedical Engineering', 'School of Public Health Sciences',
                     'Rehabilitation Medicine', 'Medicine', 'Rural Economy', 'School of Business', 
                     'Department of Mathematical and Statistical Sciences', 
                     'Department of Agricultural, Food and Nutritional Science']

jnlfilename = 'THESES-ALBERTA-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
recs = []
for page in range(pages):
    tocurl = 'https://era.library.ualberta.ca/search?direction=desc&facets[member_of_paths_dpsim][]=db9a4e71-f809-4385-a274-048f28eb6814%2Ff42f3da6-00c3-4581-b785-63725c33c7ce&search=&sort=sort_year&page=' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'media-body'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        for h3 in div.find_all('h3'):
            for a in h3.find_all('a'):
                rec['artlink'] = 'https://era.library.ualberta.ca' + a['href']
                prerecs.append(rec)
    time.sleep(5)

i = 0
dois = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = re.sub('^doi:', '', meta['content'])
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    #abstract
    for p in artpage.body.find_all('p', attrs = {'title' : 'Description / Abstract'}):
        rec['abs'] = p.text.strip()
    for dl in artpage.body.find_all('dl'):
        for dt in dl.find_all('dt'):
            dtt = dt.text.strip()
            for dd in dl.find_all('dd'):
                #keywords
                if dtt == 'Subjects / Keywords':
                    for li in dd.find_all('li'):
                        rec['keyw'].append(li.text.strip())
                #degree
                elif dtt == 'Degree':
                    rec['degree'] = dd.text.strip()
                    rec['note'].append(dd.text.strip())
                #license
                elif dtt == 'License':
                    for a in dd.find_all('a'):
                        if re.search('creativecommons.org', a['href']):
                            rec['license'] = {'url' :  a['href']}
                #department
                elif dtt == 'Department':
                    rec['department'] = re.sub('  +', ' ', re.sub('[\n\t\r]', ' ', dd.text.strip()))
                    rec['note'].append(rec['department'])
                #supervisor
                elif dtt == 'Supervisor / co-supervisor and their department(s)':
                    for a in dd.find_all('a'):
                        rec['supervisor'].append([re.sub(' \(.*', '', a.text.strip())])
    #handle fulltext depending on license
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    #cherry picking
    if 'department' in rec.keys() and rec['department'] in boringdepartments:
        print '  skip "%s"' % (rec['department'])
    else:
        if 'degree' in rec.keys() and rec['degree'] in boringdegrees:
            print '  skip "%s"' % (rec['degree'])
        else:
            if not 'doi' in rec.keys():
                rec['doi'] = '20.2000/Alberta/' + re.sub('.*items\/', '', rec['artlink'])
                rec['link'] = rec['artlink']
            if not rec['doi'] in dois:
                dois.append(rec['doi'])
                print '  ', rec.keys()
                recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
