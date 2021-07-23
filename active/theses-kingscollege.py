# -*- coding: utf-8 -*-
#harvest theses from King's Coll. London 
#FS: 2020-08-31

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

publisher = "King's Coll. London"

jnlfilename = 'THESES-KINGS_COLLEGE-%s' % (stampoftoday)

rpp = 50
pages = 4
boring = ['Social Genetic & Developmental Psychiatry', 'Global Health & Social Medicine',
          'Biomedical Engineering Department', 'Cardiovascular Imaging',
          'Centre for Oral, Clinical & Translational Sciences', 'Chemistry', 'Classics',
          'Comprehensive Cancer Centre', 'Culture, Media & Creative Industries',
          'Defence Studies', 'Developmental Neurobiology', 'English Language & Literature',
          'European & International Studies', 'Geography', 'War Studies', 
          'School of Education, Communication & Society', 'Theology & Religious Studies', 
          'Institute of Pharmaceutical Science', 'Lau China Institute',
          'Medical & Molecular Genetics', 'Medical Education', 'Political Economy',
          'Population Health Sciences', 'Psychology', 'Twin Research & Genetic Epidemiology',
          'Adult Nursing', 'Analytical, Environmental & Forensic Sciences',
          'Basic and Clinical Neuroscience', 'Cardiovascular Research', 'Film Studies', 
          'Centre for Craniofacial & Regenerative Biology', 'Dermatology', 'French',
          'Health Service & Population Research', 'History', 'Imaging Chemistry & Biology',
          'Infectious Diseases', 'Inflammation Biology', 'Informatics', 'Liberal Arts', 'Music',
          'Nutritional Sciences', 'Peter Gorer Department of Immunobiology', 'Philosophy',
          "Policy Institute at King's", 'Psychological Medicine', 'Psychosis Studies',
          'Spanish, Portuguese & Latin American Studies', 'International Development', 'Laws', 
          'Wolfson Centre for Age Related Diseases', "Women & Children's Health",
          'Centre for Stem Cells & Regenerative Medicine', 'Digital Humanities', 
          'Cicely Saunders Institute of Palliative Care, Policy & Rehabilitation', 
          'Centre for Host Microbiome Interactions', 'Centre for Human & Applied Physiological Sciences',
          'Addictions', 'Biosciences Education', 'Biostatistics & Health Informatics',
          'Brazil Institute', 'Cancer Cell Biology & Imaging', 'Cardiovascular Sciences',
          'Centre of Construction Law', 'Child & Adolescent Psychiatry', 'Comparative Literature',
          'Diabetes', 'Forensic & Neurodevelopmental Sciences', 'German', 'Haemato-Oncology',
          'Imaging and Biomedical Engineering', "King's India Institute", 'Mental Health Nursing',
          'Neuroimaging', 'Nursing & Midwifery Research', 'Old Age Psychiatry',
          'Perinatal Imaging & Health', 'Respiratory Medicine & Allergy', 'Russia Institute',
          'Surgical & Intervention Engineering', 'Vascular Biology & Inflammation',
          'Arts & Humanities Research Institute', "Cancer Epidemiology", 
          "Centre for Dental Education", "Centre for Hellenic Studies", "Physiology",
          "Population & Patient Health", "Renal Sciences", "Salivary Research Unit", 
          "Child & Family Health Nursing", "Clinical Neuroscience", "Clinical Pharmacology",
          "Conservative Dentistry (including Endodontics)", "Dental Materials",
          "Experimental Immunobiology", "Gastrointestinal Cancer", "Health Policy & Management",
          "Immunoregulation and Immune Intervention", "Innate Immunity", "Oral Pathology", 
          "Institute of Liver Sciences", "King's Academy", "Microbiology", "Orthodontics",
          "Paediatric Allergy", "Paediatrics", "Periodontology", "PET Imaging Centre Facility", 
          "Middle Eastern Studies", "Midwifery", "Molecular Haematology", "Oral Immunology", 
          "King's Centre for Global Health & Health Partnerships", 'Vascular Risk & Surgery',
          'Randall Centre of Cell & Molecular Biophysics']

hdr = {'User-Agent' : 'Magic Browser'}

prerecs = []
#first get links of year pages
for page in range(pages):
    tocurl = 'https://kclpure.kcl.ac.uk/portal/en/theses/search.html?search=&field=all&ordering=studentThesisOrderByAwardYear&pageSize=' + str(rpp) + '&page=' + str(page) + '&type=%2Fdk%2Fatira%2Fpure%2Fstudentthesis%2Fstudentthesistypes%2Fstudentthesis%2Fdoc%2Fdsc&type=%2Fdk%2Fatira%2Fpure%2Fstudentthesis%2Fstudentthesistypes%2Fstudentthesis%2Fdoc%2Fphd&descending=true'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    year = False
    for ol in tocpage.body.find_all('ol', attrs = {'class' : 'portal_list'}):
        for li in ol.find_all('li'):
            if li.has_attr('class'):
                if 'portal_list_item_group' in li['class']:
                    year = li.text.strip()
                elif 'portal_list_item' in li['class']:
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'supervisor' : [], 'note' : []}
                    for h2 in li.find_all('h2'):
                        for a in h2.find_all('a'):
                            rec['link'] = a['href']
                            rec['tit'] = a.text.strip()
                            rec['year'] = year
                            rec['date'] = year
                            rec['doi'] = '20.2000/KINGsCOLLEGE/' + re.sub('.*\/(.*).html', r'\1', a['href'])[-60:]
                    prerecs.append(rec)
    time.sleep(5)


i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for tr in artpage.body.find_all('tr'):
        for th in tr.find_all('th'):
            tht = th.text.strip()
        for td in tr.find_all('td'):
            #supervisor
            if tht == 'Supervisors/Advisors':
                for span in td.find_all('span'):
                    rec['supervisor'].append([span.text.strip()])
    #department
    for li in artpage.body.find_all('li', attrs = {'class' : 'department'}):
        dep = li.text.strip()
        if dep in boring:
            keepit = False
            print '   skip', dep
        else:
            rec['note'].append(dep)
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'textblock'}):
        rec['abs'] = div.text.strip()
    #author
    for p in artpage.body.find_all('p', attrs = {'class' : 'persons'}):
        rec['autaff'] = [[ p.text.strip(), publisher ]]
    #FFT
    for li in artpage.body.find_all('li', attrs = {'class' : 'available'}):
        for a in li.find_all('a'):
            rec['hidden'] = a['href']
    if keepit:
        print '     ', rec.keys()
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
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
    
