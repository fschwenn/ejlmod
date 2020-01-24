# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from Karlsruhe Insitute of Technolgy
# FS 2020-01-13

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import datetime
import time 

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'KIT, Karlsruhe'

typecode = 'T'

jnlfilename = 'THESES-KIT-%s' % (stampoftoday)
pages = 2
years = 2

tocurl = 'https://primo.bibliothek.kit.edu/primo_library/libweb/action/search.do?ct=facet&rfnGrpCounter=5&rfnGrpCounter=4&fn=search&indx=1&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=2&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&rfnExcGrp=3&mulIncFctN=facet_local12&mulIncFctN=facet_local12&mulIncFctN=facet_local12&dscnt=0&rfnIncGrp=3&rfnIncGrp=3&rfnIncGrp=3&vid=KIT&fctV=%5B2009+TO+null%5D&fctV=istDissertation&mode=Basic&ct=facet&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&mulExcFctN=facet_local12&fctExcV=Institut+f%C3%BCr+Unternehmungsf%C3%BChrung+%28IBU%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Computational+Materials+Science+%28IAM-CMS%29&fctExcV=Institut+f%C3%BCr+Informationswirtschaft+und+Marketing+%28IISM%29&fctExcV=Institut+f%C3%BCr+Meteorologie+und+Klimaforschung+-+Forschungsbereich+Troposph%C3%A4re+%28IMK-TRO%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Werkstoffkunde+%28IAM-WK%29&fctExcV=Institut+f%C3%BCr+Angewandte+Biowissenschaften+%28IAB%29&fctExcV=Institut+f%C3%BCr+Fahrzeugsystemtechnik+%28FAST%29&fctExcV=Institut+f%C3%BCr+Bio-+und+Lebensmitteltechnik+%28BLT%29&fctExcV=Institut+f%C3%BCr+Anthropomatik+und+Robotik+%28IAR%29&fctExcV=Institut+f%C3%BCr+Produktionstechnik+%28WBK%29&fctExcV=Institut+f%C3%BCr+Technische+Chemie+und+Polymerchemie+%28ITCP%29&fctExcV=Institut+f%C3%BCr+Physikalische+Chemie+%28IPC%29&fctExcV=Institut+f%C3%BCr+Industriebetriebslehre+und+Industrielle+Produktion+%28IIP%29&fctExcV=Institut+f%C3%BCr+Mikrostrukturtechnik+%28IMT%29&fctExcV=Lichttechnisches+Institut+%28LTI%29&fctExcV=Institut+f%C3%BCr+Angewandte+Informatik+und+Formale+Beschreibungsverfahren+%28AIFB%29&fctExcV=Institut+f%C3%BCr+Anorganische+Chemie+%28AOC%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Informatik+%28INFORMATIK%29&fctExcV=Institut+f%C3%BCr+Organische+Chemie+%28IOC%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Maschinenbau+%28MACH%29&fctExcV=Institut+f%C3%BCr+Volkswirtschaftslehre+%28ECON%29&fctExcV=Institut+f%C3%BCr+Technische+Informatik+%28ITEC%29&fctExcV=Institut+f%C3%BCr+Angewandte+Geowissenschaften+%28AGW%29&fctExcV=Institut+f%C3%BCr+Theoretische+Informatik+%28ITI%29&fctExcV=Institut+f%C3%BCr+Funktionelle+Grenzfl%C3%A4chen+%28IFG%29&fctExcV=Institut+f%C3%BCr+Sport+und+Sportwissenschaft+%28IfSS%29&fctExcV=Institut+f%C3%BCr+Angewandte+Materialien+-+Werkstoff-+und+Biomechanik+%28IAM-WBM%29&fctExcV=Institut+f%C3%BCr+Produktentwicklung+%28IPEK%29&fctExcV=Institut+f%C3%BCr+Technische+Mechanik+%28ITM%29&fctExcV=Botanisches+Institut+und+Botanischer+Garten+%28BOTANIK%29&fctExcV=Institut+f%C3%BCr+Nanotechnologie+%28INT%29&fctExcV=Institut+f%C3%BCr+Programmstrukturen+und+Datenorganisation+%28IPD%29&fctExcV=Institut+f%C3%BCr+Toxikologie+und+Genetik+%28ITG%29&fctExcV=Institut+f%C3%BCr+Mechanische+Verfahrenstechnik+und+Mechanik+%28MVM%29&fctExcV=Institut+f%C3%BCr+Technik+der+Informationsverarbeitung+%28ITIV%29&fctExcV=Fakult%C3%A4t+f%C3%BCr+Bauingenieur-%2C+Geo-+und+Umweltwissenschaften+%28BGU%29&fctExcV=Engler-Bunte-Institut+%28EBI%29&rfnGrp=4&rfnGrp=1&tab=kit_evastar&srt=date&fctN=facet_searchcreationdate&fctN=facet_local8&vl(freeText0)=istKITopen&dstmp=1578919455926&fctIncV=Institut+f%C3%BCr+Angewandte+Physik+%28APH%29&fctIncV=Physikalisches+Institut+%28PHI%29&fctIncV=Institut+f%C3%BCr+Experimentelle+Kernphysik+%28IEKP%29&fctExcV=Steinbuch%20Centre%20for%20Computing%20(SCC)&mulExcFctN=facet_local12&rfnExcGrp=5&fctExcV=Institut%20f%C3%BCr%20Angewandte%20Materialien%20-%20Keramik%20im%20Maschinenbau%20(IAM-KM)&mulExcFctN=facet_local12&rfnExcGrp=5&fctExcV=Karlsruhe%20School%20of%20Optics%20%26%20Photonics%20(KSOP)&mulExcFctN=facet_local12&rfnExcGrp=5'

recs = []
for i in range(pages):
    print '---{ %i }---' % (i)
    newrecs = []
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    for div in tocpage.body.find_all('div', attrs ={'class' : 'EXLSummaryContainer'}):
        for h3 in div.find_all('h3', attrs ={'class' : 'EXLResultFourthLine'}):
            rec = {'jnl' : 'BOOK', 'tc' : 'T'}
            rec['year'] = h3.text.strip()
            rec['date'] = h3.text.strip()
            for h2 in div.find_all('h2'):
                for a in h2.find_all('a'):
                    rec['artlink'] = 'https://primo.bibliothek.kit.edu/primo_library/libweb/action/' + a['href']
                    rec['tit'] = a.text.strip()
            try:
                if int(rec['year']) >= now.year - years:
                    newrecs.append(rec)
            except:
                newrecs.append(rec)
                print '   ', rec['year'], '?'
    print '   %i+%i=%i recs' % (len(recs), len(newrecs), len(recs)+len(newrecs))
    recs += newrecs                            
    if newrecs:
        for a in tocpage.body.find_all('a', attrs ={'class' : 'EXLBriefResultsPaginationLinkNext'}):
            tocurl = a['href']
    else:
        break
    
        

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---' % (i, len(recs))
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for div in artpage.body.find_all('div', attrs = {'class' : 'EXLDetailsContent'}):
        for li in div.find_all('li'):
            if li.has_attr('id'):
                #author
                if li['id'] == 'Verfasser-1':
                    for a in li.find_all('a'):
                        rec['autaff'] = [[ a.text.strip(), publisher ]]
                #pages
                if li['id'] == 'Auflage / Umfang-1':
                    for span in li.find_all('span'):
                        pages = span.text.strip()
                        if re.search('\d', pages):
                            rec['pages'] = re.sub('\D*(\d+).*', r'\1', pages)
                #language
                if li['id'] == 'Sprache-1':
                    for span in li.find_all('span'):
                        language = span.text.strip()
                        if language != 'Englisch':
                            if language == 'Deutsch':
                                rec['language'] = 'german'
                            else:
                                rec['language'] = language
                #DOI, ISBN
                if li['id'] == 'Identifikator-1':
                    for span in li.find_all('span'):
                        spant = span.text.strip()
                        if re.search('10\.5445\/', spant):
                            rec['doi'] = re.sub('.*(10\.5445\/.*)', r'\1', spant)
                        elif re.search('^978\-', spant):
                            rec['isbn'] = re.sub('\-', '', spant)
    #FFT
    for a in artpage.body.find_all('a'):
        if a.has_attr('href'):
            if a.text.strip() == 'Online Ressource':
                rec['FFT'] = a['href']
    #DOI-landingpage
    if 'doi' in rec.keys():
        doilink = re.sub('.*\/', 'https://publikationen.bibliothek.kit.edu/', rec['doi'])
        try:
            doipage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(doilink))
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            doipage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(doilink))        
        #abstract
        for meta in doipage.head.find_all('meta', attrs = {'name' : 'citation_abstract'}):
            rec['abs'] = meta['content']
        for table in doipage.body.find_all('table', attrs = {'class' : 'table'}):
            for tr in table.find_all('tr'):
                tds = tr.find_all('td')
                if len(tds) == 2:
                    #Keywords
                    if tds[0].text.strip() == 'Schlagworte':
                        rec['keyw'] = re.split(', ', tds[1].text.strip())
    else:
        rec['doi'] = '20.2000/KIT/%s/%04i' % (stampoftoday, i)
    print rec.keys()

    
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
 
            
    
