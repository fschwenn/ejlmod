# -*- coding: utf-8 -*-
#harvest theses from Cornell
#FS: 2019-12-09


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Cornell U.'

rpp = 10
yearstocover = 2
pages = 30

hdr = {'User-Agent' : 'Magic Browser'}
allhdls = []
recs = []
boring = ['Electrical+and+Computer+Engineering', 'Biomedical+and+Biological+Sciences',
          'Anthropology', 'Computational+Biology', 'History', 'Medicine', 'Law',
          'Linguistics', 'Mechanical+Engineering', 'Animal+Science', 'Statistics',
          'Chemistry+and+Chemical+Biology', 'Computer+Science', 'Microbiology',
          'Natural+Resources', 'Science+and+Technology+Studies', 'J.S.D.%2C+Law',
          'Ecology+and+Evolutionary+Biology', 'Food+Science+and+Technology',
          'Genetics%2C+Genomics+and+Development', 'Information+Science',
          'Comparative+Literature', 'Geological+Sciences', 'Government', 'Biophysics',
          'Plant+Biology', 'Plant+Breeding', 'Psychology', 'Theoretical+and+Applied+Mechanics',
          'Aerospace+Engineering', 'Applied+Economics+and+Management', 'Nutrition', 
          'Biochemistry%2C+Molecular+and+Cell+Biology', 'Biomedical+Engineering',
          'Chemical+Engineering', 'Civil+and+Environmental+Engineering', 'Communication',
          'D.M.A.%2C+Music', 'Economics', 'English+Language+and+Literature',
          'Germanic+Studies', 'Hotel+Administration', 'Industrial+and+Labor+Relations',
          'Music', 'Operations+Research+and+Information+Engineering', 'Sociology',
          'Biological+and+Environmental+Engineering', 'City+and+Regional+Planning',
          'Design+and+Environmental+Analysis', 'Development+Sociology', 'Horticulture',
          'Plant+Pathology+and+Plant-Microbe+Biology', 'Policy+Analysis+and+Management', 
          'History+of+Art%2C+Archaeology%2C+and+Visual+Studies', 'Management',
          'Asian+Literature%2C+Religion+and+Culture', 'Human+Development',
          'Philosophy', 'Romance+Studies', 'Soil+and+Crop+Sciences', 'Medieval+Studies',
          'Africana+Studies', 'Architecture', 'Atmospheric+Science', 'Classics', 'Entomology',
          'Fiber+Science+and+Apparel+Design', 'Near+Eastern+Studies', 'Theatre+Arts',
          'Neurobiology+and+Behavior', 'Regional+Science', 'Systems+Engineering', 
          'Materials+Science+and+Engineering', 'Asian+Literature%2C+Religion%2C+and+Culture',
          'Comparative+Biomedical+Sciences', 'Education', 'Environmental+Toxicology',
          'Genetics%2C+Genomics+and++Development', 'Genetics+and+Development', 'Zoology',
          'History+of+Art%2C+Archaeology+and+Visual+Studies', 'Horticultural+Biology',
          'Immunology+and+Infectious+Disease', 'Molecular+and+Integrative+Physiology',
          'Operations+Research', 'Pharmacology', 'Agricultural+and+Biological+Engineering',
          'Agricultural+Economics', 'Apparel+Design', 'Behavioral+Biology', 'Biochemistry',
          'Biometry', 'Developmental+Psychology', 'East+Asian+Literature', 'Ecology',
          'Electrical+Engineering', 'Evolutionary+Biology', 'Fiber+Science', 'Genetics',
          'History+of+Architecture+and+Urban+Development', 'History+of+Art+and+Archaeology',
          'Hospitality+Management', 'Human+Behavior+and+Design', 'Musicology', 'Neurobiology',
          'Physiology', 'Plant+Pathology', 'Resource+Economics', 'Veterinary+Medicine', 
          'Human+Development+and+Family+Studies', 'Immunology', 'Molecular+and+Cell+Biology']


for page in range(pages):
    tocurl = 'https://ecommons.cornell.edu/handle/1813/47/recent-submissions?rpp=' + str(rpp) + '&offset=' + str((330+page)*rpp)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    for div in divs:
        keepit = True
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for span in div.find_all('span', attrs = {'class' : 'date'}):
            rec['date'] = span.text.strip()
            if int(rec['date'][:4]) >= now.year - yearstocover:
                for span in div.find_all('span', title=re.compile('rft.degree=Doctor')):
                    degrees = re.split('.rft.degree=', span['title'])[1:]
                    for degree in degrees:
                        if degree in boring:
                            #print ' skip "%s"' % (degree)
                            keepit = False
                        elif degree in ['Applied+Mathematics', 'Mathematics']:
                            rec['fc'] = 'm'
                        elif degree in ['Astronomy', 'Astronomy+and+Space+Sciences']:
                            rec['fc'] = 'a'
                        elif not degree in ['Doctor+of+Philosophy', 'Cornell+University'] and not re.search('^Ph..D', degree):
                            rec['note'].append(degree)
                    for a in div.find_all('a'):
                        rec['artlink'] = 'https://ecommons.cornell.edu' + a['href'] #+ '?show=full'
                        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                        if rec['hdl'] in allhdls:
                            print 'skip double appearance of', rec['hdl']
                        elif keepit:
                            recs.append(rec)
                            allhdls.append(rec['hdl'])
    print '               %i records so far ' % (len(recs))
    time.sleep(10)

i = 0
for rec in recs:
        i += 1
        print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
            time.sleep(5)
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
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
                    rec['autaff'][-1].append(publisher)
                #pages
                elif meta['name'] == 'DC.description':
                    if re.search('\d\d+ pages', meta['content']):
                        rec['pages'] = re.sub('.*?(\d\d+) pages.*', r'\1', meta['content'])
                #DOI
                elif meta['name'] == 'DC.identifier' and re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
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
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
                else:
                    for div in artpage.find_all('div'):
                        for a2 in div.find_all('a'):
                            if a2.has_attr('href') and re.search('bistream.*\.pdf', a['href']):
                                divt = div.text.strip()
                                if re.search('Restricted', divt):
                                    print divt
                                else:
                                    rec['FFT'] = 'https://ecommons.cornell.edu' + re.sub('\?.*', '', a['href'])
        #hidden PDF
        if not 'license' in rec.keys():
            if 'pdf_url' in rec.keys():
                rec['hidden'] = rec['pdf_url']
            else:
                for div in artpage.find_all('div'):
                    for a2 in div.find_all('a'):
                        if a2.has_attr('href') and re.search('bistream.*\.pdf', a['href']):
                            divt = div.text.strip()
                            if re.search('Restricted', divt):
                                print divt
                            else:
                                rec['hidden'] = 'https://ecommons.cornell.edu' + re.sub('\?.*', '', a['href'])
        print '  ', rec.keys()
                                    
jnlfilename = 'THESES-CORNELL-%s' % (stampoftoday)

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
