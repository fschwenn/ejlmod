# -*- coding: utf-8 -*-
#harvest theses from North Carolina State U.
#FS: 2021-09-07

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'North Carolina State U.'

rpp = 100
pages = 2

hdr = {'User-Agent' : 'Firefox'}
jnlfilename = 'THESES-NCSU-%s' % (stampoftoday)

boringdisciplines = ['Mechanical Engineering', 'Electrical Engineering', 'Biology', 'Biomedical Engineering',
                     'Chemical Engineering', 'Civil Engineering', 'Educational Adm & Supervision',
                     'Fish, Wildlife, and Con Bio', 'Forestry and Environmental Res', 'Horticultural Science',
                     'Psychology', 'Aerospace Engineering', 'Chemistry', 'Comm, Rhetoric & Digital Media',
                     'Computer Engineering', 'Economics', 'Ed Leadership Policy Human Dev',
                     'Fiber & Polymer Science', 'Food Science', 'Forest Biomaterials', 'Genetics',
                     'Learning and Teaching in STEM', 'Material Science & Engineering', 'Public History',
                     'Sociology', 'Soil Science', 'Statistics', 'Teacher Educ and Learning Sci',
                     'Materials Science & Engineering', 'Plant Biology', 'Plant Pathology',
                     'Animal Sci & Poultry Sci', 'Bioinformatics', 'Biological & Agri Engineering',
                     'Applied Mathematics', 'Counseling & Counselor Educ', 'Crop Science',
                     'Ed Research & Policy Analysis', 'Mathematics Education', 'Microbiology',
                     'Adult and Community College Education', 'Adult and Higher Education',
                     'Agricultural and Extension Education', 'Agricultural Education', 'Animal and Poultry Science',
                     'Animal SciencePoultry ScienceFunctional Genomics', 'Animal SciencePoultry Science',
                     'Animal Science', 'Biochemistry', 'BioinformaticsStatistics', 'Botany', 'ChemistryStatistics',
                     'Comm Rhetoric & Digital Media', 'Communication, Rhetoric, and Digital Media',
                     'Comparative Biomedical Sciences',
                     #'Computer ScienceComputer Science', 'Computer Science',
                     'Counseling and Counselor Education', 'Counselor Education', 'Curriculum and Instruction',
                     'Curriculum Studies', 'EconomicsStatistics', 'EdD', 'Educational Administration and Supervision',
                     'Educational Psychology', 'Educational Research and Policy Analysis', 'Engineering',
                     'Extension Education', 'Fiber and Polymer ScienceBiomedical Engineering',
                     'Fiber and Polymer ScienceElectrical Engineering', 'ForestryNatural Resources', 'Forestry',
                     'Functional Genomics', 'Geospatial Analytics', 'Higher Education Administration', 'Immunology',
                     'Industrial EngineeringIndustrial Engineering', 'Marine, Earth and Atmospheric Sciences',
                     'Materials Science and Engineering', 'Math, Science and Technology Education',
                     'NutritionAnimal Science', 'Occupational Education', 'Operations ResearchComputer Science',
                     'Operations ResearchElectrical Engineering', 'Parks, Recreation and Tourism Management',
                     'Physiology', 'Plant PathologyCrop Science', 'Poultry Science', 'School Counseling',
                     'Technology Education', 'Textiles', 'Training and Development', 'Wood and Paper Science',
                     'Fiber and Polymer ScienceWood and Paper Science', 'Fisheries and Wildlife Sciences',
                     'Fisheries, Wildlife, and Conservation Biology', 'Forestry and Environmental Resources', 
                     'Fiber and Polymer ScienceMaterials Science and Engineering', 'Fiber and Polymer Science', 
                     'Curriculum and Instruction, English Education', 'Curriculum and Instruction, Reading', 
                     'Biological and Agricultural Engineering', 'Biomedical EngineeringFiber and Polymer Science',                     
                     'Science Education', 'Biomathematics', 'Comm, Rhetoric & Digital Media',
                     'Comparative Biomedical Sci', 'Nutrition', 'Parks, Rec and Tourism Mgmt',
                     'Curriculum & Instruction', 'Design', 'Entomology', 'Fiber & Polymer Science',
                     'Industrial Engineering', 'Marine, Earth & Atmos Sciences', 'Zoology',
                     'Material Science & Engineering', 'Materials Science & Engineering',
                     'Operations Research', 'Public Administration', 'Toxicology', 'Textile Technology Management']
boringdegrees = ['Doctor+of+Education', 'Master+of+Science']

prerecs = []
for page in range(pages):
    tocurl = 'https://repository.lib.ncsu.edu/handle/1840.20/24/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    tocfilename = '/tmp/NCSU.%s.%04i.html' % (stampoftoday, page)
    if not os.path.isfile(tocfilename):
        os.system('wget -q -O  %s "%s"' % (tocfilename, tocurl))
        time.sleep(5)
    inf = open(tocfilename, 'r')
    tocpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for span in div.find_all('span', attrs = {'class' : 'Z3988'}):
            degree = re.sub('.*?rft.degree=(.*?)\&.*', r'\1', re.sub('[\n\t\r]', '', span['title']))
            if not degree in boringdegrees:
                rec['note'].append(degree)
                for a in div.find_all('a'):
                    rec['link'] = 'https://repository.lib.ncsu.edu' + a['href']# + '?show=full'
                    rec['doi'] = '20.2000/NCSU/' + re.sub('\D', '', a['href'])
                    prerecs.append(rec)
    print '   %i recs so far' % (len(prerecs))

recs = []
i = 0
for rec in prerecs:
    discipline = False
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    artfilename = '/tmp/NCSU.%s.thesis' % (re.sub('\D', '', rec['link']))
    if not os.path.isfile(artfilename):
        os.system('wget -q -O %s "%s"' % (artfilename, rec['link']))
        time.sleep(5)
    inf = open(artfilename, 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
                rec['autaff'][-1].append(publisher)
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
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
    for tr in artpage.body.find_all('tr'):
        tdt = False
        for td in tr.find_all('td'):
            if tdt:
                if tdt == 'Discipline:':
                    discipline = td.text.strip()
                    tdt == False
            else:
                for span in td.find_all('span', attrs = {'class' : 'bold'}):
                    tdt = span.text.strip()
    if discipline and discipline in boringdisciplines:
        print '  skip', discipline
    else:
        rec['note'].append(discipline)
        recs.append(rec)
        print '  ', rec.keys()

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

