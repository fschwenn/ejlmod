#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Ukrainian Journal of Physics
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

publisher = 'National Academy of Sciences of Ukraine'
idnr = sys.argv[1]
jnl = 'ujp'
jnlfilename = jnl+idnr
jnlname = 'Ukr.J.Phys.'



urltrunk = 'http://ujp.bitp.kiev.ua'


recnr = 1
print "get table of content ..."
os.system("lynx -source \"%s/index.php?item=j&id=%s\"  > %s/%s.toc" % (urltrunk,idnr,tmpdir,jnlfilename))
    
tocfil = open("%s/%s.toc" % (tmpdir,jnlfilename),'r')
#for tline in  map(tfstrip,tocfil.readlines()):
tocline = re.sub('\s\s+',' ',' '.join(map(tfstrip,tocfil.readlines())))
subject = ''
recs = []
for tline in re.split(' *<hr.*?> *',tocline):    
    tline = removehtmlgesocks(tline)
    if re.search('href.*pdf',tline):
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['typ'] = ''
        rec['jnl'] = jnlname        
        rec['tc'] = 'P'
        rec['note'] = []
        if subject != '': rec['note'].append(subject)
        rec['pdf'] = urltrunk+re.sub('.*?<a href=\"(.*?pu?\.pdf)\">Paper.*',r'\1',tline)
        doi1 = re.sub('.*\/','',rec['pdf'])
        rec['tit'] = re.sub('.*?<div class=\"p_t\"> *(.*?) *<\/div>.*',r'\1',tline)
        #rec['tit'] = re.sub('.*?<div class=\"citation_title\"> *(.*?) *<\/div>.*',r'\1',tline)
        rec['tit'] = re.sub('<SUB>(.*?)<\/SUB>',r'_\1',rec['tit'])
        rec['tit'] = re.sub('<SUP>(.*?)<\/SUP>',r'_\1',rec['tit'])
        rec['tit'] = re.sub('<\/?I>','',rec['tit'])
        authors = re.sub('.*?<div class=\"p_a\"> *(.*?) *<\/div>.*',r'\1',tline)
        #authors = re.sub('.*?<div class=\"citation_author\"> *(.*?) *<\/div>.*',r'\1',tline)
        pbn = re.sub('.*?<div class=\"ref\"> *(.*?) *<\/div>.*',r'\1',tline)
        rec['year'] = re.sub('.*?(2\d+).*',r'\1',pbn)
        rec['vol'] = re.sub('.* Vol\. *(\d+).*',r'\1',pbn)
        rec['iss'] = re.sub('.* Vol\. *\d+, N *(\d+).*',r'\1',pbn)
        rec['p1'] = re.sub('.*, *p\. *(\d+) *\- *(\d+)',r'\1',pbn)
        rec['p2'] = re.sub('.*, *p\. *(\d+) *\- *(\d+)',r'\2',pbn)
        print "%s%s (%s) %s-%s" %(jnlname,rec['vol'],rec['year'],rec['p1'],rec['p2'])
        for aut in re.split(' *, *',authors):
            rec['auts'].append(re.sub('^(.*) (.*?)$', r'\1, \2', aut))
        #write record
        print "REC",rec
        if len(rec['auts']) > 0 and len(rec['auts'][0]) > 0:
            recs.append(rec)
        recnr += 1
    if re.search('<div class=\"ss\">',tline):
        subject = re.sub('.*<div class=\"ss\"> *(.*?)( |&nbsp;)*\/.*',r'\1',tline)


xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#xmlfile  = open(xmlf,'w')
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


