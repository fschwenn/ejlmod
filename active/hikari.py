#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Hikari Ltd.
# FS 2012-06-01

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
from removehtmlgesocks import removehtmlgesocks



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
absdir = '/afs/desy.de/group/library/abs'
tmpdir = '/tmp'
refdir = '/afs/desy.de/group/library/refs'
def tfstrip(x): return x.strip()

publisher = 'Hikari Ltd.'
jnl = sys.argv[1]
vol = sys.argv[2]
isu = sys.argv[3]

jnlfilename = jnl+vol+'.'+isu

if   (jnl == 'astp'):
    jnlname = 'Adv.Stud.Theor.Phys.'
    issn = '1313-1311'
    year = str(int(vol) + 2006)
    typecode = "P"
elif (jnl == 'aap'): 
    jnlname = 'Adv.Appl.Phys.'
    issn = ''
    year = str(int(vol) + 2012)
    typecode = "P"
elif (jnl == 'ces'):
    jnlname = 'Contemp.Eng.Sci.'
    issn = '1314-7641'
    year = str(int(vol) + 2007)
    typecode = "P"

urltrunk = 'http://www.m-hikari.com/%s/%s%s/%s%s-%s' % (jnl,jnl,year,jnl,isu,year)
print urltrunk



recnr = 1
print "get table of content of %s%s.%s ..." %(jnlname,vol,isu)
os.system("lynx -source \"%s/index.html\" > %s/%s.toc" % (urltrunk,tmpdir,jnlfilename))
    
recs = []
tocfil = open("%s/%s.toc" % (tmpdir,jnlfilename),'r')
#for tline in  map(tfstrip,tocfil.readlines()):
tocline = re.sub('  +',' ',' '.join(map(tfstrip,tocfil.readlines())))
for tline in re.split(' *<p> *',tocline):
    if re.search('href.*pdf',tline):
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['year'] = year
        rec['vol'] = vol
        rec['typ'] = ''
        rec['jnl'] = jnlname        
        rec['note'] = []
        rec['issue'] = isu
        rec['tc'] = typecode        
        parts = re.split(' *<br> *',tline)
        for aut in re.split(' *, *', parts[0]):
            aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
            aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
            rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', aut))            
        rec['tit'] = re.sub('.*?<a.*?> *(.*?) *<\/a>.*',r'\1',parts[1])
        rec['pdf'] = urltrunk+"/"+re.sub('.*?<a href=\"(.*?pdf)\".*',r'\1',parts[1])            
        rec['pdf'] = "http://www.m-hikari.com/"+re.sub('.*?<a href=\"(.*?pdf)\".*',r'\1',parts[1])            
        rec['licence'] = {'a' : 'CC-BY-4.0', 'u' : 'http://creativecommons.org/licenses/by/4.0/', 'b' : 'Hikari'}
        rec['FFT'] = rec['pdf']
        pages = re.sub('.*, *','',parts[2])
        if re.search('\-',pages):
            rec['p1'] = re.sub('(\d+) *\- *(\d+).*',r'\1',pages)
            rec['p2'] = re.sub('(\d+) *\- *(\d+).*',r'\2',pages)
        else:
            rec['p1'] = rec['p2'] =  re.sub('(\d+).*',r'\1',pages)
        print "%s%s (%s) %s-%s" % (rec['jnl'],vol,year,rec['p1'],rec['p2'])
        if len(parts) > 3 and re.search('http.*doi.org',parts[3]):
            rec['doi'] = re.sub('.*doi.org.(10.*?)".*',r'\1',parts[3])
            rec['doi'] = re.sub('<\/a>.*', '', rec['doi'])
        elif re.search('doi: 10.12988\/[a-z]+\.\d\d\d\d\.\d+', tline):
            rec['doi'] = re.sub('.*doi: (10.12988/.*?\.\d\d\d\d\.\d+).*', r'\1', tline.strip())
        else:
            rec['doi'] = '40.4000/%s%i' % (jnlfilename, recnr)
        recs.append(rec)
        recnr += 1


xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#xmlfile  = open(xmlf,'w')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()



