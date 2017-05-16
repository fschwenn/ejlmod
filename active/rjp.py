# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Romanian Journal of Physics
# FS 2014-11-14

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs



ejdir = '/afs/desy.de/user/l/library/dok/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


publisher = 'Romanian Academy Publishing House'
year = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]

jnl = 'rjp'
jnlname = 'Rom.J.Phys.'

jnlfilename = '%s%s.%s' % (jnl, vol, issue)
xmlf = os.path.join(xmldir,jnlfilename+'.xml')

url = 'http://www.nipne.ro/%s/%s_%s_%s.html' % (jnl, year, vol, issue)

print "get table of content of %s%s.%s ..." %(jnlname, vol, issue)
os.system("lynx -source \"%s\" > %s/%s.toc" % (url,tmpdir,jnlfilename))

print "read table of contents..."
tocfil = codecs.EncodedFile(open(tmpdir+"/"+jnlfilename+".toc",mode='rb'),"utf8")

lines = ''.join(map(tfstrip,tocfil.readlines()))

recs = []
note = ''
for part in re.split('<tr><td colspan="2">', lines):
    if re.search('class="tsection">', part):
        note = re.sub('.*class="tsection">(.*?)<.*', r'\1', part)
    if re.search('<span class="times">', part):
        rec = {'jnl' : jnlname, 'year' : year, 'vol' : vol, 'issue' : issue, 'tc' : 'P', 'auts' : []}
        if note != '':
            rec['note'] = [note]
        rec['p1'] = re.sub('.*<span class="times">(.*?)<.span.*', r'\1', part)
        rec['tit'] = re.sub('.*<span class="toct">(.*?)<.span.*', r'\1', part)
        authors = re.sub('.*<span class="toca">(.*?)<.span.*', r'\1', part)    
        for aut in re.split(', ', authors):
            rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', aut))
        if re.search('Full text', part):
            rec['FFT'] = 'http://www.nipne.ro/%s/%s' % (jnl, re.sub('.*href="(.*?)".*', r'\1', part))
            rec['pdf'] = rec['FFT'] 
        recs.append(rec)

xmlfile  = codecs.EncodedFile(open(xmlf,mode='wb'),"utf8")
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
