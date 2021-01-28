# -*- coding: utf-8 -*-
#harvest Liverpool Theses
#FS: 2020-02-03


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Liverpool (main)'
hdr = {'User-Agent' : 'Magic Browser'}

departmentstoskip = ['Chemistry', 'Archaeology, Classics and Egyptology', 'Archaeology',  'Architecture',  'Biochemistry',
                     'Biological Sciences',  'Biology',  'Biostatistics',  'Business Administration',
                     'Cellular &amp; Molecular Physiology',  'Cellular and Molecular Physiology',
                     'Centre for Higher Education Studies',  'Child Health',  'Civil Engineering and Industrial Design',
                     'Clinical Infection, Microbiology and Immunology',  'Clinical Psychology',  'Dentistry',
                     'Department of Archaeology, Classics and Egyptology',  'Department of Biostatistics',
                     'Department of Cellular and Molecular Physiology',
                     'Department of Clinical Infection, Microbiology and Immunology',
                     'Department of Electrical Engineering &amp; Electronics',
                     'Department of Molecular and Clinical Cancer Medicine',
                     'Department of Molecular and Clinical Pharmacology',  'Department of Psychological Sciences',
                     'Department of Sociology, Social Policy and Criminology',
                     'Department of Women&apos;s and Children&apos;s Health',  'Earth, Ocean and Ecological Sciences',
                     'Economics and Finance',  'Economics',  'Education',  'Electrical Eng &amp; Electronics',
                     'Electrical Engineering &amp; Electronics',  'Engineering',  'English',  'Environmental Sciences',
                     'Evolution, Ecology and Behaviour',  'Eye and Vision Science',  'Functional and Comparative Genomics',
                     'Gastroenterology',  'Geography and Planning',  'Health Services Research',  'History',
                     'Infection &amp; Immunity',  'Infection and Global Health',  'Infection Biology',
                     'Institute of Ageing and Chronic Disease',  'Institute of Infection &amp; Global Health',
                     'Institute of Infection and Global Health',  'Institute of Integrative Biology',
                     'Institute of Irish Studies',  'Institute of Psychology, Health &amp; Society',
                     'Institute of Psychology, Health and Society',  'Institute of Translational Medicine',  'Law',
                     'Liverpool Law School',  'Management School',  'Management',
                     'Mechanical, Materials and Aerospace Engineering',  'Medicine',  'Microbiology',
                     'Modern Languages and Cultures',  'Molecular and Clinical Cancer Medicine',
                     'Molecular and Clinical Pharmacology',  'Musculoskeletal Biology 1',  'Musculoskeletal Biology II',
                     'Musculoskeletal Biology',  'Music',  'Ocular Oncology',  'Operations and Supply Chain Management',
                     'Pharmacology',  'Politics',  'Psychological Sciences',  'Psychology',  'School of Biological Sciences',
                     'School of Chemistry',  'School of Dentistry',  'School of Education',
                     'School of Electrical Engineering, Electronics and Computer Science',  'School of Engineering',
                     'School of Environmental Sciences',  'School of Management',  'School of Psychology',
                     'School of Tropical Medicine',  'Sociology, Social Policy and Criminology',  'Sociology',
                     'Strategy, International Business and Entrepreneurship',  'Surgery and Oncology',  'Tropical medicine',
                     'Tropical Medicine',  'Veterinary Science',  'Work, Organisation and Management', 'Applied Health Research', 
                     'Archaeology (Arts)', 'Biological and Medical Sciences', 'Cancer Biology', 'Cancer Medicine', 
                     'Cellular &amp; Molecular Physiology', 'Cellular &amp;Molecular Physiology', 'Communications and Media', 
                     'Department of Communication and Media', 'Department of Electrical Engineering &amp; Electronics',
                     'Department of Epidemiology and Population Health', 'Department of Functional and Comparative Genomics',
                     'Department of Infection Biology', 'Department of Musculoskeletal Biology', 'Egyptology',
                     'Electrical Eng &amp; Electronics', 'Electrical Engineering &amp; Electronics', 'Endodontics',
                     'Epidemiology &amp; Population Health', 'Epidemiology &amp; Population Hlth',
                     'Epidemiology and Population Health', 'Epidemiology', 'Eye &amp; Vision Science', 'Geography',
                     'Haematology &amp; Leukaemia', 'Health Psychlogy', 'Higher Education (EdD)', 'Higher Education',
                     'Infect &amp; Global Hlth(Vet)', 'Infection &amp; Global Health (Medicine)', 'Infection &amp; Immunity',
                     'Infection and Global Health Veterinary', 'Infectious Diseases', 'Institute of Veterinary Science',
                     'Irish Studies', 'Management Studies', 'Medical Imaging', 'Medical Microbiology',
                     'Musculoskeletal Biol(Medicine)', 'Obesity &amp; Endocrinology(Med)', 'Orthodontics', 'Pancreatology',
                     'Pharmacology &amp; Therapeutics', 'Psychiatry', 'Psychology (Science)', 'Public Health', 'SACE',
                     'School of Histories, Languages and Cultures', 'Veterinary Immunology', 'Veterinary Parasitology',
                     'Veterinary Pathology', 'Virology', 'Women and Children&apos;s Health',
                     'Archives &amp; Record Management', 'Cellular &amp; Molecular Physiology', 'Cellular &amp;Molecular Physiology',
                     'Chester &amp; Hope', 'Civic Design', 'Educational Development', 'Electrical &amp; Electronic Engineering',
                     'Electrical Eng &amp; Electronics', 'Electrical Engineering &amp; Electronics', 'Endocrinology',
                     'Epidemiology &amp; Population Hlth', 'Eye &amp; Vision Science', 'Haematology &amp; Leukaemia',
                     'Health Services Resarch', 'Hispanic Studies', 'Immunology', 'Infect &amp; Global Hlth(Medicine)',
                     'Infect &amp; Global Hlth(Vet)', 'Infection &amp; Immunity', 'Medical Education', 'Molecular Virology',
                     'Musculoskeletal Biol(Vet)', 'Obesity &amp; Endocrinology(Med)', 'One Health (Veterinary)', 'Pathology',
                     'Pharmacology &amp; Therapeutics', 'Sociolinguistics', 'Veterinary Epidemiology',
                     'Veterinary Microbiology', 'Women&apos;s Health', 'School of Architecture',
                     'Institute of infection and Global health', 'School of Medical Education', 'Infection &amp; Immunity',
                     'Latin American Studies', 'Haematology', 'Obesity Biology', 'Clinical Engineering', 'Computer Sciences',
                     'Critical Care', 'Department of Clinical and Molecular', 'Department of Eye and Vision Science',
                     'Electrical Engineering &amp; Electronics', 'Electrical Engineering and Electronics', 'Eye &amp; Vision Science',
                     'German', 'Obesity &amp; Endocrinology(Med)', 'Pathophysiology', 'Perinatal &amp; Reproductive Med',
                     'Pharmacology &amp; Therapeutics', 'Infect &amp; Global Hlth(Vet)', 'Infection &amp; Immunity',
                     'Neurological Science', 'Ophthalmology', 'Haematology &amp; Leukaemia', 'Infect &amp; Global Hlth(Medicine)']



for year in [now.year-1, now.year]:
    prerecs = []
    jnlfilename = 'THESES-LIVERPOOL-%s_%i' % (stampoftoday, year)
    tocurl = 'https://livrepository.liverpool.ac.uk/view/doctype/thesis/%i.html' % (year)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for p in tocpage.find_all('p'):
        for a in p.find_all('a'):
            if a.has_attr('href') and re.search('livrepository.liverpool.ac.uk', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : a['href'], 'year' : str(year)}
                rec['tit'] = a.text.strip()
                rec['doi'] = '20.2000/Liverpool/' + re.sub('\D', '', a['href'])
                a.replace_with('XXX')
                pt = re.sub('.*XXX', '', re.sub('[\n\r\t]', '', p.text.strip()))
                if re.search('(Master|MD)', pt):
                    print 'skip "%s"' % (pt)
                else:
                    rec['note'] = [ pt ]
                    prerecs.append(rec)

    i = 0
    recs = []
    for rec in prerecs:
        i += 1
        print '---{ %i/%i }---{ %s }------' % (i, len(prerecs), rec['link'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(3)
        except:
            try:
                print 'retry %s in 180 seconds' % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            except:
                print 'no access to %s' % (rec['link'])
                continue
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #author
                if meta['name'] == 'eprints.creators_name':
                    rec['autaff'] = [[ meta['content'] ]]
                #ORCID
                elif meta['name'] == 'eprints.creators_orcid':
                    rec['autaff'][-1].append(re.sub('.*(\d{4}\-\d{4}\-\d{4}\-\d{4}).*', r'ORCID:\1', meta['content']))
                #keywords
                elif meta['name'] == 'eprints.keywords':
                    rec['keyw'] = re.split(', ', meta['content'])
                #abstract
                elif meta['name'] == 'eprints.abstract':
                    rec['abs'] = meta['content']
                #date
                elif meta['name'] == 'eprints.date':
                    rec['date'] = meta['content']
                #DOI
                elif meta['name'] == 'eprints.doi':
                    rec['doi'] = meta['content']
                #number of pages
                elif meta['name'] == 'eprints.pages':
                    rec['pages'] = meta['content']
                #PDF
                elif meta['name'] == 'eprints.document_url':
                    rec['hidden'] = meta['content']
                #department
                elif meta['name'] == 'eprints.department':
                    rec['department'] = meta['content']
                    rec['note'].append(rec['department'])
        if 'department' in rec.keys() and rec['department'] in departmentstoskip:
            print '   skip', rec['department']
        else:
            recs.append(rec)
            rec['autaff'][-1].append(publisher)
            print '  ', rec.keys()
                    
    #closing of files and printing
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writeXML(recs,xmlfile,publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path,'r').read()
    line = jnlfilename+'.xml'+ '\n'
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,'a')
        retfiles.write(line)
        retfiles.close()


