# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Memorie della Società Astronomica Italiana
# FS 2019-05-25
import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
publisher = 'Societa Astronomica Italiana'

tc = 'C'
vol = sys.argv[1]
isu = sys.argv[2]
jnlfilename = 'msait%s.%s' % (vol, isu)
if len(sys.argv) > 3: 
    cnum = sys.argv[3]
    jnlfilename += '_%s' % (cnum)
jnl = 'Mem.Soc.Ast.It.'



toclink = 'http://sait.oat.ts.astro.it/ToC.htm'
tocpage = BeautifulSoup(urllib2.urlopen(toclink))
for td in tocpage.body.find_all('td'):
    for a in td.find_all('a'):
        at = re.sub('[\n\t\r]', ' ', a.text.strip())
        searchstring = 'Vol. %s *. *N. *%s ' % (vol, isu)
        if re.search(searchstring, at):
            isutoclink = 'http://sait.oat.ts.astro.it/' + a['href']
            year = re.sub('.*?([12]\d\d\d).*', r'\1', at)
            break

print isutoclink
isutocpage = BeautifulSoup(urllib2.urlopen(isutoclink))
recs = []
for tr in isutocpage.find_all('tr'):
    for td in tr.find_all('td', attrs = {'colspan' : '6'}):
        rec = {'jnl' : jnl, 'vol' : vol, 'issue' : isu, 'tc' : tc, 'year' : year}
        if len(sys.argv) > 3: 
            rec['cnum'] = cnum
        for i in td.find_all('i'):
            rec['tit'] = i.text.strip()
            i.replace_with('')
        auts = re.sub(' and ', ', ', td.text.strip())
        auts = re.sub(' et al.', '', auts)
        rec['auts'] = re.split(' *, *', auts)
    for td in tr.find_all('td', attrs = {'valign' : 'bottom'}):
        rec['p1'] = re.sub('.*?(\d+).*', r'\1', td.text.strip())
    for td in tr.find_all('td', attrs = {'align' : 'center'}):
        for a in td.find_all('a'):
            if re.search('PDF', a.text):
                rec['link'] =  re.sub('(.*\/).*', r'\1', isutoclink) + a['href']
                if 'auts' in rec.keys():
                    print rec.keys()
                    recs.append(rec)

                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
