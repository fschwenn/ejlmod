# -*- coding: utf-8 -*-
#harvest theses from Virginia Tech., Blacksburg
#FS: 2020-05-29


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

publisher = 'Virginia Tech., Blacksburg'

typecode = 'T'

jnlfilename = 'THESES-VTECH-%sF' % (stampoftoday)
rpp = 50
pages = 4

boringdisciplines = ['Mechanical Engineering', 'Engineering Education', 'Biological Sciences',
                     'Civil Engineering', 'Computer Science and Applications', 'Electrical Engineering',                     
                     'Engineering Mechanics', 'Plant Pathology, Physiology and Weed Science',
                     'Accounting and Information Systems', 'Aerospace Engineering',
                     'Agricultural and Extension Education', 'Animal and Poultry Sciences',
                     'Architecture and Design Research', 'Biomedical and Veterinary Sciences',
                     'Biomedical Engineering', 'Chemical Engineering', 'Chemistry',
                     'Computer Engineering', 'Counselor Education', 'Crop and Soil Environmental Sciences',
                     'Curriculum and Instruction', 'Educational Leadership and Policy Studies',
                     'Educational Research and Evaluation', 'Environmental Design and Planning',
                     'Fisheries and Wildlife Science', 'Food Science and Technology',
                     'Human Development', 'Industrial and Systems Engineering',
                     'Materials Science and Engineering', 'Mining Engineering', 'Psychology',
                     'Public Administration/Public Affairs', 'Biochemistry',
                     'Social, Political, Ethical, and Cultural Thought',
                     'Biological Systems Engineering', 'Business, Finance',
                     'Economics, Agriculture and Life Sciences',
                     'Genetics, Bioinformatics, and Computational Biology',
                     'Geosciences', 'Geospatial and Environmental Analysis',
                     'Horticulture', 'Human Nutrition, Foods, and Exercise',
                     'Leadership and Social Change', 'Nuclear Engineering',
                     'Planning, Governance, and Globalization', 'Rhetoric and Writing',
                     'Science and Technology Studies', 'Translational Biology, Medicine and Health',
                     'Agricultural, Leadership, and Community Education', 'Animal Sciences, Dairy',
                     'Business, Business Information Technology', 'Business, Management',
                     'Business, Marketing', 'Career and Technical Education',
                     'Economics, Science', 'Economics', 'Entomology', 'Forest Products',
                     'Forestry', 'Genetics, Bioinformatics and Computational Biology',
                     'Higher Education','Hospitality and Tourism Management',
                     'Macromolecular Science and Engineering',
                     'Plant Pathology, Physiology, and Weed Science',
                     'Public Administration and Public Affairs', 'Sociology']

boringdegrees = []

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://vtechworks.lib.vt.edu/handle/10919/11041/discover?sort_by=dc.date.issued_dt&order=desc&filtertype=etdlevel&filter_relational_operator=equals&filter=doctoral&rpp=' + str(rpp) + '&page=' + str(page+1)
    print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://vtechworks.lib.vt.edu' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)
    time.sleep(3)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
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
            if meta['name'] == 'DC.creator':
                if re.search('\d{4}\-\d{4}\-', meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                else:
                    author = re.sub(', \d+.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    rec['autaff'][-1].append(publisher)
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            word = td.text.strip()
        if label == 'dc.rights':
            rec['note'].append(word)
            rec['rights'] = word
        elif label == 'dc.description.degree':
            if word != 'Doctor of Philosophy':
                rec['note'].append(word)
                rec['degree'] = word
        elif label == 'thesis.degree.discipline':
            rec['note'].append(word)
            rec['discipline'] = word
    skipit = False
    if 'discipline' in rec.keys() and rec['discipline'] in boringdisciplines:
        print '    skip', rec['discipline']
        skipit = True
    if not skipit and 'degree' in rec.keys() and rec['degree'] in boringdegrees:
        print '    skip', rec['degree']
        skipit = True
    if not skipit:
        recs.append(rec)


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
