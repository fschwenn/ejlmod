# -*- coding: utf-8 -*-
#harvest theses from U. Tennessee, Knoxville
#FS: 2022-03-25


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
from inspire_utils.date import normalize_date

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Tennessee, Knoxville'

pages = 6

jnlfilename = 'THESES-TennesseeKnoxville-%s' % (stampoftoday)

basetocurl = 'https://trace.tennessee.edu/utk_graddiss/index.'
tocextension = 'html'

boring = ['Psychology', 'English', 'Ecology and Evolutionary Biology', 'Life Sciences',
          'Nuclear Engineering', 'Materials Science and Engineering', 'Public Health', 
          'Anthropology', 'Educational Psychology', 'Environmental and Soil Sciences',
          'Environmental Engineering', 'Geography', 'Kinesiology and Sport Studies',
          'Nutrition', 'Philosophy', 'Retail, Hospitality, and Tourism Management',
          'Spanish', 'Biomedical Engineering', 'Chemical Engineering', 'Child and Family Studies',
          'Communication and Information', 'Computer Engineering', 'Political Science', 
          'Educational Psychology and Research', 'Engineering Science', 'Food Science', 'History',
          'Kinesiology', 'Modern Foreign Languages', 'Natural Resources', 'Nutritional Sciences',
          'Teacher Education', 'Data Science and Engineering', 'Economics', 'Nursing',
          'Electrical Engineering', 'Microbiology', 'Plant, Soil and Environmental Sciences', 
          'Social Work', 'Business Administration', 'Civil Engineering', 'Education',
          'Higher Education Administration', 'School Psychology', 'Industrial Engineering', 
          'Biochemistry and Cellular and Molecular Biology', 'Counselor Education', 'Chemistry',
          'Energy Science and Engineering', 'Mechanical Engineering', 'Business Analytics',
          'Instructional Technology and Educational Studies', 'Management Science',
          'Plants, Soils, and Insects', 'Animal Science', 'Biosystems Engineering',
          'Entomology and Plant Pathology', 'Entomology, Plant Pathology and Nematology',
          'Experimental Psychology', 'Plant Sciences', 'Aerospace Engineering', 'Geology',
          'Communication', 'Counseling', 'Food Science and Technology', 'French', 'German',
          'Industrial and Organizational Psychology', 'Information Sciences', 'American History',
          'Polymer Engineering', 'Sport Studies', 'Wildlife and Fisheries Science',
          'Educational Administration', 'Sociology', 'Comparative and Experimental Medicine',
          'Botany', 'Exercise and Sport Sciences', 'Health and Human Sciences', 'Exercise Science',
          ']Human Ecology', 'Human Resource Management', 'Speech and Hearing Science']
boring += ['Master of Arts', 'Master of Science', 'Master of Music', 'Master of Fine Arts',           
           'Master of Library and Information Science', 'Master of Urban Planning',
           'Doctor of Education']

prerecs = []
date = False
tocextension = 'html'
for i in range(pages):
    tocurl = basetocurl + tocextension
    print '==={ %i/%i }==={ %s }===' % (i+1, pages, tocurl)
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
    for div in tocpage.body.find_all('div'):
        if div.has_attr('class') and re.search('^lockss_\d', div['class'][0]):
            for child in div.children:
                try:
                    name = child.name
                except:
                    continue
                if name == 'h4':
                    for span in child.find_all('span'):
                        date = span.text.strip()
                elif name == 'p':
                    #year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
                    if int(date) >= now.year - 1*100:
                        rec = {'jnl' : 'BOOK', 'tc' : 'T', 'date' : date, 'note' : [], 'supervisor' : []}
                        for a in child.find_all('a'):
                            if not re.search('(viewcontent.cgi|proquest.com|network.bepress.com)', a['href']):
                                rec['tit'] = a.text.strip()
                                rec['artlink'] = a['href']
                                a.replace_with('')
                                prerecs.append(rec)
    print '  ', len(prerecs)
    tocextension = '%i.html' % (i+2)

recs = []
i = 0
for rec in prerecs:
    i += 1
    keepit = True
    department = False
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #abstract
            if meta['name'] == 'description':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #thesis type
            elif meta['name'] == 'bepress_citation_dissertation_name':
                rec['note'] = [ meta['content'] ]
                if meta['content'] in boring:
                    print '    skip "%s"' % (meta['content'])
                    keepit = False
                else:
                    rec['note'].append(meta['content'])
            #author
            elif meta['name'] == 'bepress_citation_author':
                rec['autaff'] = [[ meta['content'] ]]
                for div2 in artpage.body.find_all('div', attrs = {'id' : 'author1_orcid'}):
                    for p in div2.find_all('p'):
                        rec['autaff'][-1].append('ORCID:'+re.sub('.*org\/', '', p.text))
            #fulltext
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['pdf_url'] = meta['content']
            #DOI
            elif meta['name'] == 'bepress_citation_doi':
                rec['doi'] = re.sub('^ht.*?\/10', '10', meta['content'])
            #date
            elif meta['name'] == 'bepress_citation_date':
                rec['date'] = meta['content']
    #supervisor
    for div in artpage.body.find_all('div', attrs = {'id' : 'advisor1'}):
        for p in div.find_all('p'):
            rec['supervisor'] = [[ re.sub('^Dr. ', '', p.text.strip()) ]]
    #for div in artpage.body.find_all('div', attrs = {'id' : 'advisor2'}):
    #    for p in div.find_all('p'):
    #        rec['supervisor'].append( [re.sub('^Dr. ', '', p.text.strip())] )
    if not rec.has_key('doi'):
        rec['doi'] = '30.3000/TennesseeKoxville/' + re.sub('\W', '', re.sub('.*edu', '', rec['artlink']))
        rec['link'] = rec['artlink']
    #embargo
    for div in artpage.body.find_all('div', attrs = {'id' : 'embargo_date'}):
        for p in div.find_all('p'):
            rec['embargo'] = normalize_date(p.text.strip())
    if 'pdf_url' in rec.keys():
        if 'embargo' in rec.keys():
            if rec['embargo'] > stampoftoday:
                print '    embargo until %s' % (rec['embargo'])
            else:
                rec['FFT'] = rec['pdf_url']
        else:
            rec['FFT'] = rec['pdf_url']
    #department
    for div in artpage.body.find_all('div', attrs = {'id' : 'department'}):
        for p in div.find_all('p'):
            department = p.text.strip()
            if department in boring:
                print '    skip "%s"' % (department)
                keepit = False
            elif department == 'Mathematics':
                rec['fc'] = 'm'
            elif department == 'Computer Science':
                rec['fc'] = 'c'
            else:
                rec['note'].append(department)
    if department and department == 'Physics':
        rec['autaff'][-1].append('Tennessee U.')
    else:
        rec['autaff'][-1].append(publisher)
    if keepit:
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
