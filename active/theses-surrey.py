# -*- coding: utf-8 -*-
#harvest theses from Surrey U.
#FS: 2020-03-03

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
import requests

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Surrey U.'


jnlfilename = 'THESES-SURREY-%sB' % (stampoftoday)

undepartments = ['Department of Mechanical Engineering Sciences',
                 'Centre for Environmental Strategy',
                 'Centre for Vision Speech and Signal Processing',
                 'Centre for Vision, Speech and Signal Processing',
                 'Centre of Environment and Sustainability',
                 'Clinical and Experimental Medicine',
                 'Department of Biochemical Sciences',
                 'Department of chemical and process engineering',
                 'Department of Chemical Engineering',
                 'Department of Electrical and Electronic Engineering, Institute for Communication Systems, 5G Innovation Centre',
                 'Department of Mechanical Engineering',
                 'Department of Microbial Sciences',
                 'Electrical and Electronic Engineering',
                 'EPSRC Centre for Doctoral Training in Micro- and NanoMaterials and Technologies',
                 'Faculty of Engineering and Physical Sciences',
                 'Institute for Communication Systems',
                 'Mechanical Engineering',
                 'Nutritional Sciences / School of Biosciences and Medicine',
                 'School of Biosciences & Medicine',
                 'School of Biosciences and Medicine, Department of Microbial and Cellular Sciences',
                 'School of Biosciences and Medicine - Department of Nutritional Sciences',
                 'School of Biosciences and Medicine, Department of Nutritional Sciences',
                 'School of Business',
                 'School of Electronic Engineering',
                 'School of English and Languages',
                 'Civil and Environmental Engineering',
                 'Department of Electrical and Electronic Engineering - Institute for Communication Systems',
                 'Department of Politics',
                 'School of Law',
                 'School of Veterinary Medicine',
                 'Department of Electronic Engineering',
                 'Department of Music and Media',
                 'Guildford School of Acting',
                 'School of Health Sciences',
                 'School of Economics',
                 'Department of Chemistry',
                 'Department of Civil and Environmental Engineering',
                 'Department of Computer Science',
                 'Department of Sociology',
                 'Centre for Environment and Sustainability',
                 'School of Hospitality and Tourism Management',
                 'Department of Chemical and Process Engineering',
                 'School of Literature and Languages',
                 'Surrey Business School',
                 'Department of Mechanical Engineering Sciences',
                 'School of Biosciences and Medicine',
                 'Department of Electrical and Electronic Engineering',
                 'School of Psychology',
                 'Centre for Vision, Speech and Signal Processing (CVSSP)',
                 'Advanced Technology Institute, Faculty of Engineering and Physical Sciences.',
                 'Advanced Technology Institute.',
                 'Biochemical Sciences.',
                 'Centre for Biomedical Engineering',
                 'Centre for Communications Systems Research, Faculty of Engineering and Physical Sciences',
                 'Centre for Communication System Research',
                 'Centre for Communication Systems Research, Department of Electronic Engineering',
                 'Centre for Communication Systems Research, Faculty of Engineering and Physical Sciences',
                 'Centre for Communication Systems',
                 'Centre For Doctoral Training in Micro- And NanoMaterials and Technologies (MiNMaT)',
                 'Centre for Doctoral Training in Micro- and NanoMaterials and Technologies',
                 'Centre for Doctoral Training in Micro and Nano Materials and Technology',
                 'Centre for Environmental Strategy (CES)',
                 'Centre for Environmental Strategy.',
                 'Centre For Environmental Strategy',
                 'Centre for Translation Studies - School of English and Languages',
                 'Centre for Vision Speech and Signal Processing (CVSSP)',
                 'Centre of Environmental Strategy',
                 'Centre of Vision, Speech and Signal Processing',
                 'Chemical and Process Engineering Department',
                 'Chemical and Process Engineering.',
                 'Chemical and Processing Engineering',
                 'Chemical Engineering',
                 'Chemical Sciences',
                 'Chemical Sciences.',
                 'Chemistry Department',
                 'Civil and Environmental Engineering Department',
                 'Civil, Chemical & Environmental Engineering',
                 'Civil Engineering',
                 'College of Engineering and Physical Sciences',
                 'Culture, Media and Communication.',
                 'Deparment of Mechanical Engineering',
                 'Departement of Civil and Environmental Engineering',
                 'Department od Electrical and Electronic Engineering',
                 'Department of Biomedical Engineering',
                 'Department of Biomedical Sciences',
                 'Department of Business Studies',
                 'Department of Cellular and Microbial Sciences',
                 'Department of Chemical Engineering (DEPARTAMENTO DE INGENIERÍA QUÍMICA)',
                 'Department of Chemistry.',
                 'Department of Civil and Enviromental Engineering',
                 'Department of Civil, and Environmental Engineering',
                 'Department of Civil and Environmental Health Engineering',
                 'Department of Computing, School of Electronics and Physical Sciences.',
                 'Department of Dance, Film and Theatre Studies',
                 'Department of Dance, Film and Theatre',
                 'Department of Diabetes and Metabolic Medicine.',
                 'Department of Economics.',
                 'Department of Electrical and Electronic Engineeering',
                 'Department of Electrical and Electronic Engineering',
                 'Department of Electrical and Electronic Enginnering',
                 'Department of Electrical Electronic Engineering',
                 'Department of Electric and Electronic Engineering',
                 'Department of Electronic and Electrical Engineering',
                 'Department of Electronics and Physical Sciences.',
                 'Department of Engineering',
                 'Department of English and Languages',
                 'Department of English',
                 'Department of Health and Medical Sciences.',
                 'Department of Health and Social Care.',
                 'Department of Health Policy and Management',
                 'Department of Languages and Translation Studies',
                 'Department of Materials Science',
                 'Department of Microbial Sciences.',
                 'Department of Music and Sound Recording.',
                 'Department of Music',
                 'Department of Nutritional Sciences (Diabetes and metabolic medicine)',
                 'Department of Political, International & Policy Studies',
                 'Department of Political, International and Policy Studies',
                 'Department of Psychology & Digital World Research.',
                 'Department of Psychology, Faculty of Arts and Huma.',
                 'Department of Psychology, Faculty of Human Science.',
                 'Department of Psychology, School of Human Science.',
                 'Department of Sociology, Faculty of Arts and Human Sciences.',
                 'Department of Sociology, School of Human Sciences.',
                 'Depatment of Mechanical Engineering Sciences',
                 'Division of Health and Social Care.',
                 'Division of Microbial Sciences.',
                 'Division of Nutritional Sciences',
                 'Division of Nutritional Sciences.',
                 'Division of Nutrition and Food Science',
                 'Division of Nutrition, Dietetics and Food Science.',
                 'Electronic and Electrical Engineering',
                 'English',
                 'English.',
                 'Environmental and Human Sciences Division. Forest Research',
                 'Faculty of Arts and Human Sciences.',
                 'Faculty of Biomedical and Molecular Sciences.',
                 'Faculty of Electronics and Physical Sciences, Centre for Communication Systems Research',
                 'Faculty of Electronics and Physical Sciences.',
                 'Faculty of Engineering and Physical Sciences; Surrey Space Centre',
                 'Faculty of Health and Medical Science, Division of Health and Social Care.',
                 'Faculty of Health and Medical Science',
                 'Faculty of Management and Law.',
                 'Health and Social Sciences',
                 'IJLAB, Centre for Communication Systems Research',
                 'I LAB, Centre for Communication Systems Research',
                 'Insitute of Communications Systems, 5G Innovation Center',
                 'Institute of Communication Systems',
                 'Institute of Educational Technology',
                 'Institute of Sound and Recording',
                 'Institute of Sound Recording, Faculty of Arts and Human Sciences',
                 'Mechanical and Engineering Sciences',
                 'Mechanical Engineering Sciences (MES)',
                 'Mech, Med & Aero Engineering',
                 'Medical Oncology',
                 'Micro- and NanoMaterials and Technologies CDT',
                 'microbial and cellular sciences',
                 'Microbial Sciences Division',
                 'Minimal Access Therapy Training Unit',
                 'Music and Sound Recording',
                 'Music',
                 'Nutrition Department',
                 'Nutrition Sciences',
                 'Pharmacoepidemiology.',
                 'Politics.',
                 'Postgraduate Medical School',
                 'Postgraduate Medical School.',
                 'Royal Holloway',
                 'School od Management',
                 'School of Biological Sciences',
                 'School of Biomedical and Medicine',
                 'School of Biomedical and Molecular Science',
                 'School of Bisciences and Medicine',
                 'School of Chemical Process Engineering',
                 'School of Chemistry',
                 'School of Culture Media and Communication',
                 'school of electronics and computer science',
                 'School of Engineering.',
                 'School of Health and Medical Sciences',
                 'School of Health and Social Sciences',
                 'School of hospitality and Tourism Management',
                 'School of Hospitality and Tourism',
                 'School of Human Sciences',
                 'School of Human Sciences.',
                 'School of Management and Law',
                 'School of Mathematics',
                 'School of Nursing and Midwifery',
                 'School of Nutritional Science',
                 'School of Oriental and African Studies',
                 'School of Political, International and Policy Studies',
                 'School of Politics',
                 'School of Psychology',
                 'School of Pyschology',
                 'School of Social Sciences (Sociology)',
                 'Space Structures Research Centre',
                 'Surrey Business School (SBS)',
                 'Surrey Morphology Group, School of English and Languages',
                 'Surrey Space Centre, Faculty of Electronics and Physical Sciences',
                 'Sustainability for Engineering and Energy Systems',
                 'The Centre for Environment and Sustainability',
                 'The Department of Electrical and Electronic Engineering',
                 'The Department of Electronic Engineering',
                 'Department of Aeronautics',
                 'Department of Civil Engineering',
                 'Department of Clinical and Experimental Medicine',
                 'Department of Clinical Psychology',
                 'Department of Environmental Technology.',
                 'Department of Mechanical Engineering and Sciences',
                 'Department of Mechanical Engineering Science',
                 'Department of Music and Sound Recording',
                 'Department of Sociology.',
                 'Division of Mechanical, Medical and Aerospace Engineering',
                 'Electronic Engineering',
                 'Microbial and Cellular Sciences',
                 'School of Bioscience and Medicine',
                 'School of Biosciences',
                 'School of Electrical and Electronic Engineering',
                 'School of Electronics and Physical Sciences',
                 'School of Health and Social Care',
                 'School of Management Studies for the Service Sector',
                 'School of Social Sciences',
                 'Chemical and Process Engineering',
                 'Department of Economics',
                 'Department of Psychology, School of Human Sciences.',
                 'Division of Health and Social Care',
                 'Electronic Engineering.',
                 'Faculty of Arts and Human Sciences',
                 'Faculty of Management and Law',
                 'Music and Sound Recording.',
                 'School of Electronics and Physical Sciences.',
                 'School of Engineering',
                 'Sociology',
                 'Chemistry',
                 'Chemistry.',
                 'Department of Psychology, Faculty of Arts and Human Sciences.',
                 'Department of Psychotherapeutic and Counselling Psychology.',
                 'Faculty of Health and Medical Sciences',
                 'Health and Social Care.',
                 'Political, International and Policy Studies.',
                 'School of Electronics and Computer Science',
                 'School of Management.',
                 'Unspecified',
                 'Department of Nutritional Sciences',
                 'Institute of Sound Recording',
                 'Psychology',
                 'Department of Microbial and Cellular Sciences',
                 'Faculty of Health and Medical Sciences.',
                 'Sociology.',
                 'Centre for Communication Systems Research',
                 'Faculty of Engineering and Physical Sciences.',
                 'Advanced Technology Institute',
                 'Mechanical Engineering Sciences',
                 'Department of Psychology.',
                 'Economics.',
                 'School of Arts',
                 'Surrey Space Centre',
                 'Department of Mathematics',
                 'Psychology.',
                 'Department of Psychology',
                 'School of Management']


recs = []
for year in [now.year-1, now.year]:
    tocurl = 'http://epubs.surrey.ac.uk/cgi/exportview/type/thesis/%i/JSON/thesis_%i.js' % (year, year)
    tocjson = requests.get(tocurl).json()
    time.sleep(3)
    for recjson in tocjson:
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'year' : str(year), 'note' : [], 'autaff' : [], 'supervisor' : []}
        #department
        if 'department' in recjson.keys():
            rec['department'] = recjson['department']
            rec['note'].append(recjson['department'])
        #type
        if 'thesis_type' in recjson.keys():
            if recjson['thesis_type'] != 'doctoral':
                rec['note'].append(recjson['thesis_type'])
        #date
        if 'date' in recjson.keys():
            rec['date'] = str(recjson['date'])
        #fulltext with license
        if 'documents' in recjson.keys():
            filesize = 0
            for document in recjson['documents']:
                if 'mime_type' in document.keys() and re.search('pdf', document['mime_type']):
                    if 'date_embargo' in document.keys() and document['date_embargo'] > stampoftoday:
                        print '  embargo until %s' % (document['date_embargo'])
                    else:
                        docrec = {'link' : document['uri']}
                        if 'license' in document.keys():
                            docrec['license'] = re.sub('_', '-', document['license'].upper())
                        if document['files'][0]['filesize'] < filesize:
                            print '  file is smaller'
                        else:
                            rec['document'] = docrec
            if 'document' in rec.keys():
                if 'license' in rec['document'].keys():
                    rec['license'] = {'url' : rec['document']['license']}
                    rec['FFT'] = rec['document']['link']
                else:
                    rec['hidden'] = rec['document']['link']
        #keywords
        if 'keywords' in recjson.keys():
            rec['keyw'] = re.split(', ', recjson['keywords'])
        #DOI
        if 'id_number' in recjson.keys() and re.search('^10.15126', recjson['id_number']):
            rec['doi'] = recjson['id_number']
        elif 'uri' in recjson.keys():
            rec['doi'] = '20.2000/Surrey/' + re.sub('\W', '', recjson['uri'])
            rec['link'] = recjson['uri']
        #abstract
        if 'abstract' in recjson.keys():
            rec['abs'] = recjson['abstract']
        #title
        if 'title' in recjson.keys():
            rec['tit'] = recjson['title']
        #pages
        if 'pages' in recjson.keys():
            rec['pages'] = str(recjson['pages'])
        #author
        if 'creators' in recjson.keys():
            for author in recjson['creators']:
                rec['autaff'].append(['%s, %s' % (author['name']['family'], author['name']['given'])])
                #ORCID
                if 'orcid' in author.keys():
                    rec['autaff'][-1].append('ORCID:%s' % (author['orcid']))
                #email
                elif 'id' in author.keys() and author['id'] and re.search('@[a-z]+\.[a-z]', author['id']):
                    rec['autaff'][-1].append('EMAIL:%s' % (author['id']))
                #affiliation
                rec['autaff'][-1].append(publisher)
        #supervisor
        if 'contributors' in recjson.keys():
            for author in recjson['contributors']:
                if 'name' in author.keys():
                    rec['supervisor'].append(['%s, %s' % (author['name']['family'], author['name']['given'])])
                    #ORCID
                    if 'orcid' in author.keys():
                        rec['supervisor'][-1].append('ORCID:%s' % (author['orcid']))
                    #email
                    elif 'id' in author.keys() and author['id'] and re.search('@[a-z]+\.[a-z]', author['id']):
                        rec['supervisor'][-1].append('EMAIL:%s' % (author['id']))

        if 'department' in rec.keys() and rec['department'] in undepartments:
            print '  skip "%s"' % (rec['department'])
        else:
            recs.append(rec)
            print '  ', rec.keys()

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
