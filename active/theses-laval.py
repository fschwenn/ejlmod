# -*- coding: utf-8 -*-
#harvest theses from Laval U.
#FS: 2022-05-23

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Laval U.'
jnlfilename = 'THESES-LAVAL-%s' % (stampoftoday)

rpp = 50
pages = 8
hdr = {'User-Agent' : 'Magic Browser'}

boring = [u'Faculté de médecine.', u'Faculté des lettres et des sciences humaines.',
          u"Faculté des sciences de l'administration.",
          u"Faculté des sciences de l'agriculture et de l'alimentation.",
          u'Faculté des sciences sociales.', u'Faculté de musique.',
          u"Faculté de droit.", u"Faculté de foresterie, de géographie et de géomatique.",
          u"Faculté des sciences de l'éducation.", 'Faculté de pharmacie.',
          u"Faculté de théologie et de sciences religieuses.",
          u'Faculté des lettres et des sciences humaines',
          u'Faculté de pharmacie.',
          u"Faculté des sciences infirmières."]
boring += ['Doctorat en microbiologie-immunologie', 'Doctorat en histoire', 'Doctorat en chimie',
           "Doctorat en actuariat", u'Doctorat en génie chimique', 
           u'Doctorat en microbiologie agroalimentaire', 
           u"Doctorat en sciences de l'administration - management",
           u'Doctorat en service social', u'Doctorat interuniversitaire en océanographie',
           u"Doctorat en biologie", u'Doctorat en génie civil',
           u"Doctorat en droit", u'Doctorat en biochimie',
           u"Doctorat en nutrition", 'Doctorat en architecture',
           u"Doctorat en philosophie", 'Doctorat en microbiologie',
           u"Doctorat en psychopédagogie", 'Doctorat en théologie',
           u"Doctorat en santé communautaire", 'Doctorat en biophotonique',
           u"Doctorat en sciences des aliments - microbiologie alimentaire",
           u"Doctorat en sciences forestières",
           u"Doctorat en technologie éducative",
           u"Doctorat sur mesure"]
boring += [u'Thèse. Médecine', u"Thèse. Administration et politiques de l'éducation",
           u"Thèse. Agriculture", u"Thèse. Agroéconomie",
           u"Thèse. Aménagement du territoire et développement régional",
           u"Thèse. Anthropologie", u"Thèse. Biochimie", u"Thèse. Biologie cellulaire et moléculaire",
           u"Thèse. Biologie", u"Thèse. Biologie végétale", u"Thèse. Chimie",
           u"Thèse. Communication publique", u"Thèse. Comptabilité", u"Thèse. Didactique",
           u"Thèse. Droit", u"Thèse. Économique", u"Thèse. Ethnologie", u"Thèse. Génie chimique",
           u"Thèse. Génie civil", u"Thèse. Génie des mines, de la métallurgie et des matériaux",
           u"Thèse. Génie électrique et génie informatique", u"Thèse. Génie électrique",
           u"Thèse. Génie mécanique", u"Thèse. Géographie", u"Thèse. Géologie et minéralogie",
           u"Thèse. Histoire", u"Thèse. Linguistique", u"Thèse. Littérature canadienne-française",
           u"Thèse. Littérature espagnole", u"Thèse. Littérature et arts de la scène et de l'écran",
           u"Thèse. Littérature française", u"Thèse. Littérature francophone", u"Thèse. Management",
           u"Thèse. Médecine expérimentale", u"Thèse. Microbiologie-immunologie", u"Thèse. Musique",
           u"Thèse. Nutrition", u"Thèse. Pharmacie", u"Thèse. Philosophie", u"Thèse. Psychologie",
           u"Thèse. Psychopédagogie - Adaptation scolaire", u"Thèse. Psychopédagogie",
           u"Thèse. Relations industrielles", u"Thèse. Relations internationales",
           u"Thèse. Santé communautaire", u"Thèse. Science politique", u"Thèse. Sciences animales",
           u"Thèse. Sciences cliniques et biomédicales", u"Thèse. Sciences de l'administration",
           u"Thèse. Sciences de l'éducation", u"Thèse. Sciences de l'orientation",
           u"Thèse. Sciences des religions", u"Thèse. Sciences du bois",
           u"Thèse. Sciences et technologie des aliments", u"Thèse. Sciences forestières",
           u"Thèse. Sciences infirmières", u"Thèse. Service social", u"Thèse. Sociologie",
           u"Thèse. Archéologie", u"Thèse. Lettres", u"Thèse. Architecture et urbanisme",
           u"Thèse. Littérature ancienne", u"Mémoire. Génie des mines, de la métallurgie et des matériaux",
           u"Thèse. Actuariat", u"Thèse. Arts visuels", u"Thèse. Éducation physique",
           u"Thèse. Histoire de l'art", u"Thèse. Littérature anglaise", u"Thèse. Sciences de l'éducation.",
           u"Thèse. Sols et environnement", u"Thèse. Technologie éducative", u"Thèse. Théologie"]


inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
recs = []
for page in range(pages):
        tocurl = 'https://corpus.ulaval.ca/jspui/handle/20.500.11794/17461/simple-search?query=&filter_field_1=documentType&filter_type_1=equals&filter_value_1=COAR1_1%3A%3ATexte%3A%3ATh%C3%A8se%3A%3ATh%C3%A8se+de+doctorat&sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&etal=0&start=' + str(rpp*(page+8))
        print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)        
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for td in tocpage.find_all('td', attrs = {'headers' : 't2'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
            for a in td.find_all('a'):
                    if a.has_attr('href') and re.search('handle\/', a['href']):
                        rec['link'] = 'https://corpus.ulaval.ca' + a['href']  + '?mode=full&locale=en'
                        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                        if not rec['hdl'] in uninterestingDOIS:
                            prerecs.append(rec)
        time.sleep(6)

i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
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
    (author, altauthor, frtitle, entitle) = (False, False, False, False)
    keepit = True
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #title
            elif meta['name'] == 'DC.title':
                if meta.has_attr('xml:lang'):
                    if  meta['xml:lang'] in ['eng', 'en']:
                        entitle = meta['content']
                    else:
                        frtitle =  meta['content']
                else:
                    rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'] += re.split(',', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = re.sub('\/jspui', '', meta['content'])
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('^10\.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta.has_attr('xml:lang') and meta['xml:lang'] in ['eng', 'en']:
                    rec['abs'] = meta['content']
            #pages
            elif meta['name'] == 'DC.relation':
                rec['pages'] = meta['content']
    #author
    if altauthor:
        author += ', CHINESENAME: %s' % (altauthor)
    rec['auts'] = [ author ]
    #more metadata
    for table in artpage.body.find_all('table', attrs = {'class' : 'itemDisplayTable'}):
        for tr in table.find_all('tr'):
            for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
                label = td.text.strip()
            for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue', 'headers' : 's2'}):
                #references
                if label == 'dc.identifier.citation':
                    for br in td.find_all('br'):
                        br.replace_with('BRBRBR')
                    for ref in re.split('BRBRBR', td.text.strip()):
                        rec['refs'].append([('x', ref)])
                #supervisor
                if label == 'dc.contributor.advisor':
                    if td.text.strip():
                        rec['supervisor'].append([re.sub('.*\((.*)\)', r'\1', td.text.strip())])
                #language
                if label == 'dc.language':
                    if td.text.strip():
                        if td.text.strip() in ['fre', 'fr']:
                            rec['language'] = 'French'
                        elif td.text.strip() in ['spa']:
                            rec['language'] = 'Spanish'
                        elif not td.text.strip() in ['eng', 'en']:
                            rec['note'].append('LANGUAGE=%s' % (td.text.strip()))
                #degree
                elif label == 'etdms.degree.discipline':
                    degree = td.text.strip()
                    if degree in boring:
                        keepit = False
                    elif degree:
                        rec['note'].append('DEGREE_D: %s' % (degree))
                #degree
                elif label == 'etdms.degree.name':
                    degree = td.text.strip()
                    if degree in boring:
                        keepit = False
                    elif degree:
                        rec['note'].append('DEGREE_N: %s' % (degree))
                #department
                elif label == 'bul.faculte':
                    department = td.text.strip()
                    if department in boring:
                        keepit = False
                    else:
                        rec['note'].append('DEPARTMENT=%s' % (department))
    if not 'tit' in rec.keys():
        if 'language' in rec.keys():
            if frtitle:
                rec['tit'] = frtitle
                if entitle:
                    rec['transtit'] = entitle
            elif entitle:
                rec['tit'] = entitle
        elif entitle:
            rec['tit'] = entitle
            if frtitle:
                rec['otits'] = [ frtitle ]
        elif frtitle:
            rec['tit'] = frtitle
    if keepit:
        recs.append(rec)
        print '  ', ', '.join(['%s(%i)' % (k, len(rec[k])) for k in rec.keys()])
    else:
        newuninterestingDOIS.append(rec['hdl'])

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
