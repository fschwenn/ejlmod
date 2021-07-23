# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Bulgarian Academy of Science
# FS 2018-09-24

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'Bulgarian Academy of Sciences'
typecode = 'P'
year = sys.argv[1]
issue = sys.argv[2]
jnlfilename = 'crabs%s.%s' % (year, issue)

if issue == '10':
    urltrunk = 'http://www.proceedings.bas.bg/content/%s_a_cntent.html' % (year)
elif issue == '11':
    urltrunk = 'http://www.proceedings.bas.bg/content/%s_b_cntent.html' % (year)
elif issue == '12':
    urltrunk = 'http://www.proceedings.bas.bg/content/%s_c_cntent.html' % (year)
else:
    urltrunk = 'http://www.proceedings.bas.bg/content/%s_%s_cntent.html' % (year, issue)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))

recs = []
for tr in tocpage.body.find_all('tr'):
    for a in tr.find_all('a', attrs = {'title' : 'Click For Abstract'}):
        artlink = a['onclick']
        artlink = re.sub('.*(http.*)\'', r'\1', artlink)
        try:
            print artlink
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (artlink)
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
        rec = {'jnl' : 'Compt.Rend.Acad.Bulg.Sci.', 'issue' : issue, 'tc' : typecode,
               'year' : year}
        #pubnote
        for center in artpage.body.find_all('center'):
            for small in center.find_all('small'):
                st = small.text.strip()
                if re.search('Vol \d+', st):
                    rec['vol'] = re.sub('.*Vol (\d+).*', r'\1', st)
                p1p2 = re.sub('.*pp\.? *(\d.*\d).*', r'\1', st)
                parts = re.split('\-', p1p2)
                rec['p1'] = parts[0]
                if len(parts) > 1:
                    rec['p2'] = parts[1]
        #title
        for h2 in artpage.body.find_all('h2'):
            if not 'tit' in rec.keys():
                rec['tit'] = h2.text.strip()
        #authors
        for h3 in artpage.body.find_all('h3'):
            rec['auts'] = re.split(' *, *', h3.text.strip())
        #abstract
        for p in artpage.body.find_all('p', attrs = {'class' : 'abs'}):
            rec['abs'] = p.text.strip()
        #keywords
        for p in artpage.body.find_all('p', attrs = {'class' : 'keyw'}):
            keyw = re.sub('Key words: *', '', p.text.strip())
            rec['keyw'] = re.split(' *, *', keyw)
        #doi
        for div in artpage.body.find_all('div'):
            for small in div.find_all('small'):
                st = small.text.strip()
                if re.search('DOI', st):
                    rec['doi'] = re.sub('DOI: *', '', st)
        #topic               
        for p in artpage.body.find_all('p', attrs = {'class' : 'right'}):
            rec['note'] = [ p.text.strip() ]
        #artiocle link
        if not 'doi' in rec.keys():
            rec['link'] = artlink
        recs.append(rec)

                                      
#closing of files and printing
xmlf    = os.path.join(xmldir ,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()

