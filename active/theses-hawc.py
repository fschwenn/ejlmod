# -*- coding: utf-8 -*-
#harvest HAWC theses
#FS: 2020-11-16


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
import ssl

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'HAWC'

typecode = 'T'

jnlfilename = 'THESES-HAWC-%s' % (stampoftoday)

recs = []

tocurl = 'https://www.hawc-observatory.org/publications'
try:
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))



section = ''
for div in tocpage.find_all('div', attrs = {'class' : 'content'}):
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'h5':
            for a in child.find_all('a'):
                if a.has_attr('name'):
                    section = a['name']
                    print '==={ %s }===' % (section)
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'MARC' : []}
        elif child.name == 'p':
            if section == 'thesis':
                rec = {'jnl' : 'BOOK', 'tc' : 'T', 'exp' : 'HAWC'}
                for a in child.find_all('a'):
                    if re.search('http:', a['href']):
                        rec['link'] = a['href']
                        if re.search('pdf$', a['href']):
                            rec['hidden'] = a['href']
                    else:
                        rec['link'] = 'https://www.hawc-observatory.org/' + a['href']
                        if re.search('pdf$', a['href']):
                            rec['hidden'] = 'https://www.hawc-observatory.org/' + a['href']
                    rec['tit'] = re.sub('[\n\t\r]', '', a.text.strip())
                    rec['doi'] = '20.2000/HAWC/' + re.sub('\W', '', a['href'])
                for br in child.find_all('br'):
                    br.replace_with(' XXX ')
                pt = re.split(' XXX ', re.sub('[\n\t\r]', '', child.text.strip()))
                rec['autaff'] = [[ pt[1] ]]
                if re.search('[12]\d\d\d', pt[2]):
                    rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', pt[2])
                rec['autaff'][-1].append(re.sub(' *\([12].*', '', pt[2]))
                if 'date' in rec.keys() and int(rec['date']) < now.year-1:
                    print '  skip'
                else:
                    print ' ', rec.keys()
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
