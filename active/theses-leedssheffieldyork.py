# -*- coding: utf-8 -*-
#harvest theses from Universities of Leeds, Sheffield, and York
#FS: 2020-03-25


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'whiterose.ac.uk'

typecode = 'T'
pages = 5

jnlfilename = 'THESES-LeedsSheffieldYork-%s' % (stampoftoday)

boringaffs = ['University of Leeds, Department of Colour and Polymer Chemistry (Leeds), United Kindgom',
              'University of Leeds, Faculty of Biological Sciences (Leeds), School of Chemistry (Leeds), United Kindgom',
              'University of Leeds, Faculty of Biological Sciences (Leeds), School of Physics and Astronomy (Leeds), Institute for Molecular and Cellular Biology (Leeds), United Kindgom',
              'University of Leeds, Faculty of Biological Sciences (Leeds), School of Physics and Astronomy (Leeds), United Kindgom',
              'University of Leeds, Faculty of Environment (Leeds), Faculty of Maths and Physical Sciences (Leeds), School of Earth and Environment (Leeds), Institute for Atmospheric Science (Leeds), School of Physics and Astronomy (Leeds), United Kindgom',
              'University of Leeds, Faculty of Environment (Leeds), Food Science (Leeds), United Kindgom',
              'University of Leeds, Faculty of Maths and Physical Sciences (Leeds), Astbury Centre for Structural Molecular Biology (Leeds), United Kindgom',
              'University of Leeds, Faculty of Maths and Physical Sciences (Leeds), Food Science (Leeds), United Kindgom',
              'University of Leeds, Faculty of Maths and Physical Sciences (Leeds), School of Chemistry (Leeds), Astbury Centre for Structural Molecular Biology (Leeds), United Kindgom',
              'University of Leeds, Faculty of Maths and Physical Sciences (Leeds), School of Chemistry (Leeds), Department of Colour and Polymer Chemistry (Leeds), United Kindgom',
              'University of Leeds, Faculty of Maths and Physical Sciences (Leeds), School of Chemistry (Leeds), United Kindgom',
              'University of Leeds, Food Science (Leeds), School of Geography (Leeds), School of Medicine (Leeds), United Kindgom',
              'University of Leeds, Food Science (Leeds), School of Medicine (Leeds), United Kindgom',
              'University of Leeds, Food Science (Leeds), United Kindgom',
              'University of Leeds, Imaging Science (Leeds), Statistics (Leeds), United Kindgom',
              'University of Leeds, Institute for Atmospheric Science (Leeds), Applied Mathematics (Leeds), United Kindgom',
              'University of Leeds, Oral Biology (Leeds), School of Electronic & Electrical Engineering (Leeds), School of Physics and Astronomy (Leeds), United Kindgom',
              'University of Leeds, School of Chemistry (Leeds), Astbury Centre for Structural Molecular Biology (Leeds), United Kindgom',
              'University of Leeds, School of Chemistry (Leeds), Centre for Technical Textiles (Leeds), United Kindgom',
              'University of Leeds, School of Chemistry (Leeds), Institute for Molecular and Cellular Biology (Leeds), United Kindgom',
              'University of Leeds, School of Chemistry (Leeds), School of Chemical and Process Engineering (Leeds), United Kindgom',
              'University of Leeds, School of Chemistry (Leeds), School of Earth and Environment (Leeds), United Kindgom',
              'University of Leeds, School of Chemistry (Leeds), School of Mechanical Engineering (Leeds), United Kindgom',
              'University of Leeds, School of Computing (Leeds), School of Chemistry (Leeds), United Kindgom',
              'University of Leeds, School of Earth and Environment (Leeds), Food Science (Leeds), School of Medicine (Leeds), United Kindgom',
              'University of Leeds, School of Education (Leeds), School of Physics and Astronomy (Leeds), United Kindgom',
              'University of Leeds, School of Electronic & Electrical Engineering (Leeds), School of Physics and Astronomy (Leeds), United Kindgom',
              'University of Leeds, School of Mathematics (Leeds), School of Chemical and Process Engineering (Leeds), United Kindgom',
              'University of Leeds, School of Mathematics (Leeds), School of Mechanical Engineering (Leeds), United Kindgom',
              'University of Leeds, School of Physics and Astronomy (Leeds), Institute for Materials Research (Leeds), United Kindgom',
              'University of Leeds, School of Physics and Astronomy (Leeds), School of Chemical and Process Engineering (Leeds), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), Chemical and Biological Engineering (Sheffield), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), Faculty of Science (Sheffield), School of Mathematics and Statistics (Sheffield), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), Faculty of Science (Sheffield), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), Geography (Sheffield), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), Materials Science and Engineering (Sheffield), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), Molecular Biology and Biotechnology (Sheffield), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), Physics and Astronomy (Sheffield), United Kindgom',
              'University of Sheffield, Animal and Plant Sciences (Sheffield), United Kindgom',
              'University of Sheffield, Archaeology (Sheffield), Faculty of Arts and Humanities (Sheffield), United Kindgom',
              'University of Sheffield, Archaeology (Sheffield), United Kindgom',
              'University of Sheffield, Automatic Control and Systems Engineering (Sheffield), Psychology (Sheffield), United Kindgom',
              'University of Sheffield, Biomedical Science (Sheffield), Chemistry (Sheffield), United Kindgom',
              'University of Sheffield, Biomedical Science (Sheffield), Dentistry (Sheffield), United Kindgom',
              'University of Sheffield, Biomedical Science (Sheffield), Faculty of Medicine, Dentistry and Health (Sheffield), Medicine (Sheffield), United Kindgom',
              'University of Sheffield, Biomedical Science (Sheffield), Faculty of Science (Sheffield), United Kindgom',
              'University of Sheffield, Biomedical Science (Sheffield), Molecular Biology and Biotechnology (Sheffield), United Kindgom',
              'University of Sheffield, Biomedical Science (Sheffield), United Kindgom',
              'University of Sheffield, Chemical and Biological Engineering (Sheffield), Molecular Biology and Biotechnology (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Faculty of Medicine, Dentistry and Health (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Faculty of Science (Sheffield), Medicine (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Faculty of Science (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Information School (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Medicine (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Molecular Biology and Biotechnology (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Physics and Astronomy (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), United Kindgom',
              'University of Sheffield, Chemistry (Sheffield), Urban Studies and Planning (Sheffield), United Kindgom',
              'University of Sheffield, Computer Science (Sheffield), Human Communication Sciences (Sheffield), United Kindgom',
              'University of Sheffield, Computer Science (Sheffield), Landscape (Sheffield), United Kindgom',
              'University of Sheffield, Computer Science (Sheffield), Psychology (Sheffield), United Kindgom',
              'University of Sheffield, Electronic and Electrical Engineering (Sheffield), Physics and Astronomy (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Engineering (Sheffield), Computer Science (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Animal and Plant Sciences (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Chemistry (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Geography (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Molecular Biology and Biotechnology (Sheffield), Medicine (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Molecular Biology and Biotechnology (Sheffield), Physics and Astronomy (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Molecular Biology and Biotechnology (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Psychology (Sheffield), United Kindgom',
              'University of Sheffield, Faculty of Science (Sheffield), Psychology (Sheffield), Urban Studies and Planning (Sheffield), United Kindgom',
              'University of Sheffield, Landscape (Sheffield), Psychology (Sheffield), United Kindgom',
              'University of Sheffield, Molecular Biology and Biotechnology (Sheffield), United Kindgom',
              'University of Sheffield, Psychology (Sheffield), Faculty of Science (Sheffield), United Kindgom',
              'University of Sheffield, Psychology (Sheffield), Music (Sheffield), United Kindgom',
              'University of Sheffield, Psychology (Sheffield), United Kindgom']



hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for i in range(pages):
    tocurl = 'http://etheses.whiterose.ac.uk/cgi/search/archive/advanced?exp=0|1|-date%2Fcreators_name%2Ftitle|archive|-|iau%3Aiau%3AANY%3AEQ%3ALeeds.FA-MAPH+Leeds.RC-MATH+Leeds.SU-MTHA+Leeds.SU-MTHP+Leeds.RC-PHAS+Sheffield.FCP+Sheffield.PHY+Sheffield.SOM+York.YOR16+York.YOR21|-|eprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive|metadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&_action_search=1&order=-date%2Fcreators_name%2Ftitle&screen=Search&search_offset=' + str(20*i)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        if re.search('MSc ', tr.text) or re.search('MPhil ', tr.text):
            print '  skip Master'
        else:
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
            for td in tr.find_all('td'):
                for span in td.find_all('span'):
                    for a in td.find_all('a'):
                        rec['link'] = a['href']
                        rec['doi'] = '20.2000/' + re.sub('\W', '', a['href'])
                        prerecs.append(rec)

                
i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    aff = []
    restricted = False
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'eprints.creators_name':
                author = meta['content']
                author = re.sub(',', ';', author, count=1)
                author = re.sub(' *, *', ' ', author)
                author = re.sub(';', ',', author)
                rec['autaff'] = [[ author ]]
            #email
            elif meta['name'] == 'eprints.creators_id':
                rec['autaff'][-1].append('EMAIL:' + meta['content'])
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'eprints.keywords':
                parts = re.split(', ', meta['content'])
                if len(parts) > 3:
                    rec['keyw'] += parts
                else:
                    rec['keyw'] += re.split('[;\n] ', meta['content'])
            #thesis type
            elif meta['name'] == 'eprints.thesis_type':
                rec['note'].append(meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['pdflink'] = meta['content']
            #restricted PDF?
            elif meta['name'] == 'eprints.full_text_status':
                if  meta['content'] == 'restricted':
                    restricted = True
            #aff
            elif meta['name'] == 'DC.publisher':
                aff.append(meta['content'])
            #references
            elif meta['name'] == 'eprints.referencetext':
                rec['refs'] = []
                for ref in re.split('\n', meta['content']):
                     rec['refs'].append([('x', ref)])
    aff.append('United Kindgom')
    combinedaff = ', '.join(aff)
    if combinedaff in boringaffs:
        print '  skip "%s"' % (combinedaff)
    else:
        rec['autaff'][-1].append(combinedaff)
        #license
        for a in artpage.body.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
        if not restricted:
            if 'license' in rec.keys():
                rec['FFT'] = rec['pdflink']
            else:
                rec['hidden'] = rec['pdflink']
        else:
            print '  PDF is restricted'
        print '  ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(prerecs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
