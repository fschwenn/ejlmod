# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest http://www.mathnet.ru
# FS 2016-07-20

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

jnldict = {'uzku'  : {'tit' : 'Uch.Zapiski Kazan Univ.', 
                      'publisher' : 'Kazan University', 
                      'oa' : True},
           'aa'    : {'tit' : 'Alg.Anal.', 
                      'publisher' : 'Academizdatcenter "Nauka"', 
                      'embargo' : 3,
                      'english' : 'St.Petersburg Math.J.'},
           'zvmmf' : {'tit' : 'Zh.Vych.Mat.Mat.Fiz.', 
                      'publisher' : 'Russian Academy of Sciences, Academizdatcenter "Nauka"', 
                      'embargo' : 3,
                      'english' : 'Comput.Math.Math.Phys.'},
           'jetpl' : {'tit' : 'Pisma Zh.Eksp.Teor.Fiz.',
                      'publisher' : 'Russian Academy of Sciences, Academizdatcenter "Nauka"',
                      'embargo' : 3,
                      'english' : 'JETP Lett.'},
           'ufn'   : {'tit' : 'Usp.Fiz.Nauk',
                      'publisher' : 'Russian Academy of Sciences, Lebedev Physical Institute of the RAS',
                      'oa' : True,
                      'english' : 'Phys.Usp.'},
           'de'    : {'tit' : 'Diff.Urav.',
                      'publisher' : 'Russian Academy of Sciences, Publishing House "Nauka"',
                      'oa' : False},
           'ppi'   : {'tit' : 'Prob.Peredachi Info.',
                      'publisher' : 'Russian Academy of Sciences, Academizdatcenter "Nauka"',
                      'embargo' : 3},
           'rcd'   : {'tit' : 'Regular Chaot.Dyn.',
                      'publisher' : 'MAIK Nauka/Interperiodika',
                      'oa' : False},
           'qe'    : {'tit' : 'Kvantovaya Elektron.',
                      'publisher' : 'Lebedev Physics Institute of the Russian Academy of Sciences',
                      'embargo' : 2},
           'znsl'  : {'tit' : 'Zap.Nauchn.Semin.',
                      'publisher' : 'St. Petersburg Department of V. A. Steklov Mathematical Institute, Russian Academy of Sciences',
                      'oa' : True,
                      'english' : 'J.Math.Sci.'},
           'inta'  : {'tit' : 'Itogi Nauk.Tekh.Ser.Alg.Topol.Geom.',
                      'publisher' : 'll-Russian Institute for Scientific and Technical Information of Russian Academy of Sciences',
                      'embargo' : 1},
           'al'    : {'tit' : 'Alg.Logika',
                      'publisher' : 'Siberian Fund for Algebra and Logic', 
                      'embargo' : 3},
           'basm'  : {'tit' : 'Bul.Acad.Sti.Rep.Moldova (Fiz.Teh.)',
                      'publisher' : 'Institute of Mathematics and Computer Science of the Academy of Sciences of Moldova',
                      'oa' : True},
           'fpm'   : {'tit' : 'Fundam.Prikl.Mat.',
                      'publisher' : 'Center of New Information Technologies of Moscow State University, Publishing House "Open Systems"',
                      'oa' : True},
           'ivm'   : {'tit' : 'Izv.Vuz.Mat.',
                      'publisher' : 'Kazan (Volga Region) Federal University', 
                      'embargo' : 1},
           'jsfu'  : {'tit' : 'J.Sib.Fed.U.',
                      'publisher' : 'Siberian Federal University',
                      'oa' : True},
           'mzm'   : {'tit' : 'Mat.Zametki',
                      'publisher' : 'Steklov Mathematical Institute of Russian Academy of Sciences', 
                      'embargo' : 3},
           'sm'    : {'tit' : 'Mat.Sbornik',
                      'publisher' : 'Steklov Mathematical Institute of Russian Academy of Sciences', 
                      'embargo' : 3},
           'mmj'   : {'tit' : 'Moscow Math.J.',
                      'publisher' : 'Independent University of Moscow, Department of Mathematics of Higher School of Economics',
                      'oa' : False}, 
           'smj'   : {'tit' : 'Sib.Mat.Zh.',
                      'publisher' : 'Siberian Branch of the Russian Academy of Sciences', 
                      'embargo' : 1},
           'spm'   : {'tit' : 'Sovr.Probl.Mat.',
                      'publisher' : 'Steklov Mathematical Institute of Russian Academy of Sciences',
                      'oa' : True},
           'tvp'   : {'tit' : 'Teor.Veroyatn.Primen.',
                      'publisher' : 'Steklov Mathematical Institute of Russian Academy of Sciences',
                      'oa' : False},
           'tmf'   : {'tit' :'Teor.Mat.Fiz.',
                      'publisher' : 'Steklov Mathematical Institute of Russian Academy of Sciences', 
                      'embargo' : 3},
           'mmo'   : {'tit' : 'Trud.Mosk.Mat.Obshch.',
                      'publisher' : 'Moscow Centre of Continuous Mathematical Education (MCCME)',
                      'oa' : True},
           'tsp'   : {'tit' : 'Trud.Semin.Im.I.G.Petrovskogo',
                      'publisher' : 'Moscow University Publishing House',
                      'oa' : True},
           'uzmu'  : {'tit' : 'Uch.Zap.Kharkov.Gos.Univ.',
                      'publisher' : 'Moscow University Press',
                      'oa' : True},
           'rcr'   : {'tit' : 'Usp.Khim.',
                      'publisher' : 'Russian Academy of Sciences, N. D. Zelinsky Institute of Organic Chemistry of RAS',
                      'oa' : False}, 
           'rm'   : {'tit' : 'Usp.Mat.Nauk',
                     'publisher' : 'Steklov Mathematical Institute of Russian Academy of Sciences', 
                     'embargo' : 3,
                     'english' : 'Russ.Math.Surveys'}}

#           '' : {'tit' : '',
#                      'publisher' : '',
#                      'embargo' : }, 



jrnid = sys.argv[1]
vol = sys.argv[2]
iss = sys.argv[3]
year = sys.argv[4]

#check embargo time
if jnldict[jrnid].has_key('embargo'):
    now = datetime.datetime.now()
    if now.year - int(year) > jnldict[jrnid]['embargo']:
        jnldict[jrnid]['oa'] = True

publisher = jnldict[jrnid]['publisher']

tocurl = 'http://www.mathnet.ru/php/archive.phtml?jrnid=%s&wshow=issue&bshow=contents&series=0&volume=%s&issue=%s&option_lang=eng&year=%s' % (jrnid, vol, iss, year)
print tocurl
tocpage = BeautifulSoup(urllib2.urlopen(tocurl))

artlinks = []
for table in tocpage.body.find_all('table', attrs = {'cellpadding' : '5'}):
    for td in table.find_all('td'):
        for b in td.find_all('b'):
            artlinks.append(b.text)
        for a in td.find_all('a', attrs = {'class' : 'SLink'}):
            if a.has_attr('href') and not re.search('^ *Editorial', a.text) and not re.search('php\/getFT.phtml', a['href']):
                artlinks.append('http://www.mathnet.ru' + a['href'])


print artlinks 


recs = []
note = ''
if vol == '': vol = year
for artlink in artlinks:
    print artlink
    if not re.search('^http', artlink):
        note = artlink
        continue
    rec = {'jnl' : jnldict[jrnid]['tit'], 'tc' : 'P', 'year' : year, 
           'vol' : vol, 'issue' : iss, 'auts' : [], 'note' : [ note ],
           'link' : artlink}
    #rec['cnum'] = 'C10-11-01'
    try:
        articlepage = BeautifulSoup(urllib2.urlopen(artlink))
        time.sleep(1)
    except:
        print " - sleep -"
        time.sleep(300)
        articlepage = BeautifulSoup(urllib2.urlopen(artlink))
    #title
    for span in articlepage.body.find_all('span', attrs = {'class' : 'red'}):
        for font in span.find_all('font', attrs = {'size' : '+1'}):
            rec['tit'] = font.text.strip()
    #abstract and keywords and pages and language and DOI
    for table in articlepage.body.find_all('table', attrs = {'width' : '100%'}):
        for textrow in re.split('[\t\n]+', table.text):
            if textrow == 'Abstract:':
                rec['abs'] = ''
            elif textrow == 'Keywords:':
                rec['keyw'] = []
            elif rec.has_key('abs') and not rec['abs']:
                rec['abs'] = textrow
            elif rec.has_key('keyw') and not rec['keyw']:
                rec['keyw'] = re.split(' *, *', textrow)
            elif re.search('^\\\\pages \d', textrow) and not rec.has_key('p1'):
                pages = re.split('\-+', textrow[7:].strip())
                rec['p1'] = pages[0]
                if len(pages) > 1:
                    rec['p2'] = pages[1]
            elif textrow == ' References (in Russian):':
                rec['language'] = 'Russian'
                if 'in Russian' not in rec['note']:
                    rec['note'].append('in Russian')
            elif re.search('^\\\\crossref.http...dx', textrow):
                rec['doi'] = re.sub('.*dx.doi.org.(10.*)\}.*', r'\1', textrow.strip())                
    #pages
    if not rec.has_key('p1'):
        for title in articlepage.head.find_all('title'):
            pagerange = re.sub('.*, *', '', title.text).strip()
            pages = re.split('\D+', pagerange)
            rec['p1'] = pages[0]
            if len(pages) > 1:
                rec['p2'] = pages[1]
    #english version
    if jnldict[jrnid].has_key('english'):
        rec['note'].append('Englische Uebersetzung in Zeitschrift "%s"' % (jnldict[jrnid]['english']))
    #authors
    for a in articlepage.body.find_all('a', attrs = {'class' : 'SLink'}):
        if a.has_attr('href'):
            if re.search('person.phtml', a['href']):
                author = re.sub('\xa0', ' ', a.text.strip())
                rec['auts'].append(author)
    #fulltext
    for a in articlepage.body.find_all('a'):
        if a.has_attr('href') and a.text == 'PDF file':
            pdflink = False
            try:
                if re.search('[fF]ull.*[Tt]ext', a.previous_sibling.text):
                    pdflink = 'http://www.mathnet.ru' + a['href']
            except:
                try:
                    if re.search('[fF]ull.*[Tt]ext', a.previous_sibling.previous_sibling.text):
                        pdflink = 'http://www.mathnet.ru' + a['href']
                except:
                    pass
            if pdflink:
                rec['pdf'] = 'http://www.mathnet.ru' + a['href']
                if jnldict[jrnid].has_key('oa') and jnldict[jrnid]['oa']:
                    rec['FFT'] =  rec['pdf']
    #references
    for a in articlepage.body.find_all('a'):
        if a.has_attr('href') and a.text == 'HTML file':
            reflink = 'http://www.mathnet.ru' + a['href']
            refpage = BeautifulSoup(urllib2.urlopen(reflink))
            rec['refs'] = []
            for tr in refpage.body.find_all('tr'):
                trt = tr.text.strip()
                if len(trt) > 10:
                    rec['refs'].append([('x', trt)])
            print ' %i references found' % (len(rec['refs']))
    print rec
    recs.append(rec)


jnlfilename = 'mathnetru_%s%s.%s' % (jrnid, vol, iss)
#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
