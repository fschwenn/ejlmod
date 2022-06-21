# -*- coding: utf-8 -*-
#harvest theses from Florida U.
#FS: 2021-04-29

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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Florida U.'

rpp = 24
pages = 20
startyear = now.year-1
stopyear = now.year
boring = ['aerodynamics', 'birds', 'disease', 'religion', 'archaeology', 'hormones',
          'biocollections', 'dental', 'aircraft', 'rhetoric', 'potato', 'paleontology',
          'aegypti', 'aerosol', 'agarose', 'andes', 'anthropocene', 'antimicrobial',
          'aquaculture', 'artists', 'autism', 'bacteria', 'biomarker', 'brain',
          'burnout', 'cardiovascular', 'caregivers', 'crispr', 'diabetes', 'drugs',
          'emotion', 'everglades', 'fiction', 'fish', 'fungicide', 'geography',
          'healthcare', 'implant', 'mammal', 'medical', 'microbiology', 'microbiome',
          'middle-school', 'mitochondria', 'nutrition', 'odor', 'organic', 'orthodontic',
          'painting', 'peanut', 'pediatric', 'peru', 'phylogenetic', 'poems', 'poverty',
          'psychology', 'queer', 'renewable', 'soil', 'spanish', 'stigma', 'telehealth',
          'terpenoids', 'terrorism', 'therapy', 'tuberculosis', 'urbanization', 'urban',
          'wetlands', 'wildlife', 'womanism', 'women', 'zika', 'art', 'citrus', 'disease',
          'literature', 'workplace', 'tourism', 'world-war-ii', 'voronoi', 'urban planning',
          'sports', 'spanish', 'shipwrecks', 'satire', 'reimbursement', 'hellenistic', 
          'parkinsons', 'lionfish', 'alzheimers', 'vitamins', 'vernacular-architecture',
          'veterinary-dermatology', 'vegetable', 'ancomycin', 'usambara', 'urban planning', 
          'migration', 'technology', 'agriculture', 'america', 'ecology', 'equity',
          'feminism', 'food', 'hiv', 'pain', 'perceptions', 'poetry', 'social', 'teachers',
          'teacher', 'cancer', 'gender', 'genetics', 'health', 'obesity', 'psychosocial',
          'violence', 'children', 'rural', 'climate', 'education', 'tomato', 'sustainability',
          'Soil science', 'Cultured cells', 'music', 'marketing', 'Human organs', 'Genetic mutation',
          'Consumer research', 'Agonists', 'The Everglades', 'Resins', 'Phenotypic traits',
          'hydrogels', 'Gender roles', 'Disease risks', 'Dehydrogenases', 'Cognitive impairment',
          'beef', 'ATP binding cassette transporters', 'African American studies', 'Vegetation canopies',
          'trauma', 'Textual collocation', 'Symptomatology', 'Soil temperature regimes',
          'osteoarthritis', 'Modern art', 'Miami-Dade County', 'metabolism', 'Korean culture',
          'herbicide', 'habitat', 'Chinese culture', 'Cell lines', 'anthropology', 'African art', 
          'fishermen', 'graffiti', 'literacy']

boring += ["Accounting", "Advertising", "Aerospace Engineering", "Agricultural and Biological Engineering",
           "Agricultural Education and Communication", "Agronomy", "Animal Molecular and Cellular Biology",
           "Animal Sciences", "Anthropology", "Applied Physiology and Kinesiology", "Architecture",
           "Art and Art History", "Art History", "Behavioral Science and Community Health",
           "Biochemistry and Molecular Biology", "Biochemistry and Molecular Biology (IDP)", "Biology",
           "Biomedical Engineering", "Biostatistics", "Botany", "Building Construction", "Geology", 
           "Business Administration", "Chemical Engineering", "Chemistry", "Civil and Coastal Engineering",
           "Civil Engineering", "Classical Studies", "Classics", "Clinical and Health Psychology",
           "Communication Sciences and Disorders",
           #"Computer and Information Science and Engineering",
           "Counseling and Counselor Education", "Counseling Psychology", "Creative Writing",
           "Criminology, Law, and Society", "Curriculum and Instruction", "Curriculum and Instruction (CCD)",
           "Curriculum and Instruction (CUI)", "Curriculum and Instruction (ISC)", "Dental Sciences",
           "Dentistry", "Design, Construction and Planning", "Design, Construction, and Planning",
           "Design, Construction, and Planning Doctorate", "Digital Arts and Sciences", "Geological Sciences", 
           "Early Childhood Education", "Economics", "Educational Leadership", "Educational Psychology",
           "Electrical and Computer Engineering", "English", "English Education", "Entomology and Nematology",
           "Environmental and Global Health", "Environmental Engineering Sciences", "Environmental Horticulture", 
           "Clinical Investigation (IDP)", "Coastal and Oceanographic Engineering", "Epidemiology",
           "Family, Youth and Community Sciences", "Finance, Insurance and Real Estate", "Genetics (IDP)", 
           "Fisheries and Aquatic Sciences", "Food and Resource Economics", "Food Science", "Geography", 
           "Food Science and Human Nutrition", "Forest Resources and Conservation", "French and Francophone Studies", 
           #"Computer Engineering", "Computer Science",
           "Construction Management", "Genetics and Genomics", 
           "German", "Health and Human Performance", "Health Education and Behavior", "Health Services Research",
           "Health Services Research, Management, and Policy", "Higher Education Administration",
           "Historic Preservation", "History", "Horticultural Sciences", "Human-Centered Computing",
           "Human Development and Organizational Studies in Education", "Immunology and Microbiology (IDP)",
           "Industrial and Systems Engineering", "Information Systems and Operations Management", "Marketing", 
           "Interdisciplinary Ecology", "Interior Design", "Journalism and Communications", "Landscape Architecture",
           "Language, Literature and Culture", "Latin", "Latin American Studies", "Linguistics", "Management",
           "Marriage and Family Counseling", "Mass Communication", "Materials Science and Engineering",
           "Mechanical and Aerospace Engineering", "Mechanical Engineering", "Medical Sciences", "French",
           "Medicinal Chemistry", "Medicine", "Mental Health Counseling", "Microbiology and Cell Science",
           "Molecular Cell Biology (IDP)", "Molecular Genetics and Microbiology", "Museology", "Music",
           "Music Education", "Neuroscience (IDP)", "Nuclear and Radiological Engineering", "Religion", 
           "Nuclear Engineering Sciences", "Nursing", "Nursing Sciences", "Nutritional Sciences", 
           "Pharmaceutical Outcomes and Policy", "Pharmaceutical Sciences", "Pharmaceutics", "Pharmacodynamics",
           "Pharmacology and Therapeutics (IDP)", "Pharmacotherapy and Translational Research", "Philosophy",
           "Physiology and Functional Genomics (IDP)", "Physiology and Pharmacology (IDP)", "Sociology", 
           "Plant Molecular and Cellular Biology", "Plant Pathology", "Political Science", "Statistics", 
           "Political Science - International Relations", "Psychology", "Public Health", "Sport Management", 
           "Recreation, Parks and Tourism", "Recreation, Parks, and Tourism", "Rehabilitation Science",
           "Research and Evaluation Methodology", "Romance Languages", "School Psychology", "Science Education",
           "Sociology and Criminology &amp; Law", "Soil and Water Science", "Soil and Water Sciences", "Spanish",
           "Spanish and Portuguese Studies", "Special Education", "Speech, Language and Hearing Sciences", 
           "Special Education, School Psychology and Early Childhood Studies", "Sustainable Construction",
           "Teaching and Learning", "Tourism and Recreation Management", "Tourism, Hospitality, & Event Management",
           "Tourism, Recreation, and Sport Management", "Urban and Regional Planning", "Veterinary Medical Sciences",
           "Veterinary Medicine", "Wildlife Ecology and Conservation", "Women's Studies", "Zoology",
           "Occupational Therapy", "Romance Languages and Literatures"]
boring += ['Ed.D.', 'M.A.M.C.', 'M.A.', 'M.H.P.', 'M.S.C.M.', 'M.S.', 'M.U.R.P.', 'B.S.'] 


jnlfilename = 'THESES-FloridaU-%s' % (stampoftoday)

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
driver_options = Options()
driver_options.headless = True
driver = webdriver.Chrome(options=driver_options)
for page in range(pages):
    tocurl = 'https://ufdc.ufl.edu/results?datehi=' + str(stopyear) + '-31-12&datelo=' + str(startyear) + '-01-01&filter=type%3Atheses&page=' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    #try:
    if 1>0:
        driver.implicitly_wait(60)
        driver.get(tocurl)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'BriefView_container__2e-2g')))
        tocpage = BeautifulSoup(driver.page_source, features="lxml")
        sections = tocpage.find_all('article', attrs = {'class' : 'BriefView_container__2e-2g'})
        for section in sections:
            for div in section.find_all('div', attrs = {'class' : 'BriefView_title__1OtwX'}):
                for a in div.find_all('a'):
                    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [], 'restricted' : False, 'autaff' : []}
                    rec['link'] =  'https://ufdc.ufl.edu' + a['href']
                    #marc xml works only for some records
                    rec['artlink'] =  re.sub('^\/(..)(..)(..)(..)(..)\/(.*)\/citation', r'https://ufdcimages.uflib.ufl.edu/\1/\2/\3/\4/\5/\6/marc.xml', a['href'])
                    rec['doi'] = '20.2000/FloridaU' + re.sub('\/citation', '', a['href'])
                    if not rec['doi'] in uninterestingDOIS:
                        prerecs.append(rec)
    #except:
    #    print ' could not load "%s"' % (tocurl)
    #    break
    time.sleep(10)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    embargo = False
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    #TRY MARC XML
    artfilename = '/tmp/florida_%s' % (re.sub('\W', '', rec['artlink']))
    if not os.path.isfile(artfilename):
        os.system('wget -O %s -q "%s"' % (artfilename, rec['artlink']))
        time.sleep(5)
    inf = open(artfilename, 'r')
    lines = inf.readlines()
    inf.close()
    artpage = BeautifulSoup(''.join(lines), features="lxml")
    #author
    for df in artpage.find_all('datafield', attrs = {'tag' : '100'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['autaff'] = [[ re.sub('\.$', '', sf.text.strip()) ]]
    #title
    for df in artpage.find_all('datafield', attrs = {'tag' : '245'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['tit'] = sf.text.strip()
    #date
    for df in artpage.find_all('datafield', attrs = {'tag' : '260'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'c'}):
            rec['date'] = re.sub('\.$', '', sf.text.strip())
    #keywords
    for df in artpage.find_all('datafield', attrs = {'tag' : '653'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['keyw'].append(sf.text.strip())
    #pages
    for df in artpage.find_all('datafield', attrs = {'tag' : '300'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            sft = sf.text.strip()
            if re.search('\d+ pages', sft):
                rec['pages'] = re.sub('.*?(\d+) pages.*', r'\1', sft)
            elif  re.search('\d+ p\.\)', sft):
                rec['pages'] = re.sub('.*?(\d+) p\..*', r'\1', sft)
    #abstract
    for df in artpage.find_all('datafield', attrs = {'tag' : '520'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['abs'] = sf.text.strip()
    #department
    for df in artpage.find_all('datafield', attrs = {'tag' : '690'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            dep = re.sub('(.*) thesis,.*', r'\1', sf.text.strip())
            if dep in boring:
                keepit = False
                print '   skip "%s"' % (dep)
            else:
                rec['note'].append(dep)
    #500
    for df in artpage.find_all('datafield', attrs = {'tag' : '500'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            sft = sf.text.strip()
            #supervisor
            if re.search('^Advisor:', sft):
                rec['supervisor'].append([re.sub('.*: *', '', sft)])
            #department
            elif re.search('^Major department:', sft):
                dep = re.sub('Major department: *', '', sft)
                dep = re.sub('\.$', '', dep).strip()
                if dep in boring:
                    keepit = False
                    print '   skip "%s"' % (dep)
                else:
                    rec['note'].append(dep)
    #degree
    for df in artpage.find_all('datafield', attrs = {'tag' : '502'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            if re.search('Thesis \(', sf.text):
                degree = re.sub('Thesis \((.*?)\).*', r'\1', sf.text.strip())
                if degree in boring:
                    print '  skip "%s"' % (degree)
                    keepit = False
                elif degree != 'Ph.D.':
                    rec['note'].append(degree)
    #complete
    dfs = artpage.find_all('datafield')
    #for df in dfs:
    #    for sf in df.find_all('subfield'):
    #        rec['note'].append('[MARC] %s%s : %s' % (df['tag'], sf['code'], sf.text.strip()))
    #IF MARC XML DOES NOT WORK
    if not dfs:
        time.sleep(1)
        print '     try', rec['link']
        try:
            driver.get(rec['link'])
            #WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'my-3')))
            artpage = BeautifulSoup(driver.page_source, features="lxml")
            #print artpage
            time.sleep(5)
            for meta in artpage.head.find_all('meta'):
                if meta.has_attr('property'):
                    #title
                    if meta['property'] == 'title':
                        rec['tit'] = meta['content']
            for div in artpage.body.find_all('div', attrs = {'class' : 'my-3'}):
                for a in div.find_all('a'):
                    if a.has_attr('href'):
                        #author
                        if re.search('filter=creator:', a['href']):
                            rec['autaff'] = [[ re.sub('.*filter=creator: *', '', a['href']) ]]
                        #date
                        elif re.search('publication_date=', a['href']):
                            rec['date'] = a.text.strip()
                #pages
                if re.search('\d+ pages\)', div.text):
                    rec['pages'] = re.sub('.*?(\d+) pages.*', r'\1', div.text.strip())
            for div in artpage.body.find_all('div', attrs = {'class' : 'content-css'}):
                for span in div.find_all('span'):
                    spant = span.text.strip()
                    if re.search('Major department: '):
                        dep = re.sub('Major department: ', '', spant)
                        dep = re.sub('\.$', '', dep).strip()
                        if dep in boring:
                            keepit = False
                            print '   skip "%s"' % (dep)
                        else:
                            rec['note'].append(dep)
            if not 'tit' in rec.keys() or not rec['autaff']:
                embargo = True
                print '    failed'                
        except:
            embargo = True
            print '    failed'
    
    


    if keepit:
        if not embargo and rec['autaff']:
            rec['autaff'][-1].append(publisher)
            print'  ', rec.keys()
            recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['doi'])

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


ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()
