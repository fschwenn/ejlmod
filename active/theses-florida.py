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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Florida U.'

rpp = 20
pages = 50
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
           "Communication Sciences and Disorders", "Computer and Information Science and Engineering",
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
           "Computer Engineering", "Computer Science", "Construction Management", "Genetics and Genomics", 
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

jnlfilename = 'THESES-FloridaU-%sB' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://ufdc.ufl.edu/ufir/contains/brief/' + str(page+1) + '/?t=%22theses%22&f=GE&o=11'
    print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for section in tocpage.body.find_all('section', attrs = {'class' : 'sbkBrv_SingleResult'}):
        keepit = True
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [], 'restricted' : False}
        for span in section.find_all('span', attrs = {'class' : 'RestrictedItemText'}):
            rec['restricted'] = True
        for span in section.find_all('span', attrs = {'class' : 'briefResultsTitle'}):
            for a in span.find_all('a'):
                rec['link'] =  a['href']
                rec['tit'] = a.text.strip()
                rec['doi'] = '20.2000/FloridaU/' + re.sub('.*edu\/', '', a['href'])
        for dl in section.find_all('dl'):
            for child in dl.children:
                try:
                    child.name
                except:
                    continue
                if child.name == 'dt':
                    dtt = child.text.strip()
                elif child.name == 'dd':
                    #date
                    if dtt == 'Publication Date:':
                        rec['date'] = child.text.strip()
                    #author
                    elif dtt == 'Creator:':
                        rec['autaff'] = [[ child.text.strip() ]]
                    #pages
                    elif dtt == 'Format:':
                        if re.search('\d\d p\.', child.text):
                            rec['pages'] = re.sub('.*?(\d\d+) p\..*', r'\1', child.text.strip())
                    #keywords
                    elif dtt == 'Subjects:':
                        rec['keyw'] = re.split(' \-\- ', child.text.strip())
                        for keyw in rec['keyw']:
                            if keyw in boring:
                                print '      skip', keyw
                                keepit = False
        if keepit:
            prerecs.append(rec)
    print '   %i theses so far' % (len(prerecs))
    time.sleep(10)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link']+ '/citation')
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']+ '/citation'), features="lxml")
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']+ '/citation'), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    for dl in  artpage.find_all('dl'):
        for child in dl.children:
            try:
                child.name
            except:
                continue
            if child.name == 'dt':
                dtt = child.text.strip()
            elif child.name == 'dd':
                #absract
                if dtt == 'Abstract:':
                    rec['abs'] = re.sub(' *\( *en *\) *$', '', child.text.strip())
                #disciplines
                elif dtt == 'Degree Disciplines:':
                    for a in child.find_all('a'):
                        disc = a.text.strip()
                        if disc in boring:
                            keepit = False
                            print '  skip', disc
                        else:
                            rec['note'].append('discipline: '+disc)
    if not rec['restricted']:
        for ul in artpage.body.find_all('ul', attrs = {'class' : 'sf-menu'}):
            for a in ul.find_all('a'):
                if a.text.strip() == 'PDF':
                    rec['hidden'] = a['href']
    rec['autaff'][-1].append(publisher)
    if keepit:
        print'  ', rec.keys()
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
