# -*- coding: utf-8 -*-
#harvest theses Stony Brook U.
#FS: 2020-03-26

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

publisher = 'Stony Brook U.'
jnlfilename = 'THESES-STONYBROOK-%s' % (stampoftoday)
boringdepartments = ['Department of Molecular and Cellular Biology',
                     'Department of Biomedical Engineering',
                     'Department of Biopsychology',
                     'Department of Chemistry', 'Department of Geosciences',
                     'Department of Marine and Atmospheric Science',
                     'Department of Neuroscience', 'Department of Anthropology',
                     'Department of Art History and Criticism',
                     'Department of Materials Science and Engineering',
                     'Department of Biochemistry and Cell Biology',
                     'Department of Biomedical Engineering.',
                     'Department of Comparative Literary and Cultural Studies',
                     'Department of Ecology and Evolution',
                     'Department of Economics', 'Department of English',
                     'Department of Electrical Engineering',
                     'Department of Experimental Psychology',
                     'Department of Genetics', 'Department of Linguistics',
                     'Department of Music', 'Department of Philosophy',
                     'Department of Physiology and Biophysics',
                     'Department of Social/Health Psychology',
                     'Department of Science Education', 'Department of Studio Art',
                     'Department of Biochemistry and Structural Biology',
                     'Department of Clinical Psychology',
                     'Department of Comparative Literature',
                     'Department of Computer Engineering',
                     'Department of Computer Engineering.',
                     'Department of Electrical Engineering.',
                     'Department of English.', 'Department of Chemistry.',
                     'Department of Experimental Psychology.',
                     'Department of Hispanic Languages and Literature',
                     'Department of History', 'Department of Sociology',
                     'Department of Materials Science and Engineering.',
                     'Department of Mechanical Engineering',
                     'Department of Molecular Genetics and Microbiology',
                     'Department of Molecular Genetics and Microbiology.',
                     'Department of Oral Biology and Pathology',
                     'Department of Political Science',
                     'Department of Romance Languages and Literature (Italian)',
                     'Department of Technology, Policy, and Innovation',
                     'Department of Theatre Arts',
                     'Department of Anatomical Sciences.',
                     'Department of Anthropology.',
                     'Department of Art History and Criticism.',
                     'Department of Biochemistry and Cell Biology.',
                     'Department of Biochemistry and Structural Biology.',
                     'Department of Biological Sciences.',
                     'Department of Biopsychology.',
                     'Department of Clinical Psychology.',
                     'Department of Comparative Literary and Cultural Studies.',
                     'Department of Comparative Literature.',
                     'Department of Dramaturgy.',
                     'Department of Ecology and Evolution.',
                     'Department of Economics.', 'Department of Genetics.',
                     'Department of Geosciences.',
                     'Department of Hispanic Languages and Literature.',
                     'Department of History.', 'Department of Linguistics.',
                     'Department of Marine and Atmospheric Science.',
                     'Department of Mechanical Engineering.',
                     'Department of Molecular and Cellular Biology.',
                     'Department of Molecular and Cellular Pharmacology',
                     'Department of Molecular and Cellular Pharmacology.',
                     'Department of Music.', 'Department of Neuroscience.',
                     'Department of Oral Biology and Pathology.',
                     'Department of Philosophy.', 'Department of Political Science.',
                     'Department of Physiology and Biophysics.',
                     'Department of Social/Health Psychology.',
                     'Department of Social Welfare.',
                     'Department of Creative Writing and Literature.',
                     'Department of Sociology.', 'Department of Studio Art.',
                     'Department of Technology, Policy, and Innovation.',
                     'Department of Theatre Arts.',
                     'Department of English (Comparative Literature)',
                     'Department of Creative Writing and Literature',
                     'Department of Dramaturgy', 'Department of Art History',
                     'Department of Marine and Atmospheric Scienc',
                     'Department of Population Health and Clinical Outcomes Research',
                     'Department of Romance Languages and Literature (French)',
                     'Department of Social Welfare']

rpp = 100
pages = 5

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://ir.stonybrook.edu/xmlui/handle/11401/73112/browse?order=DESC&rpp=' + str(rpp) + '&sort_by=2&etal=-1&offset=' + str(page*rpp) + '&type=dateissued'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://ir.stonybrook.edu' + a['href'] #+ '?show=full'
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
            #pages
            elif meta['name'] == 'DC.description':
                if re.search('\d\d pg\.', meta['content']):
                    rec['pages'] = re.sub('.*?(\d\d+) pg.*', r'\1', meta['content'])
            #department
            elif meta['name'] == 'DC.contributor':
                if re.search('Department', meta['content']):
                    rec['department'] = meta['content']
                    rec['note'].append(meta['content'])
            #thesis type
            elif meta['name'] == 'DC.type':
                rec['note'].append(meta['content'])
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
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
