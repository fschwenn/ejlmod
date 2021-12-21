# -*- coding: utf-8 -*-
#harvest theses Indiana U., Bloomington (main)
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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Indiana U., Bloomington (main)'
jnlfilename = 'THESES-INDIANABLOOMINGTON-%s' % (stampoftoday)
boringdepartments = ['Anthropology/University Graduate School', 'Department of Anthropology',
                     'Department of Biology',
                     'Department of Biology School of Informatics Computing Engineering/University Graduate School',
                     'Department of Communication Culture', 'Department of Earth Atmospheric Sciences',
                     'Department of English/University Graduate School', 'Department of Folklore Ethnomusicology',
                     'Department of History', 'Department of Linguistics',
                     'Department of Linguistics the Department of Second Language Studies',
                     'Department of Psychological Brain Sciences',
                     'Department of Psychological Brain Sciences/College of Arts Sciences',
                     'Department of Psychological Brain Sciences Program in Neuroscience',
                     'Department of Psychological Brain Sciences the Cognitive Science Program',
                     'Department of Psychological Brain Sciences the Program in Neural Science',
                     'Department of Psychological Brain Sciences the Program in Neuroscience',
                     'Department of Psychological Brain Sciences/University Graduate School',
                     'Department of Spanish Portuguese', 'Department of Speech Hearing Sciences',
                     'History Philosophy of Science Medicine/University Graduate School',
                     #'Informatics Computing Engineering/University Graduate School',
                     'Jacobs School of Music', 'Kelley School of Business',
                     'Linguistics/University Graduate School',
                     'Media School/University Graduate School',
                     'Musicology/Jacobs School of Music', 'School of Education',
                     'School of Education/University Graduate School',
                     #'School of Informatics Computing Engineering',
                     'School of Optometry', 'School of Public Environmental Affairs',
                     'School of Public Health', 'School of Public Health/University Graduate School',
                     'Anthropology', 'Biochemistry', 'Biochemistry Molecular Biology',
                     'Biology', 'Business', 'Cellular Integrative Physiology',
                     'Central Eurasian Studies', 'Chemistry', 'Classical Studies',
                     'Cognitive Science', 'Cognitive Science Program',
                     'Cognitive Science/Psychological Brain Sciences',
                     'Communication Culture', 'Comparative Literature', 'Criminal Justice',
                     'Department of Biochemistry Molecular Biology',
                     'Department of Biology School of Informatics Computing Engineering/University Graduate School',
                     'Department of Central Eurasian Studies', 'Department of English',
                     'Department of Folklore Ethnomusicology', 'Department of French Italian',
                     'Department of Psychological Brain Sciences',
                     'Department of Psychological Brain Sciences Program in Neuroscience',
                     'Department of Psychological Brain Sciences the Department of Biology',
                     'Department of Psychological Brain Sciences the Program in Neuroscience',
                     'Department of Sociology', 'East Asian Languages Cultures',
                     'East Asian Languages Cultures (EALC', 'Ecology Evolutionary Biology',
                     'Economics', 'Education', 'Educational Leadership',
                     'Educational Leadership Policy Studies', 'English', 'Environmental Science',
                     'Fine Arts', 'Folklore Ethnomusicology', 'French',
                     'Geography', 'Geological Sciences', 'Germanic Studies',
                     'Health Rehabilitation Sciences', 'History', 'History/American Studies',
                     'History of Art', 'History Philosophy of Science', 'Italian',
                     'Journalism', 'Linguistics', 'Linguistics Central Eurasian Studies',
                     'Linguistics/Second Language Studies', 'Mass Communications/Telecommunications',
                     'Microbiology', 'Microbiology Immunology', 'Molecular Cellular Developmental Biology',
                     'Music', 'Near Eastern Languages Cultures', 'Neuroscience',
                     'Nursing Science', 'Optometry', 'Pharmacology Toxicology',
                     'Philanthropic Studies', 'Philosophy', 'Political Science',
                     'Psychological Brain Sciences',
                     'sychological Brain Sciences/Cognitive Science',
                     'Psychological Brain Sciences/Cognitive Sciences',
                     'Psychological Brain Sciences the Cognitive Science Program',
                     'Psychology', 'Public Affairs', 'Public Health', 'Public Policy',
                     'School of Health Physical Education Recreation',
                     #'School of Informatics Computing', 'School of Informatics Computing Engineering',
                     'Sociology', 'Spanish', 'Spanish Portuguese', 'Speech Hearing']



                     


rpp = 50
pages = 1

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://scholarworks.iu.edu/dspace/handle/2022/3086/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(page*rpp) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'item-metadata'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://scholarworks.iu.edu' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)
    time.sleep(10)

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
            print "   retry %s in 5 seconds" % (rec['artlink'])
            time.sleep(5)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "   no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
            #supervisor
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([ meta['content']])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content'][:10]
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
            #department
            elif meta['name'] == 'DC.description':
                dep = re.sub('.*Indiana University, *(.*), [12].*', r'\1', meta['content'])
                dep = re.sub('(,| and|\&) ', ' ', dep)
                rec['department'] = dep
                rec['note'].append(meta['content'])
            #thesis type
            elif meta['name'] == 'DC.type':
                if meta['content'] != 'Doctoral Dissertation':
                    rec['note'].append(meta['content'])
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('^10\.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
    rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'pdf_url' in rec.keys():
                rec['FFT'] = rec['pdf_url']
    #upload PDF at least hidden
    if not 'FFT' in rec.keys() and 'pdf_url' in rec.keys():
        rec['hidden'] = rec['pdf_url']
    if 'department' in rec.keys() and rec['department'] in boringdepartments:
        print '  skip "%s"' % (rec['department'])
    else:
        print '  ', rec.keys()
        recs.append(rec)

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
