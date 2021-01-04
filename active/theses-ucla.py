# -*- coding: utf-8 -*-
#harvest theses from University of California
#FS: 2019-11-05

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
retfiles_path = '/afs/desy.de/user/l/library/proc/retinspire/retfiles'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

abbr = sys.argv[1]

numberofpages = 5-2
articlesperpage = 100
subjectstoskip = ['Biochemistry', 'LGBTQstudies', 'Classicalstudies', 'Microbiology', 'Informationscience', 
                  'Remotesensing', 'Filmstudies', 'Organicchemistry', 'Internationallaw', 
                  'Classicalliterature', 'Artificialintelligence', 'Genetics', 'Biomechanics', 
                  'AfricanAmericanstudies', 'Islamicstudies', 'Africanstudies', 'Philosophy',  
                  'Biophysics', 'Sustainability', 'EastEuropeanstudies', 'Environmentalstudies',  
                  'Musichistory', 'Management', 'Womensstudies', 'Cognitivepsychology',  
                  'Webstudies', 'Arthistory', 'Toxicology', 'Medicalimaging', 'Economictheory',  
                  'Masscommunication', 'Ecology', 'Nursing', 'Urbanplanning', 'Robotics',  
                  'Parasitology', 'Environmentalhealth', 'Theoreticalmathematics', 'Education',  
                  'Agriculture', 'AsianAmericanstudies', 'Statistics', 'Asianhistory',  
                  'Internationalrelations', 'Physicalanthropology', 'Physicalchemistry',  
                  'Macroecology', 'Publichealth', 'Geotechnology', 'Neurosciences', 'Biology',  
                  'Occupationalsafety', 'Asianstudies', 'Developmentalbiology', 'LatinAmericanhistory',  
                  'Planetology', 'Musicalcomposition', 'Nanotechnology', 'Immunology',  
                  'Educationalpsychology', 'Quantitativepsychology', 'Economics',  
                  'Electricalengineering', 'Architecture', 'Bioengineering', 'Pedagogy',  
                  'Chemistry', 'Archaeology', 'Finance', 'Judaicstudies', 'Africanhistory',  
                  'Dance', 'Translationstudies', 'Molecularbiology', 'Design', 'Ethnicstudies',  
                  'Americanstudies', 'Polymerchemistry', 'Slavicstudies', 'Laborrelations',  
                  'Linguistics', 'Climatechange', 'Psychology', 'Organizationtheory', 'Fluidmechanics',  
                  'Healthcaremanagement', 'Music', 'Medicine', 'Musictheory', 'Europeanhistory',  
                  'MaterialsScience', 'Americanhistory', 'Literature', 'Wildlifeconservation',  
                  'Geology', 'Socialwork', 'Epidemiology', 'Ophthalmology', 'Computationalchemistry',  
                  'Bioinformatics', 'Mechanicalengineering', 'Physiology', 'Environmentalgeology',  
                  'Highereducation', 'Language', 'Ancienthistory', 'Dentistry', 'Atmosphericchemistry',  
                  'History', 'Botany', 'Biostatistics', 'Environmentaleconomics', 'Electromagnetics',  
                  'Engineering', 'HistoryofOceania', 'Surgery', 'Energy', 'Frenchliterature',  
                  'Sociology', 'Physicaloceanography', 'Cellularbiology', 'LatinAmericanstudies',  
                  'Performingartseducation', 'Pharmacology', 'Evolutiondevelopment',  
                  'MiddleEasternstudies', 'Geophysics', 'Law', 'Civilengineering',  
                  'Chemicalengineering', 'Laboreconomics', 'Virology', 'Educationpolicy',  
                  'Biomedicalengineering', 'Foreignlanguageeducation', 'Politicalscience',  
                  'Demography', 'Logic', 'Publicpolicy', 'Culturalanthropology', 'Englishliterature',  
                  'Genderstudies', 'Americanliterature', 'LatinAmericanliterature', 
                  'Environmentalscience', 'Geography', 'Aging', 'Mentalhealth', 'Healthsciences', 
                  'Aero spaceengineering', 'Religion', 'Russianhistory', 'Conservationbiology', 
                  'Healtheducation', 'Optics', 'SouthAsianstudies', 'Behavioralsciences', 
                  'Oncology', 'Sociolinguistics', 'Sociolinguistics', 'Alternativemedicine', 
                  'Teachereducation', 'Theaterhistory', 'Businessadministration', 'Caribbeanstudies', 
                  'Clinicalpsychology', 'Artsmanagement', 'Libraryscience', 'Modernliterature', 
                  'Theater', 'NativeAmericanstudies', 'Educationalleadership', 'Gerontology', 
                  'Aesthetics', 'Performingarts', 'Environmentalengineering', 'Morphology', 
                  'Waterresourcesmanagement', 'Economichistory', 'Slavicliterature', 
                  'Medievalhistory', 'Operationsresearch', 'Scienceeducation', 'Artcriticism', 
                  'Geochemistry', 'Hydrologicsciences', 'Elementaryeducation', 'Regionalstudies', 
                  'Industrialengineering', 'Environmentaleducation', 'Alternativeenergy', 
                  'Geographicinformationscienceandgeodesy', 'Ethics', 'Educationalevaluation', 
                  'Earlychildhoodeducation', 'Folklore', 'Creativewriting', 'Physicalgeography', 
                  'Environmentaljustice', 'Kinesiology', 'Modernhistory', 'Mechanics', 
                  'Educationalphilosophy', 'Fashion', 'Sedimentarygeology', 'Endocrinology', 
                  'Arteducation', 'Computerscience', 'Italianliterature', 'Landscapearchitecture', 
                  'Pathology', 'Criminology', 'Communitycollegeeducation', 
                  'Culturalresourcesmanagement', 'Multimediacommunications', 
                  'Developmentalpsychology', 'Physicaltherapy', 'Museumstudies', 'Plantsciences', 
                  'Ancientlanguages', 'Biogeochemistry', 'Environmentallaw', 
                  'Pharmaceuticalsciences', 'Molecularphysics', 'Educationhistory', 
                  'PhilosophyofReligion', 'Bilingualeducation', 'Curriculumdevelopment', 
                  'Hydraulicengineering', 'Readinginstruction', 'Englishasasecondlanguage', 
                  'Rhetoric', 'Analyticalchemistry', 'Acoustics', 'Biblicalstudies', 'Paleoecology', 
                  'Scandinavianstudies', 'Asianliterature', 'Militaryhistory', 'Psychobiology', 
                  'Informationtechnology', 'Packaging', 'Behavioralpsychology', 'Zoology', 
                  'NorthAfricanstudies', 'Musiceducation', 'Worldhistory', 'SoutheastAsianstudies', 
                  'Epistemology', 'Specialeducation', 'Socialpsychology', 'Comparativeliterature', 
                  'Forestry', 'Foodscience', 'Medievalliterature', 'Physiologicalpsychology', 
                  'Secondaryeducation', 'Socialresearch', 'Nutrition', 'Environmentalmanagement', 
                  'Transportation', 'Peacestudies', 'Individualfamilystudies', 
                  'Educationaltestsmeasurements', 'Experimentalpsychology', 'Therapy',  
                  'Atmosphericsciences', 'Sciencehistory', 'Nanoscience', 'Banking', 'Sexuality',  
                  'Blackstudies', 'Finearts', 'Paleoclimatescience', 'Publichealtheducation',  
                  'Systematicbiology', 'NearEasternstudies', 'Spirituality', 'Canadianstudies',  
                  'Communication', 'Landuseplanning', 'Educationfinance', 'Holocauststudies',  
                  'Aerospaceengineering', 'Militarystudies', 'Disabilitystudies', 'Modernlanguage',  
                  'Germanliterature', 'Intellectualproperty', 'Highereducationadministration',  
                  'Organizationalbehavior', 'Occupationalpsychology', 'Blackhistory',  
                  'Africanliterature', 'Marketing', 'Mathematicseducation', 'Romanceliterature',  
                  'Educationaladministration', 'Socialstructure', 'Journalism',  
                  'Educationalsociology', 'Inorganicchemistry', 'Geomorphology', 'Systemsscience',  
                  'MiddleEasternhistory', 'Paleontology', 'Adulteducation', 'Europeanstudies',  
                  'Wildlifemanagement', 'HispanicAmericanstudies', 'Aquaticsciences',  
                  'Religioushistory', 'Educationaltechnology']
subjectstoskip += ['Meteorology', 'Agronomy', 'Chemicaloceanography', 'Vocationaleducation', 'Accounting',
                   'Lawenforcement', 'Agricultureeconomics', 'Petroleumengineering', 'Entomology',
                   'Middleschooleducation', 'Geologicalengineering', 'Speechtherapy', 'Oceanengineering',
                   'Naturalresourcemanagement', 'Limnology', 'Plantpathology', 'Languagearts',
                   'Marinegeology', 'Biologicaloceanography', 'Medicalethics', 'PacificRimstudies',
                   'Socialscienceseducation', 'Obstetrics', 'Multiculturaleducation', 'Entrepreneurship',
                   'Soilsciences', 'Sportsmanagement', 'Schoolcounseling', 'Urbanforestry',
                   'Comparativereligion', 'Counselingpsychology', 'Animalsciences', 'Balticstudies',
                   'Geobiology', 'Horticulture', 'Personalitypsychology', 'Recreation', 'Veterinaryscience',
                   'Agricultureengineering', 'Navalengineering', 'Automotiveengineering', 'Transportationplanning',
                   'Areaplanningdevelopment', 'Hightemperaturephysics', 'Petrology', 'Veterinaryscience']
subjectstoskip += ['Animalbehavior', 'ChemistryPharmaceutical', 'Neurobiology',
                   'HealthSciencesRehabilitationandTherapy', 'MolecularBiology', 'CellularBiology',
                   'BehavioralSciences', 'HealthSciencesImmunology', 'Medicalimagingandradiology',
                   'OccupationalHealth', 'HistoryofScience', 'BiologyBioinformatics', 'AnthropologyCultural',
                   'BiologyNeuroscience', 'EngineeringBiomedical', 'HealthSciences', 'BiophysicsGeneral',
                   'BiologyGeneral', 'BiomedicalEngineering', 'SociologyGeneral', 'BiologyMicrobiology',
                   'BiologyMolecular', 'Occupationalhealth', 'HealthSciencesDentistry', 'BiologyCell',
                   'AdultEducation', 'DevelopmentalBiology', 'ChemistryBiochemistry', 'HealthSciencesOncology',
                   'AnthropologyMedicalandForensic', 'PharmaceuticalSciences', 'HealthSciencesNursing',
                   'Plastics', 'HealthSciencesPharmacology', 'Obstetricsandgynecology', 'BiologyGenetics',
                   'BiophysicsMedical', 'Histology', 'BiologyAnimalPhysiology', 'Historyofscience',
                   'HealthSciencesEpidemiology', 'Animaldiseases']
subjectstoskip += ['Areaplanninganddevelopment', 'Businesseducation', 'Computerengineering',
                   'Fisheriesandaquaticsciences', 'Islamicculture', 'Metaphysics', 'Mineralogy',
                   'Molecularchemistry', 'Nuclearengineering', 'Plantbiology', 'Platetectonics',
                   'PoliticalScience', 'Publicadministration', 'SouthAfricanstudies', 'Statisticalphysics',
                   'SubSaharanAfricastudies', 'BritishandIrishliterature', 'Business', 'GLBTstudies', 
                   'Continentaldynamics', 'Agricultureeducation', 'Biographies', 'Theology', 'Biologicaloceanography',
                   'Philosophyofscience', 'Sociologyofeducation', 'Animaldiseases', 'MiddleEasternliterature',
                   'Cognitivepsychology', 'Materials Science', 'Public health', 'Demography',
                   'Theater', 'Politicalscience', 'Musictheory']
subjectstoskip += ['AnthropologyArchaeology', 'Architecturalengineering', 'Audiology',
                   'Canadianhistory', 'Caribbeanliterature', 'Cinematography',
		   'CommerceBusiness', 'Computationalphysics', 'EconomicsCommerceBusiness',
		   'EconomicsLabor', 'Environmentalphilosophy', 'Foreignlanguageinstruction',
		   'Forensicanthropology', 'Geophysicalengineering', 'Giftededucation',
		   'Instructionaldesign', 'Mining', 'Multimedia', 'Optometry', 'Patentlaw',
		   'Petroleumgeology', 'Physicaleducation', 'Quantitativepsychologyandpsychometrics',
		   'Rangemanagement', 'Religiouseducation', 'Systemscience',
		   'Technicalcommunication', 'Textileresearch', 'FrenchCanadianculture']

problematiclinks = ['https://escholarship.org/uc/item/3hv4z0z8', 'https://escholarship.org/uc/item/5gw3v7bf', 'https://escholarship.org/uc/item/69m6205w', 'https://escholarship.org/uc/item/49q2s5km', 'https://escholarship.org/uc/item/4xn23688', 'https://escholarship.org/uc/item/8tj5d61d', 'https://escholarship.org/uc/item/28w4j5xc', 'https://escholarship.org/uc/item/6972h04z']
#problematiclinks = []
hdr = {'User-Agent' : 'Magic Browser'}
campi = {'ucla' : 'UCLA, Los Angeles (main)', 'ucd' : 'UC, Davis (main)',
         'uci' : 'UC, Irvine (main)', 'ucb' : 'UC, Berkeley (main)',
         'ucr' : 'UC, Riverside (main)', 'ucsd' : 'UC, San Diego (main)',
         'ucsf' : 'UC, San Francisco', 'ucsb' : 'UC, Santa Barbara (main)',
         'ucsc' : 'UC, Santa Cruz (main)'}
publisher = campi[abbr]
recs = []
for i in range(numberofpages):
    tocurl = 'https://escholarship.org/uc/%s_etd/search?sort=desc&rows=%i&start=%i' % (abbr, articlesperpage, articlesperpage*i)
    print '---{ %i/%i }---{ %s }---'  % (i+1, numberofpages, tocurl)
    tocfilename = '/tmp/THESES-%s-%s.%i.%i.toc' % (abbr.upper(), stampoftoday, articlesperpage, i)
    if not os.path.isfile(tocfilename):
        os.system('wget -T 300 -t 3 -q -O %s "%s"' % (tocfilename, tocurl))
        time.sleep(10)
    inf = open(tocfilename, 'r')
    lines = ''.join(inf.readlines())
    tocpage = BeautifulSoup(lines)
    inf.close()
    #req = urllib2.Request(tocurl, headers=hdr)
    #tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'c-pub'})
    if len(divs) == 100:
        for div in divs:
            for h2 in div.find_all('h2'):
                for a in h2.find_all('a'):
                    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
                    rec['artlink'] = 'https://escholarship.org' + a['href']
                    rec['tit'] = a.text.strip()
                    if rec['artlink'] in problematiclinks:
                        print ' link "%s" is problematic' % (rec['artlink'])
                    else:
                        recs.append(rec)
    else:
        divs2 = re.split('<div class="c-pub">', lines)[1:]
        print 'BeautifulSoup failed to get all links (now %i instead of %i)' % (len(divs2), len(divs))
        i = 0
        for div in divs2:
            parts = re.split('<\/', div)
            i += 1
            print ' - ', i, len(parts), len(div)
            for part in parts:
                if re.search('<h2', part):
                    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
                    rec['artlink'] = 'https://escholarship.org' + re.sub('.*href="(.*?)".*', r'\1', part)
                    rec['tit'] = re.sub('.*<div class="c-clientmarkup">', '', part)
                    print rec['artlink']
                    break
            if rec['artlink'] in problematiclinks:
                print ' link "%s" is problematic' % (rec['artlink'])
            else:
                recs.append(rec)
    print '  ', len(recs)

i = 0
subjectrecs = {}
relevantrecs = []
for rec in recs:
    i += 1
    artfilename = '/tmp/THESES-%s-%s' % (abbr.upper(), re.sub('\W', '', rec['artlink'][32:]))
    print '---{ %i/%i }---{ %s }---{ %s }---' % (i, len(recs), rec['artlink'], artfilename)
    if not os.path.isfile(artfilename):
        os.system('wget -T 300 -t 3 -q -O %s "%s"' % (artfilename, rec['artlink']))
        time.sleep(10)
    inf = open(artfilename, 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    #withdrawn?
    withdrawn = False
    for div in artpage.find_all('div', attrs = {'class' : 'c-clientmarkup'}):
        if re.search('This item has been withdrawn', div.text): 
            withdrawn = True
            recs.remove(rec)
    if withdrawn: continue                      
    #req = urllib2.Request(rec['artlink'], headers=hdr)
    #artpage = BeautifulSoup(urllib2.urlopen(req))
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #abstract
            if meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #year 
            elif meta['name'] == 'citation_publication_date':
                rec['year'] = meta['content']
            #date
            elif meta['name'] == 'citation_online_date':
                rec['date'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    #for late online
    if 'date' in rec.keys() and 'year' in rec.keys():
        onlineyear = re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])
        if onlineyear > rec['year']:
            print '   change rec_date from "%s" to "%s"' % (rec['date'], rec['year'])
            rec['date'] = rec['year']
    #JSON
    for script in artpage.body.find_all('script'):
        if script.contents:
            #scriptt = re.sub('[\n\t]', '', script.text.strip())
            scriptt = re.sub('[\n\t]', '', script.contents[0].strip())
            scriptt = re.sub('.*window.jscholApp_initialPageData *= *(\{.*\}).*', r'\1', scriptt)
        else:
            scriptt = False
        if scriptt:
            scripttjson = json.loads(scriptt)
            #supervisors
            if 'advisors' in scripttjson.keys():
                if scripttjson['advisors']:
                    for adv in scripttjson['advisors']:
                        rec['supervisor'].append([ adv['name'] ])
            if 'attrs' in scripttjson.keys():
                #keywords
                if 'keywords' in scripttjson['attrs'].keys():
                    rec['keyw'] = scripttjson['attrs']['keywords']
                #subject
                if 'subjects' in scripttjson['attrs'].keys():
                    rec['subjects'] = scripttjson['attrs']['subjects']
                    rec['note'] += scripttjson['attrs']['subjects']
                #author
                if 'authors' in scripttjson['attrs'].keys():
                    for author in scripttjson['attrs']['authors']:
                        if 'email' in author.keys():
                            rec['autaff'] = [[ author['name'], 'EMAIL:%S' % (author['email']), publisher ]]
            #license
            if 'rights' in scripttjson.keys():
                if scripttjson['rights'] and re.search('creativecommons.org', scripttjson['rights']):
                    rec['license'] = {'url' : scripttjson['rights']}
            if 'citation' in scripttjson.keys():
                #DOI
                if 'doi' in scripttjson['citation'].keys() and scripttjson['citation']['doi']:
                    rec['doi'] = scripttjson['citation']['doi']
                else:
                    rec['doi'] = '20.2000/%s/%s' % (abbr.upper(), re.sub('.*\/', '', rec['artlink']))
                    rec['link'] = rec['artlink']
            #OA
            if 'oa_policy' in scripttjson.keys() and scripttjson['oa_policy']:
                rec['note'].append(scripttjson['oa_policy'])
                print '  ', scripttjson['oa_policy']
    #sort by subject
    if not 'subjects' in rec.keys():
        rec['subjects'] = ['NoSubject']
    for s in rec['subjects']:
        subject = re.sub('\W', '', s)
        if not subject in subjectstoskip:
            relevantrecs.append(rec)
            if subject in subjectrecs.keys():
                subjectrecs[subject].append(rec)
            else:
                subjectrecs[subject] = [rec]
            break
    print '   ', rec.keys()
    print '   ', ', '.join(['%s (%i)' % (s, len(subjectrecs[s])) for s in subjectrecs.keys()])
jnlfilename = 'THESES-%s-%s_%i' % (abbr.upper(), stampoftoday, numberofpages*articlesperpage)
##sorting no longer needed for regular updates
#for s in  subjectrecs.keys():
#    if not s in subjectstoskip:
#        jnlfilename = 'THESES-%s-%s_%i-%s' % (abbr.upper(), stampoftoday, numberofpages*articlesperpage, s)
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(relevantrecs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, 'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path, 'a')
    retfiles.write(line)
    retfiles.close()
