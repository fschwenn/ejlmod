# -*- coding: UTF-8 -*-
#program to harvest journals from the Nuleonika new page
# FS 2016-10-24


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


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'De Gruyter'
tc = 'P'

year = sys.argv[1]
vol = sys.argv[2]
iss = sys.argv[3]
if len(sys.argv) > 4:
    cnum = sys.argv[4]

jnlname = 'Nukleonika'
toclink = 'https://www.degruyter.com/view/j/nuka.%s.%s.issue-%s/issue-files/nuka.%s.%s.issue-%s.xml' % (year, vol, iss, year, vol, iss)
jnlfilename = "%s%s.%s" % (jnlname, year, iss)


print "get table of content from %s ..." % (toclink)

recs = []
tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
for li in tocpage.find_all('li', attrs = {'class' : 'smart-nav-item notread'}):
    rec = {'jnl' : jnlname, 'tc' : tc, 'note' : [], 'auts' : [], 'aff' : [],
           'year' : year, 'vol' : vol, 'issue' : iss}
    for a in li.find_all('a'):
        artlink = 'https://www.degruyter.com' + a['href']
        rec['tit'] = a.text.strip()
        print rec


  
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
