# -*- coding: utf-8 -*-
#look for interesting SPIE-conferences

import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import re
import codecs
import time

ejldir = '/afs/desy.de/user/l/library/dok/ejl/backup'

rpp = 5000

verbose = False
checkpagination = False

area = sys.argv[1]
   
if area in ['qis', 'QIS']:
    keywords = ["quantum computing", "quantum computer", "qubit", "quantum information", "quantum algorithm", "qudit", "variational quantum", "quantum circuit", "quantum device", "quantum sensing", "quantum sensor"]
    namelikekeywords = []
    uninteresting = ['11200', '11203', '11264', '11268', '11269', '11274', '11276',
                     '11284', '11289', '11290', '11294', '11299', '11300', '11301', 
                     '11302', '11309', '11315', '11323', '11324', '11326', '11331', 
                     '11387', '11409', '11427', '11460', '11464', '11467', '11486', 
                     '11493', '11497', '11518', '11548', '11553', '11554', '11557', 
                     '11562', '11563', '11582', '11673', '11687', '11688', '11689', 
                     '11690', '11695', '11704', '11718', '11741', '11742', '11746', 
                     '11753', '11769', '11790', '11793', '11807', '11808', '11813', 
                     '11880', '11889', '11890', '11894', '11895', '11902', '11903', 
                     '11907', '11940', '11967', '11982', '11992', '11996', '11997',
                     '12020', '12194', '12130', '12067', '12030', '12018', '11988',
                     '11716', '11882']                     
elif area in ['hep', 'HEP']:
    keywords = ["LHC", "RHIC", "BELLE", "CERN", "DESY", "SLAC", "Fermilab", "KEK", "JINR", "MU2E", "CALICE", "IceCube", "VIRGO"] # ILC -> iterative learning control
    namelikekeywords = ['NICA']
    uninteresting = ['11203', '11216', '11219', '11221', '11229', '11234', '11240',
                     '11241', '11251', '11254', '11263', '11264', '11265', '11266',
                     '11268', '11274', '11275', '11285', '11286', '11292', '11296', 
                     '11307', '11312', '11320', '11324', '11326', '11379', '11387',
                     '11391', '11393', '11394', '11406', '11407', '11421', '11427', 
                     '11429', '11430', '11435', '11440', '11441', '11456', '11462',
                     '11465', '11471', '11472', '11480', '11481', '11494', '11503', 
                     '11510', '11513', '11516', '11522', '11524', '11527', '11530',
                     '11532', '11534', '11539', '11542', '11549', '11553', '11558', 
                     '11566', '11567', '11574', '11575', '11582', '11583', '11590',
                     '11591', '11593', '11595', '11597', '11602', '11605', '11610', 
                     '11617', '11618', '11619', '11621', '11628', '11631', '11634', 
                     '11637', '11639', '11641', '11645', '11650', '11655', '11665', 
                     '11671', '11672', '11684', '11692', '11706', '11708', '11712', 
                     '11720', '11723', '11731', '11741', '11743', '11749', '11756', 
                     '11766', '11767', '11772', '11781', '11784', '11788', '11797', 
                     '11798', '11799', '11800', '11800', '11809', '11813', '11815', 
                     '11818', '11819', '11821', '11832', '11837', '11845', '11846', 
                     '11847', '11849', '11857', '11868', '11871', '11875', '11878', 
                     '11880', '11884', '11890', '11894', '11899', '11900', '11915', 
                     '11916', '11919', '11922', '11924', '11925', '11934', '11935', 
                     '11938', '11944', '11949', '11951', '11969', '11973', '11980', 
                     '11982', '11985', '11986', '11989', '11993', '11994', '11999', 
                     '12001', '12004', '12005', '12007', '12010', '12013', '12017', 
                     '12018', '12019', '12021', '12023', '12031', '12033', '12037', 
                     '12038', '12039', '12042', '12046', '12050', '12061', '12066', 
                     '12073', '12076', '12078', '12127', '12128', '12153', '12156', 
                     '12157', '12163', '12164', '12178', '12192', '12193', '12194',
                     '11270']
#interesting but only videos:
uninteresting += ['11918', '11917', '11714'] 

    
regexs = []
for kw in keywords+namelikekeywords:
    regexs.append(re.compile('([^A-Za-z])(%s)' % (kw)))

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
startyear = str(now.year-2)
stopyear = str(now.year)

done = []
redoki = re.compile('.*spie(\d\d\d+).*')
for ordner in [ejldir, os.path.join(ejldir, str(now.year-1)), os.path.join(ejldir, str(now.year-2))]:
    for datei in os.listdir(ordner):
        if redoki.search(datei):
            done.append(redoki.sub(r'\1', datei))
print '%i done, %i uninteresting' % (len(done), len(uninteresting))

searchterm = '%22)+OR+(%22'.join(keywords)
if namelikekeywords:
    searchterm += '%22)+ABSTRACT:(%22'
    searchterm += '%22)+ABSTRACT:(%22'.join(namelikekeywords)
    searchterm += '%22)+TITLE:(%22'
    searchterm += '%22)+TITLE:(%22'.join(namelikekeywords)
conferences = {}

tocfilename = '/tmp/spie_confsearch.%s.%s' % (area, stampoftoday)
toclink = "https://www.spiedigitallibrary.org/search?term=((%22" + re.sub(' ', '+', searchterm) + "%22)&PubType=Proceedings_Article&startYear=" + str(startyear) + "&endYear=" + str(stopyear) + "&sortBy=PubDateDesc&pageSize=" + str(rpp)
if verbose: print toclink
if not os.path.isfile(tocfilename):
    os.system('wget -T 300 -t 3 -q -O %s "%s"' % (tocfilename, toclink))
    time.sleep(5)
inf = codecs.EncodedFile(open(tocfilename, mode='rb'), "utf8")
lines = re.sub('[\n\r\t]', ' ', ''.join(inf.readlines()))
lines = re.sub('\\\\[nrt]', '', lines)
lines = re.sub('\\\\"', '"', lines)
parts = re.split('<div class=..?TOCLineItemRowCol2', lines)
if verbose:
    print len(parts), 'parts'


    
conferences = {}
divs = []
for part in parts[1:-1]:
    div = BeautifulSoup('<div class="TOCLineItemRowCol2' + re.sub('<.div><div style="padding-left.*', '', part), features="lxml")
    divs.append(div)
    (artabs, arttit, artlink) = ('', '', '')
    for button in div.find_all('button', attrs = {'class' : 'form-group'}):
        if button.has_attr('onclick'):
            doi = re.sub('.*(10.1117\/[0-9A-Za-z\.\/]*).*', r'\1', button['onclick'])
            artlink = 'http://doi.org/' + doi
    for text in div.find_all('text', attrs = {'class' : 'ProfileTOCLineItemText'}):
        textt = text.text.strip()
        if not re.search('^(Proc. SPIE. |This PDF file)', textt):
            if len(textt) > 50:
                artabs = textt
                for regex in regexs:
                    artabs = regex.sub(r'\1<font color="red">\2</font>', artabs)
    for span in div.find_all('span', attrs = {'class' : 'ProfileTOCLineItemBoldText'}):
        arttit = span.text.strip()
    for text in div.find_all('text', attrs = {'class' : 'ProfileTOCLineItemText'}):
        conftit = text.text
        if re.search('^Proc. SPIE. ', conftit):
            confnumber = re.sub('\D+?(\d+).*', r'\1', conftit)
            if confnumber in conferences.keys():
                conferences[confnumber]['articles'].append((arttit, artlink, artabs))
            elif confnumber in done:
                if verbose:
                    print '  %s already done' % (confnumber)
            elif confnumber in uninteresting:
                if verbose:
                    print '  %s not interesting' % (confnumber)
            else:
                if verbose:
                    print ' ', confnumber, conftit
                conferences[confnumber] = {'title' : re.sub('^\D+?\d+,? *', '', conftit), 'articles' : [(arttit, artlink, artabs)]}
    

        
ouf = codecs.EncodedFile(codecs.open('/afs/desy.de/group/library/www/html/akw/spie_confsearch_%s.html' % (area.lower()), mode='wb'), 'utf8')
ouf.write('<html>\n <head><title>SPIE conference search (%s)</title></head>\n' % (area.upper()))
ouf.write(' <body>\n  <h2>%s: %s [%s]</h2>\n' % (area.upper(), ', '.join(keywords), stampoftoday))
ouf.write('Please add uninteresting conferences in /afs/desy.de/user/l/library/proc/spie_confsearch.py<br>')
ouf.write('  <ol>\n')
confnumbers = conferences.keys()
confnumbers.sort()
i = 0
pagestotal = 0
for confnumber in confnumbers:
    i += 1
    if verbose:
        print '\n---{ %i/%i }---{ %s | %s }---' % (i, len(confnumbers), confnumber, conferences[confnumber]['title'])
    else:
        print '---{ %i/%i }---' % (i, len(confnumbers))
    ouf.write('   <li>\n')
    conflink = 'https://www.spiedigitallibrary.org/conference-proceedings-of-spie/%s.toc' % (confnumber)
    try:
        ouf.write('    <h3><a href="%s">%s</a></h3>\n' % (conflink, conferences[confnumber]['title']))
    except:
        ouf.write('    <h3><a href="%s">%s</a></h3>\n' % (conflink, '...'))
    numberofarticles = 0
    pagenumbers = []
    confsubtit = []
    #check number of conferencepapers in that conference?
    if checkpagination:
        urltrunc = "https://www.spiedigitallibrary.org"
        toclink = "%s/conference-proceedings-of-spie/%s.toc" % (urltrunc, confnumber)
        try:
            print 'open %s' % (toclink)
            page = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink), features="lxml")
            recs = []
            for div in page.body.find_all('div'):
                if div.attrs.has_key('class'):
                    if 'TOCLineItemRow1' in div['class']:
                        numberofarticles += 1
            for text in page.body.find_all('text', attrs = {'class' : 'ConferenceTitleText'}):
                confsubtit.append(text.text)
            time.sleep(22)
        except:
            pass
        if verbose:
            print ' ', numberofarticles
        pagestotal += numberofarticles
    #conference infos
    if confsubtit:
        ouf.write('    %s<br>\n' % ('; '.join(confsubtit)))

    #loop of articles to get abstract?
    ouf.write('    <ol>\n')
    for (arttit, artlink, artabs) in conferences[confnumber]['articles']:
        try:
            ouf.write('     <li><a href="%s">%s</a><br>' % (artlink, arttit))
        except:
            ouf.write('     <li><a href="%s">%s</a><br>' % (artlink, '...'))
        try:
            ouf.write(artabs)
        except:
            pass
        ouf.write('</li>\n')

    ouf.write('    </ol><br>\n')   
    if checkpagination:
        ouf.write('    /home/library/.virtualenvs/inspire/bin/python $afl/proc/spie_proc_crawler.py %s # %i ' % (confnumber, numberofarticles))
    else:
        ouf.write('    /home/library/.virtualenvs/inspire/bin/python $afl/proc/spie_proc_crawler.py %s' % (confnumber))     
ouf.write('  </ol>\n')
      
if checkpagination:
    ouf.write('%i conference papers in total' % (pagestotal))

    
ouf.write(' </body>\n</html>')

print '\nhttp://www-library.desy.de/akw/spie_confsearch_%s.html\n' % (area.lower())
