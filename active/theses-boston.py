# -*- coding: utf-8 -*-
#harvest theses from Boston U.
#FS: 2021-04-23

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
jnlfilename = 'THESES-BOSTON-%s' % (stampoftoday)

publisher = 'Boston U.'

hdr = {'User-Agent' : 'Magic Browser'}

rpp = 50
pages = 15
years = 20
boringdisciplines = ['Mechanical+Engineering', 'Biomedical+Engineering', 'Education',
                     'Systems+Engineering', 'Sargent+College+of+Health+and+Rehabilitation+Sciences',
                     'Microbiology', 'Molecular+and+Translational+Medicine', 'Neuroscience', 'Pharmacology',
                     'Social+Work', 'Anatomy+%26+Neurobiology', 'Chemistry', 'Computer+Science',
                     'Electrical+%26+Computer+Engineering', 'Emerging+Media+Studies', 'Environmental+Health',
                     'Epidemiology', 'Genetics+%26+Genomics', 'Health+Services+Research', 'Management',
                     'Materials+Science+%26+Engineering', 'Pathology', 'Public+Health', 'Social+Work',
                     'American+%26+New+England+Studies', 'Biochemistry', 'Bioinformatics+GRS', 'Biology',
                     'Earth+%26+Environment', 'English', 'French+Language+%26+Literatures', 'Global+Health',
                     'Mass+Communication', 'Orthodontics+and+Dentofacial+Orthopedics', 'Philosophy',
                     'Religious+Studies', 'Theology', 'Emerging+Media+Studies', 'Periodontology', 'Astronomy',
                     'Biostatistics', 'Economics', 'Editorial+Studies', 'Hispanic+Language+%26+Literatures',
                     'History+of+Art+%26+Architecture', 'History', 'Mathematical+Finance', 'Political+Science',
                     'Prosthodontics', 'Sociology+%26+Social+Work', 'Sociology', 'Archaeology', 
                     'Molecular+%26+Cell+Biology', 'Molecular+Biology%2C+Cell+Biology+%26+Biochemistry', 
                     'Anthropology', 'Behavioral+Neurosciences', 'Physiology', 'Psychological+%26+Brain+Sciences',
                     'Endodontics', 'Nutrition+and+Metabolism', 'Oral+Biology', 'Biophysics',
                     'Medical+Sciences', 'Music+Education', 'Cognitive+%26+Neural+Systems',
                     'Dental+Public+Health', 'Dermatology', 'Molecular+Medicine',
                     'Accounting', 'Art+%26+Architecture%2C+History+of', 'Behavioral+Neuroscience',
                     'Bioinformatics', 'Biomedical+Engineering+and+Pharmacology+and+Experimental+Therapeutics',
                     'Business+Administration', 'Clinical+Psychology', 'Computer+Engineering',
                     'Electrical+and+Computer+Engineering', 'Electrical+Engineering',
                     'Health+Policy+%26+Management', 'Health+Sciences', 'Materials+Science+and+Engineering',
                     'Medical+Nutritional+Sciences', 'Occupational+Therapy+Doctorate', 'Occupational+Therapy',
                     'Operations+and+Technology+Management', 'Pathology+%26+Laboratory+Medicine',
                     'Pharmacology+%26+Experimental+Therapeutics', 'Physiology+%26+Biophysics', 'Psychology',
                     'Rehabilitation+Sciences', 'Restorative+Sciences+%26+Biomaterials', 'Romance+Studies',
                     'Speech%2C+Language+%26+Hearing+Sciences', 'Speech+Language+and+Hearing+Sciences',
                     'Strategy+and+Innovation','American+and+New+England+Studies', 'American+Studies',
                     'Anatomy+and+Neurobiology', 'Anatomy', 'Applied+Anatomy+and+Physiology', 'Archeology',
                     'Art+History', 'Bimolecular+Pharmacology', 'Biochemistry+and+Cell+and+Molecular+Biology',
                     'Biomedical+engineering', 'Biomolecular+Pharmacology', 'Biophysical+Chemistry',
                     'Brain%2C+Behavior%2C+and+Cognition', 'Cell+%26+Molecular+Biology',
                     'Cell+and+Molecular+Biology', 'Cell+Biology%2C+Molecular+Biology%2C+and+Biochemistry',
                     'Classical+Studies', 'Coastal+Geomorphology', 'Cognitive+and+Neural+Systems',
                     'Comparative+Literature+and+Religious+Studies', 'Counseling+Psychology+and+Religion',
                     'Counseling+Psychology+and+Sports+Psychology', 'Cultural+Anthropology',
                     'Curriculum+and+Teaching', 'Developmental+Studies', 'Earth+Sciences', 'Earth+Science',
                     'Ecology%2C+Evolution%2C+and+Behavior', 'Educational+Policy', 'Engineering',
                     'Engingeering', 'English+Literature', 'Environmental+Studies', 'Experimental+Physics',
                     'Genetics+and+Genomics', 'Geography+and+Environment', 'Geography',
                     'Health+Policy+and+Management+Research', 'Health+Policy+and+Management',
                     'Hispanic+Language+and+Literature', 'Hispanic+Literature', 'Hispanic+Studies',
                     'History+of+Art+and+Architecture', 'Inorganic+Chemistry', 'International+Relations',
                     'Linguistics', 'Literature', 'Marketing', 'Material+Science+and+Engineering',
                     'Medical+Nutrition+Sciences', 'Medicine', 'Microbiology+and+Cell+and+Molecular+Biology',
                     'Molecular%2C+Cell+Biology+%26+Biochemistry', 'Neurology', 'Organic+Chemistry',
                     'Molecular+and+Cellular+Biology+--+Biochemistry', 'Pathology+and+Immunology', 
                     'Molecular+Biology%2C+Biochemistry%2C+and+Cell+Biology', 'Philosophy+and+Greek', 
                     'Molecular+Biology%2C+Cell+Biology%2C+and+Biochemistry', 'Physiology+and+Biophysics', 
                     'Molecular+Biology%2C+Cell+Biology%2C+Biochemistry', 'Rehabilitation+Science', 
                     'Pharmacology+and+Experimental+Therapeutics+and+Biomedical+Neuroscience',
                     'Pharmacology+and+Experimental+Therapeutics', 'Pharmacology+and+Neuroscience', 
                     'Molecular+Biology%2C+Cell+Biology+and+Biochemistry', 'Religion',
                     'Religious+and+Theological+Studies', 'Spanish', 'Statistical+Mathematics', 
                     'Molecular+Medicine%2C+Cell+and+Molecular+Biology', 'Pathology+and+Laboratory+Medicine', 
                     'Movement+Rehabilitation+and+Health+Sciences', 'Music', 'Synthetic+Organic+Chemistry',
                     'Near+Eastern+Archaeology+and+Paleoethnobotany', 'Neurobiology', 'Neurolinguistics', 
                     'Musicology', 'Computational+Neuroscience', 'Applied+Linguistics', 'Biophysic']
boringdegrees = ['Master+of+Science', 'masters', 'Doctor+of+Education', 'Doctor+of+Musical+Arts',
                 'Master+of+Music', 'Doctor+of+Business+Administration', 'Doctor+of+Occupational+Therapy',
                 'Doctor+of+Ministry', 'Doctor+of+Public+Health', 'Doctor+of+Science+in+Dentistry']

recs = []
redeg = re.compile('rft.degree=')
for page in range(pages):
    tocurl = 'https://open.bu.edu/handle/2144/8520/discover?rpp='+str(rpp)+'&etal=0&group_by=none&page=' + str(page+1 + 86) + '&sort_by=dc.date.issued_dt&order=desc'
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
                        elif not degree in ['Ph.D.', 'doctoral', 'Boston+University']:
                            rec['note'].append(degree)
        if keepit:
            for a in div.find_all('a'):
                if re.search('handle', a['href']):
                    rec['artlink'] = 'https://open.bu.edu' + a['href'] + '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
    print '  %i records so far' % (len(recs))
    time.sleep(2)

i = 0
for rec in recs:
    keepit = True
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            req = urllib2.Request(rec['artlink'], headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
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
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
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
