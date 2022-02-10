# -*- coding: utf-8 -*-
#harvest theses from Surrey U.
#JH: 2021-12-12

from time import sleep
import urllib2
from json import loads
import getopt
import sys
import os
import ejlmod2
import codecs
import datetime
import re
import classifier

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Surrey U.'

jnlfilename = 'THESES-SURREY-%s' % (stampoftoday)

recs = []
rpp = 10
pages = 20
undepartments = ['Department of Mechanical Engineering Sciences',
                 'Centre for Environmental Strategy',
                 'Centre for Vision Speech and Signal Processing',
                 'Centre for Vision, Speech and Signal Processing',
                 'Centre of Environment and Sustainability',
                 'Clinical and Experimental Medicine',
                 'Department of Biochemical Sciences',
                 'Department of chemical and process engineering',
                 'Department of Chemical Engineering',
                 'Department of Chemistry; Faculty of Engineering and Physical Sciences',
                 'Department of Electrical and Electronic Engineering, Institute for Communication Systems, 5G Innovation Centre',
                 'Department of Mechanical Engineering',
                 'Department of Microbial Sciences',
                 'Electrical and Electronic Engineering',
                 'EPSRC Centre for Doctoral Training in Micro- and NanoMaterials and Technologies',
                 'Faculty of Engineering and Physical Sciences',
                 'Faculty of Health and Medical Sciences; School of Psychology',
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
                 #'Department of Computer Science',
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
                 'Economics.', 'Faculty of Arts and Social Sciences; School of Economics',
                 'School of Arts', 'Faculty of Arts and Social Sciences; School of Law',
                 'Faculty of Arts and Social Sciences; School of Hospitality and Tourism Management',
                 'Surrey Space Centre',
                 'Department of Mathematics',
                 'Psychology.', 'Faculty of Arts and Social Sciences; School of Literature and Languages',
                 'Department of Psychology',
                 'Faculty of Health and Medical Sciences; School of Biosciences and Medicine',
                 'Faculty of Health and Medical Sciences; School of Veterinary Medicine',
                 'School of Management']

def get_sub_side(id):
    url = "https://openresearch.surrey.ac.uk/esplorows/rest/research/fullAssetPage/assets/"+str(id)+"?institution=44SUR_INST&language=en"
    print "["+url+"] --> Harvesting data"
    request = urllib2.Request(url)
    server_data = loads(urllib2.urlopen(request).read())['esploroAssetForPortalFullAssetPage']

    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'artlink' : url}

    #DOI
    try:
        for doi in server_data['entityModel']['identifiers']['assetIdentifiers']['DOI']:
            rec['doi'] = doi
    except:
        rec['doi'] = '20.2000/Surrey/' + str(id)
        rec['link'] = server_data['permalink']

    #keywords
    try:
        rec['keyw'] = server_data['entityModel']['keywords']['translationMap']['und']
    except:
        pass

    #title
    rec['tit'] = server_data['title']
    
    if server_data.get('licenseDetails') is not None:
        licenseDetails = server_data['licenseDetails']
        if licenseDetails.get('licenseLabel') is not None:
            rec['licence'] = {'url': licenseDetails.get('licenseURL'), 'statement': licenseDetails.get('licenseLabel')}
            if server_data.get('pdfFileGSUrl') is not None:
                rec['FFT'] = server_data['pdfFileGSUrl']
        else:
            if server_data.get('pdfFileGSUrl') is not None:
                rec['hidden'] = server_data['pdfFileGSUrl']
    rec['date'] = server_data['date']
    rec['abs'] = server_data['description']
    
    # Get the authors
    rec['autaff'] = []
    for author in server_data['creators']:
        name = author['displayName']
        rec['autaff'].append([name])
        if 'orcid' in author.keys():
            rec['autaff'][-1].append('ORCID:'+author['orcid'])
        rec['autaff'][-1].append(publisher)

    # Get the advisors
    rec['supervisor'] = []
    for advisor in server_data['contributors']:
        if 'role' in advisor.keys():
            if advisor['role'] == 'Supervisor' and advisor['displayName'] != 'Surrey, University of':
                rec['supervisor'].append([advisor['displayName']])
                if 'orcid' in advisor.keys():
                    rec['supervisor'][-1].append('ORCID:'+advisor['orcid'])
                if 'affiliationName' in advisor.keys():
                    rec['supervisor'][-1].append(advisor['affiliationName'])

    #department and pages
    keepit = True
    for detail in server_data['details']:
        if detail['code'] == 'esploroAssetModel.general.assetAffiliation':
            dep = detail['value']
            if dep in undepartments:
                print '  skip "%s"' % (dep)
                keepit = False
            else:
                rec['note'].append(dep)
        elif detail['code'] == 'esploroAssetModel.general.pages':
            rec['pages'] = detail['value']
    if keepit: 
        recs.append(rec)
        print '  ', len(recs), rec.keys()

for page in range(pages):
    print "\n-- Accessing Page %i/%i ---" % (page+1, pages)
    #index_url = "https://openresearch.surrey.ac.uk/esplorows/rest/research/simpleSearch/assets?institution=44SUR_INST&q=any,contains,Dissertations%20OR%20Thesis&scope=Research&tab=Research&offset="+str(page)+"&limit=10&sort=rank&lang=en&enableAsteriskSearch=false&qInclude=facet_topic,exact,Physics"
    index_url = "https://openresearch.surrey.ac.uk/esplorows/rest/research/simpleSearch/assets?q=any,contains,Dissertations%20OR%20Thesis&page=1&institution=44SUR_INST&scope=ResearchETD&offset="+str(page*rpp)+"&limit="+str(rpp)+"&sort=date_d"
    req = urllib2.Request(index_url)
    index_page = loads(urllib2.urlopen(req).read())
    assets = index_page['assets']
    for asset in assets:
        if asset['resourceType'] == 'etd.doctoral':
            get_sub_side(asset['id'])
            sleep(5)
        else:
            print asset['resourceType'] 
    sleep(10)

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

