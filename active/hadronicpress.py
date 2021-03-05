# -*- coding: UTF-8 -*-
#program to harvest journas from hadronic Press
# FS 2021-01-16


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


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

publisher = 'Hadronic Press'
tc = ''
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]

if jnl == 'hj':
    jnlname = 'Hadronic J.'
elif jnl == 'agg':
    jnlname = 'Alg.Groups Geom.'
toclink = 'http://hadronicpress.com/%s/%sVol/%s%s-%sI.php' % (jnl.upper(), jnl.upper(), jnl.upper(), vol, issue)
jnlfilename = "hadronic%s%s.%s" % (jnl, vol, issue)

print "get table of content... from %s" % (toclink)

try:
    tocpage = BeautifulSoup(urllib2.urlopen(toclink), features="lxml")
except:
    print '%s not found' % (toclink)
    sys.exit(0)


recs = []

for title in tocpage.find_all('title'):
    year = re.sub('.*([12]\d\d\d).*', r'\1', title.text.strip())
    print year
for article in tocpage.body.find_all('article'):
    for p in article.find_all('p')[1:]:
        rec = {'jnl' : jnlname, 'tc' : tc, 'issue' : issue, 'note' : [], 
               'autaff' : [], 'keyw' : [], 'vol' : vol, 'year' : year}
        strongs = p.find_all('strong')
        #title and page
        titpag = re.sub('[\n\t\r]', ' ', strongs[0].text.strip())
        rec['p1'] = re.sub('.*\D(\d+)$', r'\1', titpag)
        rec['tit']= re.sub('(.*),.*', r'\1', titpag)
        rec['doi'] = '20.2000/HadroniPress/%s/%s/%s/%s' % (jnl, vol, issue, rec['p1'])
        strongs[0].decompose()
        #links
        for a in strongs[-1].find_all('a'):
            rec['link'] = a['href']
            strongs[-1].decompose()
        #authors
        for strong in strongs[1:-1]:
            st = strong.text.strip()
            strong.replace_with(' YYY ' + st + ' XXX ')
        for br in p.find_all('br'):
            br.replace_with(' ')
        for autaff in re.split(' +YYY +', re.sub('^ *YYY *', '', re.sub('[\n\t\r]', ' ', p.text.strip()))):            
            parts = re.split(' +XXX +', autaff)
            rec['autaff'].append(parts)
        recs.append(rec)
        print rec.keys()
    
    
#write xml
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
