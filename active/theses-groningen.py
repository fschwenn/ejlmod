# -*- coding: utf-8 -*-
#harvest theses from Groningen U.
#FS: 2022-02-14

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

publisher = 'Groningen U.'

rpp = 50
pages = 20
jnlfilename = 'THESES-GRONINGEN-%s' % (stampoftoday)

boringdegrees = ['Master of Philosophy', 'Master of Science']
boringinstitutes = ['Education in Culture', 'Analytical Biochemistry', 'Arctic and Antarctic studies',
                    'Artificial Intelligence', 'Chemical Biology 2', 
                    'Drug Design', 'Effective Criminal Law', 'Electron Microscopy',
                    'Environmental Psychology', 'Etienne group', 'Faculty of Philosophy',
                    'Intelligent Systems', 'Molecular Dynamics', 'Culture, Language & Technology',
                    'Nanostructures of Functional Oxides', 'Sociology/ICS', 'SOM EEF', 'SOM Marketing',
                    'SOM OPERA', 'Theoretical Chemistry', 'Theory and History of Psychology',
                    'Transboundary Legal Studies', 'Zernike Institute for Advanced Materials',
                    'Archaeology of Northwestern Europe', 'Beersma lab', 'Beukeboom lab',
                    'Biomolecular Chemistry & Catalysis', 'Biotechnology',
                    'Center for Language and Cognition (CLCG)',
                    'Center for Liver, Digestive and Metabolic Diseases (CLDM)',
                    'Chemical and Pharmaceutical Biology', 'Chemical Technology',
                    'Classical and Mediterranean Archaeology', 'Clinical Neuropsychology',
                    'Clinical Psychology and Experimental Psychopathology', 'Conservation Ecology Group',
                    'Culture, Language & Technology', 'Department of Social Sciences',
                    'Discrete Technology and Production Automation', 'Dugdale group',
                    'Energy and Sustainability Research Institute Gron.', 'Enzymology', 'Eriksson group',
                    'Experimental Psychology', 'Falcao Salles lab', 'Fontaine lab',
                    'Groningen Institute for Gastro Intestinal Genetics and Immunology (3GI)',
                    'Groothuis lab', 'Komdeur lab', 'Maan group', 'Molecular Genetics',
                    'Molecular Microbiology', 'Molecular Pharmacology', 'Van Dijk lab',
                    'Nanostructured Materials and Interfaces', 'Ocean Ecosystems',
                    'Organizational Psychology', 'Product Technology', 'Public Trust and Public Law',
                    'Research and Evaluation of Educational Effectiveness',
                    'Science Education and Communication', 'Tieleman lab', 'Van de Zande lab',
                    'Scientific Visualization and Computer Graphics', 'Smart Manufacturing Systems',
                    'Software Engineering', 'Solid State Materials for Electronics',
                    'Systems, Control and Applied Analysis', 'Cell Biochemistry',
                    'Damage and Repair in Cancer Development and Cancer Treatment (DARE)',
                    'Developmental and behavioural disorders in education and care: assessment and intervention',
                    'Developmental Psychology', 'Distributed Systems', 'Ethics, Social and Political Philosophy',
                    'Faculteit Medische Wetenschappen', 'Host-Microbe Interactions', 'Kas lab',
                    'Macromolecular Chemistry & New Polymeric Materials', 'Molecular Systems Biology',
                    'Palsbøll lab', 'Pharmaceutical Analysis', 'Pharmaceutical Technology and Biopharmacy',
                    'PharmacoTherapy, -Epidemiology and -Economics', 'Photophysics and OptoElectronics',
                    'Products and Processes for Biotechnology', 'Public Interests and Private Relationships',
                    'Research Centre for the Study of Democratic Cultures and Politics (DemCP)',
                    'Stratingh Institute for Chemistry', 'Surfaces and Thin Films', 'Synthetic Organic Chemistry',
                    'Teaching and Teacher Education', 'Advanced Production Engineering',
                    'Adv Res Ctr Nanolithog ARCNL', 'Billeter lab', 'Bioproduct Engineering', 'Both group',
                    'Chemical Biology 1', 'Chemistry of (Bio)organic Materials and Devices',
                    'Comparative Study of Religion', 'Cosmic Frontier', 'Department of Humanities',
                    'Discourse and Communication (DISCO)', 'Eisel lab', 'Elizabeth Hosp, Dept Surg',
                    'Govers group', 'Greek Archaeology', 'Havekes lab', 'History of Philosophy',
                    'Isala Hosp, Dept Cardiol', 'Jewish, Christian and Islamic Origins',
                    'Law on Energy and Sustainability', 'Meerlo lab', 'Molecular Biophysics',
                    'Molecular Cell Biology', 'Molecular Immunology', 'Molecular Inorganic Chemistry',
                    'Mol Enzymol Groningen Biomol Sci & Biotechnol Ins', 'Nanomedicine & Drug Targeting',
                    'Olff group', 'Olivier lab', 'Palsbøll lab', 'Piersma group',
                    'Polymer Chemistry and Bioengineering', 'Protecting European Citizens and Market Participants',
                    'Psychometrics and Statistics', 'Radboud University Nijmegen Medical Centre',
                    'Research unit Medical Physics', 'Rijnstate Hosp, Dept Surg, Div Vasc Surg', 'Smit group',
                    'Social Psychology', 'Spaarne Hosp, Dept Pulm Dis', 'Sustainable Economy',
                    'Sust Entr. in a Circular Econ', 'System Chemistry', 'Theoretical Philosophy',
                    'UMC Utrecht, University of Utrecht, Dept Rehabil Nursing Sci & Sports',
                    'Univ Amsterdam, University of Amsterdam, University of Groningen, Acad Med Ctr, Dept Resp Med, Univ Groningen',
                    'University of Groningen, Faculty of Behavioural and Social Sciences',
                    'Groningen Biomolecular Sciences and Biotechnology',
                    'Groningen Institute for Organ Transplantation (GIOT)',
                    'Groningen Research Institute of Pharmacy', 'Urban and Regional Studies Institute',
                    'Univ. Giessen, Justus-Liebig-Universität Giessen, Fac. Psychologie und Sportwissenschaften, Institut für Psychologische Diagnostik',
                    'Univ Groningen, University of Groningen, Grad Sch Humanities', 'Univ Groningen, University of Groningen, Univ Med Ctr Groningen, Div Geriatr Med, Univ Ctr Geriatr Med',
                    'Univ Med Ctr Groningen, University of Groningen, Dept Surg, Div Vasc Surg',
                    'User-friendly Private Law', 'Van der Heide group', 'Van der Zee lab', 'Van Doorn group',
                    'Vrije Universiteit Amsterdam, Amsterdam', 'Wertheim lab', 'X-ray Crystallography']
                    
inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://research.rug.nl/en/publications/?type=%2Fdk%2Fatira%2Fpure%2Fresearchoutput%2Fresearchoutputtypes%2Fthesis%2Fdoc3&type=%2Fdk%2Fatira%2Fpure%2Fresearchoutput%2Fresearchoutputtypes%2Fthesis%2Fdoc&nofollow=true&format=&page=' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for li in tocpage.body.find_all('li', attrs = {'class' : 'list-result-item'}):
        for a in li.find_all('a', attrs = {'rel' : 'Thesis'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [], 'isbns' : []}
            rec['artlink'] = a['href']
        for span in li.find_all('span', attrs = {'class' : 'numberofpages'}):
            rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', span.text.strip())
        if not rec['artlink'] in uninterestingDOIS:
            prerecs.append(rec)
    time.sleep(5)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append('%s, %s' % (meta['content'], publisher))
                if meta['content'] in boringinstitutes:
                    keepit = False
                    print '   skip "%s"' % (meta['content'])
                else:
                    rec['note'].append(meta['content'])
            #doi
            elif meta['name'] == 'citation_doi':
                if re.search('^10.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
            #pdf
            elif meta['name'] == 'citation_pdf_url':
                if re.search('Complete_thesis', meta['content']):
                    rec['FFT'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] != 'English':
                    rec['language'] = meta['content']
    for tr in artpage.body.find_all('tr'):
        for th in tr.find_all('th'):
            tht = th.text.strip()
            for td in tr.find_all('td'):
                #ISBN
                if re.search('Print ISBN', tht):
                    for isbn in re.split(', ', td.text.strip()):
                        rec['isbns'].append([('a', re.sub('\-', '', isbn)), ('b', 'Print')])
                elif re.search('Electronic ISBNs', tht):
                    for isbn in re.split(', ', td.text.strip()):
                        rec['isbns'].append([('a', re.sub('\-', '', isbn)), ('b', 'Online')])
                #Supervisor
                elif re.search('Supervisor', tht):
                    for li in td.find_all('li'):
                        if re.search('Supervisor', li.text):
                            for span in li.find_all('span', attrs = {'class' : 'person'}):
                                rec['supervisor'].append([span.text.strip()])
                #Qualification
                elif re.search('Qualification', tht):
                    degree = td.text.strip()
                    if degree != 'Doctor of Philosophy':
                        if degree in boringdegrees:
                            print '   skip "%s"' % (degree)
                            keepit = False
                        else:
                            rec['note'].append(degree)
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'rendering_abstractportal'}):
        for div2 in div.find_all('div', attrs = {'class' : 'textblock'}):
            rec['abs'] = div2.text.strip()
    if keepit:
        if not 'doi' in rec.keys():
            rec['link'] = rec['artlink']
            rec['doi'] = '30.3000/Groningen/' + re.sub('\W', '', rec['link'][39:])
        print '  ', rec.keys()
        recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['artlink'])


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
