# -*- coding: utf-8 -*-
#harvest theses from oatd.org (Open Access Theses and Dissertations)
#FS: 2021-02-02

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
from bs4 import Comment
import re
import ejlmod2
import unicodedata
import codecs
import datetime
import time
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
#from selenium.webdriver.firefox.options import Options

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

singlewords = ["2HDM", "ABJM", "antibaryon", "antifermion", "antifield",
               "antigravitation", "antihydrogen", "antihyperon", "antineutrino",
               "antinucleon", "antiparticle", "antiquark", "ArgoNeuT", "ASACUSA",
               "axino", "axion", "BaBar", "Bagger-Lambert-Gustavsson", "Baksan",
               "Balitsky-Kovchegov", "baryon", "Becchi-Rouet-Stora", "BFKL",
               "Borexino", "Born-Infeld", "Brans-Dicke", "BTeV", "Callan-Gross",
               "CCFM", "CERN", "Chaplygin", "Chern-Simons", "Chou-Yang",
               "chromoelectric", "chromomagnetic", "CPT", "CRESST", "D-brane",
               "DEAP-3600", "DESY", "DGLAP", "dilaton", "dilepton", "diquark",
               "Dirac-Kaehler", "D-particle", "Drell-Hearn-Gerasimov", "Drell-Yan",
               "Duffin-Kemmer-Petiau", "Dvali-Gabadadze-Porrati", "dyon",
               "Dyson-Schwinger", "Eguchi-Kawai", "Einstein-Yang-Mills", 'Einstein-Yang-Mills-Higgs',
               "electroweak", "Ellis-Jaffe", "EPRL", "eRHIC", "Fermilab",
               "FINUDA", "Froissart", "Gauss-Bonnet", "Gell-Mann-Okubo", "GeV",
               "Georgi-Glashow", "Ginsparg-Wilson", "Glashow-Iliopoulos-Maiani",
               "glasma", "glueball", "GlueX", "gluino", "gluon", "Goldstino",
               "gravitino", "graviton", "Green-Schwarz", "Gross-Neveu", "GZK",
               "hadron", "hadroproduction", "HAPPEX", "HEP", "Higgs", "Higgsino",
               "Higgsless", "Horava-Lifshitz", "Horava-Witten", "hypercharge",
               "hypernucleus", "hyperon", "Hyperon", "hyperonic", "IAXO", "IceCube",
               "Iizuka-Okubo-Zweig", "inflaton", "Isgur-Wise", "JLEIC",
               "Jona-Lasinio-Nambu", "Kaluza-Klein", "KAMIOKANDE", "KamLAND",
               "Kazakov-Migdal", "Klebanov-Witten", "KM3NeT", "Kobayashi-Maskawa",
               "KTeV", "L3", "Landau-Pomeranchuk-Migdal", "leptogenesis", "lepton",
               "leptophilic", "leptophobic", "leptoproduction", "leptoquark", "LHCb",
               "LHeC", "LIGO", "Lippmann-Schwinger", "Majoron", "M-brane", "meson",
               "MicroBooNE", "MiniCLEAN", "MOEDAL", "MSSM", "M-theory", "Mu2e",
               "Mu3e", "muon", "muonium", "N2HDM", "NA48", "NA49", "NA60", "NA61",
               "NA62", "neutrino", "neutrinoless", "neutrinoproduction", "NLSP",
               "NMSSM", "odderon", "Pati-Salam", "Peccei-Quinn", "pentaquark",
               "pomeron", "positronium", "pQCD", "Proca", "QCD", "QFT", "quark",
               "quarkonium", "Randall-Sundrum", "Rarita-Schwinger", "Regge",
               "RHIC", "Salam-Weinberg", "SciBooNE", "S-duality", "Seiberg-Witten ", "semileptonic",
               "sfermion", "sine-Gordon", "sinh-Gordon", "Skyrmion", "SLAC", "slepton",
               "sneutrino", "squark", "Supergravity", "SuperKEKB", "superluminal",
               "superstring", "supersymmetry", "SUSY", "T2K", "tachyon", "T-duality",
               "technicolor", "tetraquark", "TeV", "Tevatron", "topcolor", "T-parity",
               "TPC", "TQFT", "Ward-Takahashi", "Wess-Zumino", "Wess-Zumino-Witten",
               "Wheeler-DeWitt", "Wick-Cutkosky", "WIMP", "Wino", "wormhole", "XENON1T",
               "Yang-Mills", "Yang-Mills-Higgs", "Zino"]
multwords = [['AdS', 'CFT'], ['quantum', 'field', 'theory'],
             ['PANDA', 'FAIR'], ['quantum', 'chromodynamics'],
             ['Quantum', 'Cosmology'], ['quantum', 'electrodynamics'],
             ['quantum', 'gravity'], ['string', 'theory'],
             ['wakefield', 'acceleration']]
dedicatedharvester = ['alberta', 'arizona-diss', 'asu', 'barcelona', 'baylor', 'bielefeld', 'brown', 'caltech', 'cambridge',
                      'colorado', 'columbia-diss', 'dortmund-diss', 'durham', 'freiburg-diss', 'glasgow',
                      'goettingen', 'harvard', 'heid-diss', 'houston', 'humboldt-diss', 'ksu',
                      'ku', 'liverpool', 'lmu-germany', 'lund', 'manchester', 'mcgill', 'melbourne',
                      'mississippi', 'montstate', 'narcis', 'neu', 'ohiolink', 'oregon', 'princeton', 
                      'qucosa-diss', 'regensburg-diss', 'rochester', 'rutgers', 'giessen-diss', 'tamu', 'toronto-diss',
                      'ttu', 'ubc', 'uky-diss', 'umich', 'valencia', 'vcu', 'vt', 'washington', 'wayne',
                      'whiterose', 'wm-mary', 'wurz-diss']
dedicatedaffiliations = ['Imperial College London', 'University of Edinburgh',
                         'University College London (University of London)',
                         "King's College London (University of London)", 'University of Manchester']
dedicatedsuboptimalharvester = ['eth', 'fsu', 'cornell', 'karlsruhe-diss', 'stanford', 'texas', 'thueringen', 'thueringen-diss']
nodedicatedharvester = ['aberdeen', 'alabama', 'ankara', 'arkansas', 'bremen', 'brazil', 'bu', 'cardiff',  'clemson', 'colo-mines','colostate',
                        'darmstadt', 'darmstadt2', 'delaware', 'duquesne', 'ethos', 'fiu', 'florida', 'gatech', 'georgia-state', 
                        'groningen', 'guelph', 'hokkaido', 'iowa', 'jairo', 'jamescook', 'lehigh', 'liberty', 'lsu-diss', 'macquarie-phd',
                        'maynooth', 'montana', 'msstate', 'mtu', 'ncsu', 'odu', 'oviedo', 'potsdam-diss', 'regina', 'rice', 'rit', 'siu-diss',
                        'south-carolina', 'star-france', 'stellenbosch', 'st-andrews', 'syracuse-diss', 'temple', 'uconn',
                        'udel', 'uiuc', 'ulm-diss', 'unm', 'unsw', 'utk-diss', 'urecht', 'uwm', 'vandy', 'virginia', 'vrije',
                        'wustl', 'wvu', 'york']
dontcheckforpdf = ['ethos']

wordsperquery = 10
searches = []
for j in range((len(singlewords)-1)/wordsperquery + 1):
    words = singlewords[j*wordsperquery:(j+1)*wordsperquery]
    if len(words) > 1:
        searches.append('("' + '" OR "'.join(words) + '")')
    else:
        searches.append('"' + words[0]+ '"')
for words in multwords:
    searches.append('(' + ' AND '.join(words) + ')')
startyear = str(now.year-1)
stopyear = str(now.year+1)
startsearch = int(sys.argv[1])
stopsearch = int(sys.argv[2])
rpp = 30
chunksize = 50
publisher = 'oatd.org'
comment = Comment('Kommentar')

#check already harvested
ejldirs = ['/afs/desy.de/user/l/library/dok/ejl/onhold',
           '/afs/desy.de/user/l/library/dok/ejl',
           '/afs/desy.de/user/l/library/dok/ejl/zu_punkten',
           '/afs/desy.de/user/l/library/dok/ejl/zu_punkten/enriched',
           '/afs/desy.de/user/l/library/dok/ejl/backup',
           '/afs/desy.de/user/l/library/dok/ejl/backup/%i' % (now.year-1)]
redoki = re.compile('THESES.OATD')
renodoi = re.compile('^I\-\-NODOI:(.*)\-\-$')
bereitsin = []
for ejldir in ejldirs:
    print ejldir
    for datei in os.listdir(ejldir):
        if redoki.search(datei):
            inf = open(os.path.join(ejldir, datei), 'r')
            for line in inf.readlines():
                if len(line) > 1 and line[0] == 'I':
                    if renodoi.search(line):
                        nodoi = renodoi.sub(r'\1', line.strip())
                        if not nodoi in bereitsin:
                            bereitsin.append(nodoi)
            #print '  %6i %s' % (len(bereitsin), datei)
print '   %i theses already in backup or pipeline' % (len(bereitsin))

i = 0
recs = []
prerecs = []
dois = []
date = 'pub_dt:[' + startyear + '-01-01T00:00:00Z TO ' + stopyear + '-01-01T00:00:00Z]'

driver = webdriver.PhantomJS()
#opts = Options()
#opts.add_argument("--headless")
#caps = webdriver.DesiredCapabilities().FIREFOX
#caps["marionette"] = True
#driver  = webdriver.Firefox(options=opts, capabilities=caps)
 
driver.implicitly_wait(60)
driver.set_page_load_timeout(30)
for search in searches[startsearch:stopsearch]:
    i += 1
    page = 0
    tocurl = 'https://oatd.org/oatd/search?q=' + search + ' AND ' + date + '&level.facet=doctoral&sort=author&start=' + str(page*rpp+1)
    print '==={ %i/%i }==={ %s }==={ %s }===' % (i, stopsearch-startsearch, search, tocurl)
    try:
        driver.get(tocurl)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'citeFormatName')))
        tocpages = [BeautifulSoup(driver.page_source, features="lxml")]
    except:
        print '   \ wait 2 minutes /'
        time.sleep(120)
        driver.get(tocurl)
        #WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'citeFormatName')))
        tocpages = [BeautifulSoup(driver.page_source, features="lxml")]
    numofpages = 1
    for link in tocpages[0].find_all('link', attrs = {'rel' : 'last'}):
        time.sleep(25)
        numoftheses = int(re.sub('.*=', '', link['href']))
        numofpages = (numoftheses - 1)/rpp + 1
        for j in range(numofpages-1):
            page = j + 1
            tocurl = 'https://oatd.org/oatd/search?q=(' + search + ') AND ' + date + '&level.facet=doctoral&start=' + str(page*rpp+1)
            print ' =={ %i/%i | %i/%i }==={ %s }===' % (i, stopsearch-startsearch, page+1, numofpages, tocurl)
            try:
                time.sleep(10)
                driver.get(tocurl)
                WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'citeFormatName')))
                tocpages.append(BeautifulSoup(driver.page_source, features="lxml"))
            except:
                print '   \ wait 10s /'
                time.sleep(10)
                driver.get(tocurl)
                #WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'citeFormatName')))
                tocpages.append(BeautifulSoup(driver.page_source, features="lxml"))
    page = 0
    for tocpage in tocpages:
        page += 1
        print '  ={ %i/%i | %i/%i }===' % (i, stopsearch-startsearch, page, numofpages)
        for desce in tocpage.descendants:
            if type(desce) == type(comment) and re.search('Repository', desce.string):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [search]}
                repo = re.sub('Repository: (.*?) \|.*', r'\1', desce.string).strip()
                rec['repo'] = repo
                tid = re.sub('.*\| ID: (.*?) \|.*', r'\1', desce.string)
                tid = re.sub(':', '\:', tid)
                tid = re.sub('/', '\%2F', tid)
                rec['artlink'] = 'https://oatd.org/oatd/record?record=' + tid
                rec['nodoi'] = '20.2000/OATD/' + re.sub('\W', '', re.sub('.*record=', '', tid))
                if repo in dedicatedharvester:
                    print '   skip', repo
                else:
                    if repo in nodedicatedharvester:
                        rec['note'].append('(REPO:' + repo + ')')
                    elif repo in dedicatedsuboptimalharvester:
                        rec['note'].append('REPO:' + repo + '!')
                    else:
                        rec['note'].append('REPO:' + repo)
                    if rec['nodoi'] in bereitsin:
                        print '    ((', rec['nodoi'],'))'
                    elif not rec['nodoi'] in dois:
                        print '      ', rec['nodoi']
                        rec['note'].append('NODOI:'+rec['nodoi'])
                        prerecs.append(rec)
                        dois.append(rec['nodoi'])
                    else:
                        print '     (', rec['nodoi'],')'
        print '    %i records so far' % (len(prerecs))
    if not prerecs:
        print '[]',tocpage.text

i = 0
rehdl = re.compile('.*hdl.handle.net\/')
repothdl = re.compile('.*\/handle\/(\d+\/.*)')
reurn = re.compile('.*resolve.urn=')
redoi = re.compile('.*doi.org\/(10.*)')
reinfodoi = re.compile('^info:doi\/(10.*)')
recc = re.compile('.*(http.*?creativecommons.org.*?)[ ,\.;$].*')
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s : %s }------' % (i, len(prerecs), len(recs), rec['repo'], rec['artlink'])
    try:
        time.sleep(10)
        driver.get(rec['artlink'])
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'leftCol')))
        artpage = BeautifulSoup(driver.page_source, features="lxml")
    except:
        try:
            print '\\\| wait 15s |///'
            time.sleep(15)
            driver.get(rec['artlink'])
            artpage = BeautifulSoup(driver.page_source, features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    aff = False
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_author':
                if meta['content']:
                    rec['autaff'] = [[ meta['content'] ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #institution
            elif meta['name'] == 'citation_dissertation_institution':
                aff = meta['content']
                if aff in dedicatedaffiliations:
                    keepit = False
                    print '   skip "%s"' % (aff)
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
            #date
            elif meta['name'] == 'dc.date':
                rec['date'] = meta['content']
            #PIDs
            elif meta['name'] == 'dc.identifier':
                for mc in re.split(' *; *', meta['content']):
                    if rehdl.search(mc):
                        rec['hdl'] = rehdl.sub('', mc)
                    elif reurn.search(mc):
                        rec['urn'] = reurn.sub('', mc)
                    elif redoi.search(mc):
                        rec['doi'] = redoi.sub(r'\1', mc)
                    elif repothdl.search(mc):
                        hdl = repothdl.sub(r'\1', mc)
                        if not re.search('123456789\/', hdl):
                            #verify
                            try:
                                driver.get('http://hdl.handle.net/' + hdl)
                                hdlpage = BeautifulSoup(driver.page_source, features="lxml")
                                for title in hdlpage.find_all('title'):
                                    if title.text.strip() == 'Not Found':
                                        rec['note'].append('%s seems not to be a proper HDL' % (hdl))
                                        rec['link'] = mc
                                    else:
                                        rec['hdl'] = hdl
                                        rec['note'].append('%s seems to be a proper HDL' % (hdl))
                            except:
                                print 'could not check handle %s' % (hdl)
                                rec['link'] = mc
                    else:
                        rec['link'] = mc
            #abstract
            elif meta['name'] == 'dc.description':
                rec['abs'] = meta['content']
    if aff: rec['autaff'][0].append(aff)
    for table in artpage.body.find_all('table', attrs = {'class' : 'recordTable'}):
        for tr in table.find_all('tr'):
            for td in tr.find_all('td', attrs = {'class' : 'leftCol'}):
                tdt = td.text.strip()
                td.decompose()
            for td in tr.find_all('td'):
                #keyword
                if tdt == 'Subjects/Keywords':
                    rec['keyw'] = re.split('; ', td.text.strip())
                #language
                elif tdt == 'Language':
                    lang = td.text.strip()
                    if lang != 'en':
                        if lang == 'fr':
                            rec['language'] = 'French'
                        elif lang == 'se':
                            rec['language'] = 'Swedish'
                        elif lang == 'it':
                            rec['language'] = 'Italian'
                        elif lang == 'tr':
                            rec['language'] = 'Turkish'
                        elif lang == 'es':
                            rec['language'] = 'Spanish'
                        elif lang == 'pt':
                            rec['language'] = 'Portuguese'
                        elif lang == 'de':
                            rec['language'] = 'German'
                        elif lang == 'pl':
                            rec['language'] = 'Polish'
                        elif re.search('ingl.s', lang):
                            pass
                        else:
                            print '!unknown language', lang
                            rec['language'] = lang
                #other identifiers
                elif tdt == 'Other Identifiers':
                    if reinfodoi.search(td.text) and not 'doi' in rec.keys():
                        rec['doi'] = reinfodoi.sub(r'\1', td.text.strip())
                #license
                elif tdt == 'Rights':
                    if recc.search(td.text):
                        rec['license'] = {'url' : recc.sub(r'\1', td.text.strip())}
    if keepit or i == len(prerecs):
        #try to get pdf
        serverlink = False
        if 'link' in rec.keys() and re.search('pdf$', rec['link']):
            rec['FFT'] = rec['link']
        elif 'hdl' in rec.keys():
            serverlink = 'http://hdl.handle.net/' + rec['hdl']
        elif 'doi' in rec.keys():
            serverlink = 'http://dx.doi.org/' + rec['doi']
        elif 'link' in rec.keys():
            serverlink = rec['link']
        if serverlink and not rec['repo'] in dontcheckforpdf:
            rec['note'].append('REPOLINK:'+serverlink)
            print '    ... check for PDF at %s' % (serverlink)
            try:
                driver.get(serverlink)
                serverpage = BeautifulSoup(driver.page_source, features="lxml")
                for meta in serverpage.find_all('meta', attrs = {'name' : ['citation_pdf_url', 'bepress_citation_pdf_url', 'eprints.document_url']}):
                    if not 'FFT' in rec.keys():
                        if meta['content']:
                            rec['FFT'] = meta['content']
                            print '          ', meta['content']
                if not 'doi' in rec.keys():
                    print '    ... check for DOI at %s' % (serverlink)
                    for meta in serverpage.find_all('meta', attrs = {'name' : ['citation_doi', 'bepress_citation_doi', 'eprints.doi', 'eprints.doi_name', 'DC.Identifier.doi']}):
                        rec['doi'] = meta['content']
                        rec['note'].append('DOI from reposerver')
                        print '          ', meta['content']
                    if not 'doi' in rec.keys():
                        for meta in serverpage.find_all('meta', attrs = {'name' : 'DC.identifier'}):
                            if re.search('doi.org', meta['content']):
                                rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
                                print '          ', rec['doi']
                                rec['note'].append('DOI from reposerver')
                            elif re.search('handle.net', meta['content']) and not 'hdl' in rec.keys():
                                rec['hdl'] = re.sub('.*handle.net\/', '', meta['content'])
                                print '          ', rec['hdl']
                                rec['note'].append('HDL from reposerver')
            except:
                print '           failed'
        #pseudoDOI?
        if not 'doi' in rec.keys() and not 'hdl' in rec.keys():
            if not 'link' in rec.keys():
                rec['link'] = rec['artlink']
            if not 'urn' in rec.keys():
                rec['doi'] = rec['nodoi']
        if 'autaff' in rec.keys():
            recs.append(rec)
            print '  ', rec.keys()
        else:
            print '!', rec
            time.sleep(20)
        if ((i % chunksize) == 0) or (i == len(prerecs)):
            print i, len(prerecs), len(recs)
            if recs:
                chunknumber = (i-1)/chunksize + 1
                numofchunks = (len(prerecs) - 1) / chunksize + 1
                jnlfilename = 'THESES-OATD_%s_%s-%s_%i-%i-%i_%i_%02i-%i' % (stampoftoday, startyear, stopyear, startsearch, stopsearch, len(searches), chunksize, chunknumber, numofchunks)
                crecs = recs[(chunknumber-1)*chunksize:chunknumber*chunksize]
                #closing of files and printing
                xmlf = os.path.join(xmldir, jnlfilename+'.xml')
                xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
                ejlmod2.writeXML(crecs, xmlfile, publisher)
                xmlfile.close()
                #retrival
                retfiles_text = open(retfiles_path,"r").read()
                line = jnlfilename+'.xml'+ "\n"
                if not line in retfiles_text:
                    retfiles = open(retfiles_path, "a")
                    retfiles.write(line)
                    retfiles.close()

