# -*- coding: UTF-8 -*-
#program to harvest journals from the Royal Society
# FS 2016-09-27


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

publisher = 'Royal Society'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]
if   (jnl == 'prs'): 
    issn = '1364-5021'
    url = 'PRSLA'
    jnlname = 'Proc.Roy.Soc.Lond.'
    vol = 'A' + vol
    urltrunk = 'http://rspa.royalsocietypublishing.org'
elif (jnl == 'prts'): 
    issn = '1364-503x'
    url = 'PTRSA'
    vol = 'A' + vol
    jnlname = 'Phil.Trans.Roy.Soc.Lond.'
    urltrunk = 'http://rsta.royalsocietypublishing.org'

jnlfilename = "%s%s.%s" % (jnl,vol,issue)
toclink = "%s/content/%s/%s.toc" % (urltrunk, re.sub('^[A-Z]', '', vol), issue)

print "%s%s, Issue %s" %(jnlname,vol,issue)
print "get table of content... from %s" % (toclink)

tocpage = BeautifulSoup(urllib2.urlopen(toclink))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'issue-toc'}):
    for a in div.find_all('a', attrs = {'class' : 'highwire-cite-linked-title'}):
        artlink = "%s%s" % (urltrunk, a['href'])
        print artlink
        artpage = BeautifulSoup(urllib2.urlopen(artlink))
        rec = {'jnl' : jnlname, 'tc' : 'P', 'vol' : vol, 'issue' : issue, 'autaff' : [], 'refs' : []}
    #meta
        autaff = False
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                if meta['name'] == 'citation_firstpage':
                    rec['p1'] = meta['content']
                if meta['name'] == 'citation_lastpage':
                    rec['p2'] = meta['content']
                elif meta['name'] == 'citation_doi':
                    rec['doi'] = meta['content']
                elif meta['name'] == 'article:section':
                    rec['note'] = [ meta['content'] ]
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                elif meta['name'] == 'citation_author':
                    if autaff:
                        rec['autaff'].append(autaff)
                    autaff = [ meta['content'] ]
                elif meta['name'] == 'citation_author_institution':
                    autaff.append(meta['content'])
                elif meta['name'] == 'citation_author_orcid':
                    orcid = re.sub('.*\/', '', meta['content'])
                    autaff.append('ORCID:%s' % (orcid))
                elif meta['name'] == 'citation_author_email':
                    email = meta['content']
                    autaff.append('EMAIL:%s' % (email))
                elif meta['name'] == 'DC.Description':
                    rec['abs'] = meta['content']
        rec['autaff'].append(autaff)
        #ref
        for ol in artpage.body.find_all('ol', attrs = {'class' : 'cit-list'}):
            for li in ol.find_all('li', recursive=False):
                rec['refs'].append([('x', re.sub('\)OpenUrl', ' ) ', li.text.strip()))])
        recs.append(rec)


  
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
