# -*- coding: utf-8 -*-
#harvest theses from Guelph U.
#FS: 2022-04-20

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
jnlfilename = 'THESES-GUELPH-%sB' % (stampoftoday)

publisher = 'Guelph U.'

hdr = {'User-Agent' : 'Magic Browser'}

rpp = 50
pages = 6
years = 3
boringdisciplines = ['Mechanical+Engineering', 'Environmental+Sciences', 'Animal+and+Poultry+Science',
                     'Chemistry', 'Department+of+Animal+Biosciences', 'Department+of+Chemistry',
                     'Department+of+Economics+and+Finance', 'Department+of+Family+Relations+and+Applied+Nutrition',
                     'Department+of+Pathobiology', 'Department+of+Plant+Agriculture', 'Economics', 'Engineering',
                     'Family+Relations+and+Applied+Nutrition', 'Pathobiology', 'Plant+Agriculture', 'Public+Health',
                     'School+of+Engineering', 'Department+of+Population+Medicine', 'Bioinformatics', 'Geography', 
                     'Biomedical+Sciences', 'Clinical+Studies', 'Creative+Writing', 'Department+of+Clinical+Studies', 
                     'Criminology+and+Criminal+Justice+Policy', 'Department+of+Biomedical+Sciences', 'English',
                     'Department+of+Geography%2C+Environment+and+Geomatics', 'Department+of+History', 'History', 
                     'Department+of+Human+Health+and+Nutritional+Sciences', 'Department+of+Integrative+Biology',
                     'Department+of+Marketing+and+Consumer+Studies', 'Department+of+Molecular+and+Cellular+Biology',
                     'Department+of+Psychology', 'Department+of+Sociology+and+Anthropology', 'Doctor+of+Veterinary+Science',
                     'Human+Health+and+Nutritional+Sciences', 'Integrative+Biology', 'Landscape+Architecture', 'Management', 
                     'Latin+American+and+Caribbean+Studies', 'Literary+Studies+%2F+Theatre+Studies+in+English',
                     'Molecular+and+Cellular+Biology', 'Psychology', 'Rural+Planning+and+Development', 'Sociology',
                     'School+of+English+and+Theatre+Studies', 'School+of+Environmental+Design+and+Rural+Development',
                     'School+of+Languages+and+Literatures', 'Theatre+Studies', 'Veterinary+Science', 'Philosophy',
                     'Biophysics', 'Collaborative+International+Development+Studies', 'Department+of+Philosophy', 
                     'Department+of+Food%2C+Agricultural+and+Resource+Economics', 'Department+of+Food+Science',
                     'Department+of+Political+Science', 'Food%2C+Agriculture+and+Resource+Economics', 'Food+Science',
                     'Political+Science', 'School+of+Environmental+Sciences', 'Tourism+and+Hospitality', 'Toxicology',
                     'School+of+Hospitality%2C+Food+and+Tourism+Management', 'Applied+Statistics',
                     'Department+of+Environmental+Biology', 'Department+of+Land+Resource+Science',
                     'Environmental+Biology', 'Faculty+of+Environmental+Sciences', 'Land+Resource+Science',
                     'Population+Medicine']
boringdegrees = ['Master+of+Science', 'masters', 'Doctor+of+Education', 'Doctor+of+Musical+Arts',
                 'Master+of+Music', 'Doctor+of+Business+Administration', 'Doctor+of+Occupational+Therapy',
                 'Doctor+of+Ministry', 'Doctor+of+Public+Health', 'Doctor+of+Science+in+Dentistry',
                 'Master+of+Applied+Science', 'Master+of+Arts', 'Master+of+Fine+Arts', 'Bachelor+of+Science',
                 'Master+of+Business+Administration+%28Hospitality+and+Tourism+Management%29',
                 'Master+of+Landscape+Architecture', 'Master+of+Science+%28Planning%29']

recs = []
redeg = re.compile('rft.degree=')
for page in range(pages):
    tocurl = 'https://atrium.lib.uoguelph.ca/xmlui/handle/10214/151/browse?order=DESC&rpp='+str(rpp)+'&sort_by=3&etal=-1&offset=' + str((50+page)*rpp) + '&type=dateissued'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        keepit = True
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'supervisor' : []}
        for span in div.find_all('span', attrs = {'class' : 'date'}):
            if re.search('[12]\d\d\d', span.text):
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                if int(rec['year']) < now.year - years:
                    keepit = False
                    #print '  skip',  rec['year']
        for span in div.find_all('span', attrs = {'class' : 'Z3988'}):
            infos = re.split('&', span['title'])
            for info in infos:
                if keepit:
                    if redeg.search(info):
                        degree = redeg.sub('', info)
                        if degree in boringdisciplines or degree in boringdegrees:
                            keepit = False
                            #print '  skip', degree
                        elif not degree in ['Ph.D.', 'doctoral', 
                                            'University+of+Guelph', 'Doctor+of+Philosophy']:
                            rec['note'].append(degree)
        if keepit:
            for a in div.find_all('a'):
                if re.search('handle', a['href']):
                    rec['link'] = 'https://atrium.lib.uoguelph.ca' + a['href']# + '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
    print '  %i records so far' % (len(recs))
    time.sleep(3)

i = 0
for rec in recs:
    keepit = True
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'] + '?show=full', headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(4)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            req = urllib2.Request(rec['link'] + '?show=full', headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['content']:
                    rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split('[,;] ', meta['content']):
                    rec['keyw'].append(keyw)
            #rights
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
    for tr in artpage.body.find_all('tr'):
        tdt = ''
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            tdt = td.text.strip()
            td.decompose()
        for td in tr.find_all('td'):
            if td.text.strip() == 'en_US':
                continue
            #supervisor
            if tdt in ['dc.contributor.supervisor', 'dc.contributor.advisor']:
                if td.text.strip():
                    rec['supervisor'].append([ re.sub(' \(.*', '', td.text.strip()) ])
            #ORCID
            elif tdt == 'dc.identifier.orcid':
                if re.search('\d\d\d\d\-\d\d\d\d', td.text):
                    rec['autaff'][-1].append('ORCID:' + re.sub('.*orcid.org\/+', '', td.text.strip()))
    #fulltext
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    rec['autaff'][-1].append(publisher)
            
    print '  ', rec.keys()
                
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
