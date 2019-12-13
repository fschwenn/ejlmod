# -*- coding: utf-8 -*-
#harvest theses from Mainz U.
#FS: 2019-12-09


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

yearstocover = 1

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Mainz U.'

jnlfilename = 'THESES-MAINZ-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}
def tfstrip(x): return x.strip()
recs = []


tocurls = ['https://publications.ub.uni-mainz.de/theses/ergebnis.php?suchart=teil&Lines_Displayed=0&sort=o.date_year+DESC%2C+o.title&suchfeld1=oi.inst_nr&suchwert1=0801&opt1=AND&suchfeld2=person&suchwert2=&opt2=AND&suchfeld3=date_year&suchwert3=&startindex=0&page=0&dir=2&suche=&la=de', 'https://publications.ub.uni-mainz.de/theses/ergebnis.php?suchart=teil&Lines_Displayed=0&sort=o.date_year+DESC%2C+o.title&suchfeld1=oi.inst_nr&suchwert1=0802&opt1=AND&suchfeld2=person&suchwert2=&opt2=AND&suchfeld3=date_year&suchwert3=&startindex=0&page=0&dir=2&suche=&la=de', 'https://publications.ub.uni-mainz.de/theses/ergebnis.php?suchart=teil&Lines_Displayed=0&sort=o.date_year+DESC%2C+o.title&suchfeld1=oi.inst_nr&suchwert1=0804&opt1=AND&suchfeld2=person&suchwert2=&opt2=AND&suchfeld3=date_year&suchwert3=&startindex=0&page=0&dir=2&suche=&la=de']
for i in range(len(tocurls)):
    tocurl = tocurls[i]
    print tocurl
    tocfilename = '/tmp/%s.toc.%i' % (jnlfilename, i)
    if not os.path.isfile(tocfilename):
        os.system('wget -O %s "%s"' % (tocfilename, tocurl))
    inf = open(tocfilename, 'r')

    #webpage ist korrupt
    for line in inf.readlines():
        if re.search('publications.UB.Uni-Mainz.*opus', line):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}  
            rec['link'] = re.sub('.*HREF="(.*?)".*', r'\1', line.strip())
        if re.search('<TD class="normalergebnis" VALIGN="TOP">20', line):
            rec['date'] = re.sub('.*<TD class="normalergebnis" VALIGN="TOP">(20..).*', r'\1', line.strip())
            try:
                if int(rec['date']) >= now.year - yearstocover:
                    recs.append(rec)
            except:
                print rec
    inf.close()
    print len(recs)
            
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i}---{ %s }------' % (i, len(recs), rec['link'])
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

    for table in artpage.body.find_all('table', attrs = {'class' : 'front'}):
        for tr in table.find_all('tr'):
            tds = tr.find_all('td')
            name = tds[0].text.strip()
            content = tds[1].text.strip()
            #author
            if re.search('Person:', name):
                for a in tds[1].find_all('a'):
                    rec['autaff'] = [[ a.text.strip(), publisher ]]
            #title
            elif re.search('Titel:', name):
                rec['tit'] = content
            #FFT
            elif re.search('Dokument:', name):
                for a in tds[1].find_all('a'):
                    rec['pdf_url'] = a['href']
            #keywords
            elif re.search('Freie Schlag.*nglisch', name):
                rec['keyw'] = re.split(', ', content)
            #URN
            elif re.search('URN:', name):
                rec['urn'] = content
            #language
            elif re.search('Sprache', name):
                if re.search('eutsch', content):
                    rec['language'] = 'german'
            #OA? Fulltext?
            elif re.search('Open Access', name):
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
            #pages
            elif re.search('Quelle', name):
                if re.search('\d+ S\.', content):
                    rec['pages'] = re.sub('.*?(\d+) S\..*', r'\1', content)
            #abstract
            elif re.search('^Abstract', name):
                rec['abs1'] = content
                abs1eng = len(re.findall('[tT]he', rec['abs1'])) - len(re.findall(' (der|die|das|den|dem|des) ', rec['abs1']))
            elif re.search('Abstract', name):
                rec['abs2'] = content
                abs2eng = len(re.findall('[tT]he', rec['abs2'])) - len(re.findall(' (der|die|das|den|dem|des) ', rec['abs2']))
    #decide which abstract to take
    if 'abs2' in rec.keys() and abs2eng > abs1eng:
        rec['abs'] = rec['abs2']
    elif 'abs1' in rec.keys():
        rec['abs'] = rec['abs1']
    else:
        rec['note'] = [ 'Vorsicht: kein Abstract!' ]
    #no urn?
    if not 'urn' in rec.keys():
        rec['doi'] = '20.2000/MAINZ/' + re.sub('\W', '', rec['link'][20:])
    print '  ', rec.keys()



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
