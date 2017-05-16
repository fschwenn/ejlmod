# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Romanian Reports in Physics
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

jnl = 'rrp'
jnlname = 'Rom.Rep.Phys.'

jnlfilename = '%s%s.%s' % (jnl, vol, issue)
xmlf = os.path.join(xmldir,jnlfilename+'.xml')

url = 'http://rrp.infim.ro/%s_%s_%s.html' % (year, vol, issue)

print "get table of content of %s%s.%s ..." %(jnlname, vol, issue)
os.system("lynx -source \"%s\" > %s/%s.toc" % (url,tmpdir,jnlfilename))

print "read table of contents..."
tocfil = codecs.EncodedFile(open(tmpdir+"/"+jnlfilename+".toc",mode='rb'),"utf8")

lines = ''.join(map(tfstrip,tocfil.readlines()))

recs = []
note = ''
for part in re.split('<TR.*?>', lines):
    if re.search('colspan=2.*<strong>', part):
        note = re.sub('.*<strong>(.*?)<.strong.*', r'\1', part)
    if re.search('<SPAN class=times>', part):
        rec = {'jnl' : jnlname, 'year' : year, 'vol' : vol, 'issue' : issue, 'tc' : 'P', 'auts' : []}
        if note != '':
            rec['note'] = [note]
        rec['p1'] = re.sub('.* class=times>(.*?)<.*', R'\1', part)
        if not rec['p1']:
            rec['p1'] = re.sub('.*TD>(.*?)<SPAN.*', R'\1', part)
        rec['tit'] = re.sub('.* class=tocTitle>(.*?)<.*', r'\1', part)
        authors = re.sub('.*class=tocAuth>(.*?)<.*', r'\1', part)    
        for aut in re.split(', ', authors):
            rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', aut))
    if re.search('Acrobat.*PDF', part):
        rec['FFT'] = 'http://rrp.infim.ro' + re.sub('.*HREF=".(.*?)".*', r'\1', part)
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
