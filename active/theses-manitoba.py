# -*- coding: utf-8 -*-
#harvest theses from Manitoba U.
#FS: 2020-08-25
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'THESES-MANITOBA-%s' % (stampoftoday)

publisher = 'Manitoba U.'

hdr = {'User-Agent' : 'Magic Browser'}

rpp = 50
pages = 10
boringdisciplines = ['Pharmacology and Therapeutics', 'Disability Studies', 'History',
                     'Educational Administration, Foundations and Psychology',
                     'Political Studies', 'Psychology', 'Religion', 'School of Art', 'Soil Science',
                     'Biomedical Engineering', 'Biosystems Engineering', 'Chemistry', 'Economics',
                     'English, Film, and Theatre', 'Food and Human Nutritional Sciences',
                     'Geological Sciences', 'Natural Resources Institute', 'Oral Biology',
                     'Peace and Conflict Studies', 'Preventive Dental Science', 'Sociology',
                     'Applied Health Sciences', 'Civil Engineering', 'Social Work', 'Animal Science',
                     'Anthropology', 'Biological Sciences', 'City Planning',
                     'Community Health Sciences', 'Education', 'Electrical and Computer Engineering',
                     'Entomology', 'Environment and Geography', 'Human Anatomy and Cell Science',
                     'Human Nutritional Sciences', 'Law', 'Management', 'Mechanical Engineering',
                     'Medical Microbiology and Infectious Diseases', 'Microbiology',
                     'Native Studies', 'Nursing', 'Pharmacy', 'Physiology and Pathophysiology',
                     'Plant Science', 'Biochemistry and Medical Genetics', 'Business Administration',
                     'Cancer Control', 'Curriculum, Teaching and Learning', 'English, Theatre, Film and Media'
                     'Agribusiness and Agricultural Economics', 'Food Science',
                     'Medical Microbiology', 'Accounting and Finance', 'Architecture',
                     'English', 'Family Social Sciences', 'History (Archival Studies)',
                     'Interior Design', 'Kinesiology and Recreation Management',
                     'Landscape Architecture', 'Management/Business Administration',
                     'Mechanical and Manufacturing Engineering', 'Pathology', 'Physiology',
                     'Food and Nutritional Sciences', 'French, Spanish and Italian', 'Immunology',
                     'Interdisciplinary Program', 'Linguistics', 'Natural Resources Management']

boringdegrees = ['Master of Science (M.Sc.)', 'Master of Arts (M.A.)',  'Master of Education (M.Ed.)',
                 'Master of Fine Art (M.F.A.)',  'Master of Interior Design (M.I.D.)',
                 'Master of Landscape Architecture (M.Land.Arch.)',  'Master of Dentistry (M. Dent.)',
                 'Master of Natural Resources Management (M.N.R.M.)', 'Master of Nursing (M.N.)',
                 'Master of Social Work (M.S.W.)', 'Master of City Planning (M.C.P.)',
                 'Master of Mathematical, Computational and Statistical Sciences (M.M.C.S.S.)',
                 'Master of Laws (LL.M.)', 'Bachelor of Science (B.Sc.)']


inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
for page in range(pages):
    tocurl = 'https://mspace.lib.umanitoba.ca/xmlui/handle/1993/6/discover?rpp='+str(rpp)+'&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        new = True
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : []}
        for span in div.find_all('span', attrs = {'class' : 'date'}):
            if re.search('[12]\d\d\d', span.text):
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                if int(rec['year']) < now.year - 2:
                    new = False
                    print '  skip',  rec['year']
        if new:
            for a in div.find_all('a'):
                if re.search('handle', a['href']):
                    rec['artlink'] = 'https://mspace.lib.umanitoba.ca' + a['href'] + '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    if not rec['hdl'] in uninterestingDOIS:
                        prerecs.append(rec)
    time.sleep(2)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['content']:
                    rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split('[,;] ', meta['content']):
                    if not re.search('^info.eu.repo', keyw):
                        rec['keyw'].append(keyw)
    for tr in artpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            tdt = td.text.strip()
            td.decompose()
        for td in tr.find_all('td'):
            if td.text.strip() == 'en_US':
                continue
            #supervisor
            if tdt == 'dc.contributor.supervisor':
                rec['supervisor'] = [[ re.sub(' \(.*', '', td.text.strip()) ]]
            #discipline
            elif tdt == 'dc.degree.discipline':
                discipline = td.text.strip()
                if discipline in boringdisciplines:
                    print '  skip "%s"' % (discipline)
                    keepit = False
                else:
                    rec['note'].append(discipline)
            #degree
            elif tdt == 'dc.degree.level':
                degree = td.text.strip()
                if degree in boringdegrees:
                    print '  skip "%s"' % (degree)
                    keepit = False
                else:
                    rec['note'].append(degree)
    if keepit:
        recs.append(rec)
        print '  ', rec.keys()
    else:
        newuninterestingDOIS.append(rec['hdl'])
                
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'),'utf8')
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

