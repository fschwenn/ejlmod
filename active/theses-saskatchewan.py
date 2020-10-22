# -*- coding: utf-8 -*-
#harvest theses from Saskatchewan U.
#FS: 2020-09-25

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

publisher = 'Saskatchewan U.'

rpp = 50
pages = 5+25
boring = ['Chemistry', 'Veterinary Biomedical Sciences', 'English', 'Educational Foundations',
          'History', 'School of Environment and Sustainability', 'Soil Science',
          'Agricultural and Resource Economics', 'Archaeology and Anthropology',
          'Biomedical Engineering', 'Chemical and Biological Engineering',
          'Educational Administration', 'Electrical and Computer Engineering',
          'Interdisciplinary Centre for Culture and Creativity', 'Interdisciplinary Studies',
          'Johnson-Shoyama Graduate School of Public Policy', 'Nursing', 'Pharmacology',
          'School of Public Health', 'Veterinary Pathology', 'Toxicology Centre',
          'Animal and Poultry Science', 'Biology', 'Civil and Geological Engineering',
          'Community Health and Epidemiology', 'Geography and Planning',
          'Large Animal Clinical Sciences', 'Law', 'Mechanical Engineering', 'Medicine',
          'Microbiology and Immunology', 'Psychology', 'Sociology', 'Veterinary Microbiology',
          'Anatomy and Cell Biology', 'Art and Art History', 'Biochemistry', 'Curriculum Studies',
          'Food and Bioproduct Sciences', 'Geological Sciences', 'Kinesiology',
          'Bioresource Policy, Business and Economics', 'Environmental Engineering',
          'Nutrition', 'Pathology and Laboratory Medicine', 'Western College of Veterinary Medicine',
          'Pharmacy and Nutrition', 'Physiology', 'Plant Sciences', 'School of Physical Therapy']
boring += ['Master of Science (M.Sc.)', 'Master of Education (M.Ed.)', 'Master of Arts (M.A.)',
           'Master of Nursing (M.N.)', 'Master of Public Policy (M.P.P.)',
           'Master of Laws (LL.M.)', 'Master of Fine Arts (M.F.A.)']

jnlfilename = 'THESES-SASKATCHEWAN-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://harvest.usask.ca/handle/10388/381/discover?sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&page=' + str(page+1)
    print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://harvest.usask.ca' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
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
                if re.search('\d{4}\-\d{4}\-', meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                else:
                    rec['autaff'] = [[  meta['content'] ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split('[,;] ', meta['content']):
                    rec['keyw'].append(re.sub('\.$', '', keyw))
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    rec['autaff'][-1].append(publisher)
    for div in artpage.body.find_all('div', attrs = {'class' : 'table'}):
        for h5 in div.find_all('h5'):
            h5t = h5.text.strip()
            h5.decompose()
            #degree
            if h5t == 'Degree':
                rec['degree'] = div.text.strip()
                rec['note'].append(rec['degree'])
                if rec['degree'] in boring:
                    print '   skip "%s"' % (rec['degree'])
                    keepit = False
            #Department
            elif h5t == 'Department':
                rec['department'] = div.text.strip()
                rec['note'].append(rec['department'])
                if rec['department'] in boring:
                    print '   skip "%s"' % (rec['department'])
                    keepit = False
            #supervisor
            elif h5t == 'Supervisor':
                for span in div.find_all('span'):
                    for sv in re.split('; ', span.text.strip()):
                        if re.search('@', sv):
                            email = re.sub('.* (.*?@[\w\.]+).*', r'EMAIL:\1', sv)
                            sv = re.sub(' .*?@.*', '', sv)
                            rec['supervisor'].append([sv, email])
                        else:
                            rec['supervisor'].append([sv])
    if keepit:
        print'  ', rec.keys()
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
