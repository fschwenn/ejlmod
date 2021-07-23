# -*- coding: utf-8 -*-
#harvest theses from Kansas U.
#FS: 2021-01-05

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Kansas U.'

jnlfilename = 'THESES-KANSAS_U-%s' % (stampoftoday)
rpp = 50
pages = 4

boringdisciplines = ['Nursing', 'Bioengineering', 'Civil, Environmental & Architectural Engineering',
                     'Aerospace Engineering', 'Biostatistics', 'Electrical Engineering & Computer Science',
                     'English', 'Mechanical Engineering', 'Molecular Biosciences', 'Music',
                     'Pharmaceutical Chemistry', 'Physical Therapy & Rehabilitation Sciences',
                     'Slavic Languages & Literatures', 'Anthropology', 'Chemical & Petroleum Engineering',
                     'Chemistry', 'Curriculum and Teaching', 'Dietetics & Nutrition', 'Geology',
                     'Psychology', 'Geography', 'Psychology & Research in Education',
                     'History of Art', 'Clinical Child Psychology', 'Counseling Psychology',
                     'Hearing and Speech', 'Applied Behavioral Science', 'American Studies',
                     'Public Administration', 
                     'Film & Media Studies', 'Communication Studies', 'Economics', 'Theatre',
                     'Ecology & Evolutionary Biology', 'Educational Leadership and Policy Studies',
                     'Health, Sport and Exercise Sciences', 'Medicinal Chemistry', 'Anthropology',
                     'Chemical & Petroleum Engineering', 'Chemistry', 'Curriculum and Teaching',
                     'Dietetics & Nutrition', 'Ecology & Evolutionary Biology', 'Geology', 'Social Welfare'
                     'Educational Leadership and Policy Studies', 'Health, Sport and Exercise Sciences',
                     'Medicinal Chemistry', 'Microbiology, Molecular Genetics & Immunology',
                     'Music Education & Music Therapy', 'Neurosciences', 'Pathology & Laboratory Medicine', 
                     'Microbiology, Molecular Genetics & Immunology', 'Music Education & Music Therapy',
                     'Neurosciences', 'Pathology & Laboratory Medicine', 'Social Welfare']
boringdegrees = []

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://kuscholarworks.ku.edu/handle/1808/1952/discover?sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&page=' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://kuscholarworks.ku.edu' + a['href'] + '?show=full'
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
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d\d', meta['content']):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', meta['content'])
    rec['autaff'][-1].append(publisher)
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            word = td.text.strip()
        #License
        if label == 'dc.rights':
            rec['note'].append(word)
            rec['rights'] = word
        #Degree
        elif label == 'dc.thesis.degreeLevel':
            if word != 'Doctor of Philosophy':
                rec['note'].append(word)
                rec['degree'] = word
        #Discipline
        elif label == 'dc.thesis.degreeDiscipline':
            rec['note'].append(word)
            rec['discipline'] = word
        #ORCID
        elif label == 'dc.identifier.orcid':
            rec['autaff'][-1].append(re.sub('.*\/', 'ORCID:', word))
        #supervisor
        elif label == 'dc.contributor.advisor':
            rec['supervisor'].append([word])
    rec['autaff'][-1].append(publisher)
    skipit = False
    if 'discipline' in rec.keys() and rec['discipline'] in boringdisciplines:
        print '    skip', rec['discipline']
        skipit = True
    if not skipit and 'degree' in rec.keys() and rec['degree'] in boringdegrees:
        print '    skip', rec['degree']
        skipit = True
    if not skipit:
        recs.append(rec)
        print '   ', rec.keys()

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
