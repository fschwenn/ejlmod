#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest The African Review of Physics
# FS 2012-06-01

import os
import ejlmod2
import codecs
import re
import sys
import unicodedata
import string
from removehtmlgesocks import removehtmlgesocks



tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

def tfstrip(x): return x.strip()

publisher = 'The Abdus Salam International Centre for Theoretical Physics'
jnl = 'arp'
vol = sys.argv[1]
year = sys.argv[2]

jnlfilename = jnl+vol
jnlname = 'Afr.Rev.Phys.'

urltrunk = 'http://www.aphysrev.org/index.php/aphysrev/issue/view' 


recs = []
recnr = 1
print "get table of content of %s%s ..." %(jnlname,vol)
os.system("lynx -source \"%s/%i/showToc\" > %s/%s.toc" % (urltrunk,int(vol)+21,tmpdir,jnlfilename))
    
tocfil = open("%s/%s.toc" % (tmpdir,jnlfilename),'r')
#for tline in  map(tfstrip,tocfil.readlines()):
tocline = re.sub('\s\s+',' ',' '.join(map(tfstrip,tocfil.readlines())))
for tline in re.split(' *<\/table> *',tocline):
    tline = removehtmlgesocks(re.sub('.*<table ','',tline))
    if re.search('tocArticle',tline):
        print tline
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['year'] = year
        rec['vol'] = vol
        rec['typ'] = ''
        rec['jnl'] = jnlname        
        rec['note'] = []
        rec['tc'] = "P"
        rec['tit'] = re.sub('.*?<td class=\"tocTitle\"> *(.*?) *<\/td>.*',r'\1',tline)
        for aut in re.split(' *, *',  re.sub('.*?<td class=\"tocAuthors\"> *(.*?) *<\/td>.*',r'\1',tline)):
            aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
            aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
            rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', aut))            
        rec['pdf'] = re.sub('.*?<a href=\"(.*?)\".*',r'\1',tline)+'.pdf'
        rec['p1'] = rec['p2'] = "%04i" % (recnr)
        print "%s%s (%s) %s" % (rec['jnl'],vol,year,rec['p1'])
        #write record
        recs.append(rec)
        recnr += 1


xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
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
