# -*- coding: utf-8 -*-
#program to harvest "GESJ: Physics "
# FS 2014-10-07

import os
import ejlmod2
import re
import sys
import codecs

from removehtmlgesocks import removehtmlgesocks

ejdir = '/afs/desy.de/user/l/library/dok/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

def tfstrip(x): return x.strip()

publisher = 'Internet Academy'
year = sys.argv[1]
issue = sys.argv[2]
jnl = 'GESJ Phys.'
jnlfilename = 'gesj'+year+'.'+issue






print "get table of content..."
if issue == '1':
    os.system("wget -q -O /tmp/gesj http://gesj.internet-academy.org.ge/en/list_artic_en.php\\?b_sec=phys\\&issue=%s-06" % (year))
else:
    os.system("wget -q -O /tmp/gesj http://gesj.internet-academy.org.ge/en/list_artic_en.php\\?b_sec=phys\\&issue=%s-12" % (year))




tocfil = open(tmpdir+"/gesj", 'r')
recs = []
toc = ''.join(map(tfstrip, tocfil.readlines()))
for record in  re.split('images.bul1.gif', toc)[1:]:
    record = re.sub('<hr.*', '', record)
    rec = {'jnl' : jnl, 'vol' : year, 'year' : year, 'issue' : issue, 'tc' : 'P'}
    #authors
    rec['auts'] = []
    for author in re.split('<script>', re.sub('.*?<script>(.*)<table.*',r'\1',record)):
        author = re.sub('.*a title=.(.*?)".*', r'\1', author)
        rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', author))
    #title
    title = re.sub('.*<strong>(.*?)</strong>.*spacer.gif.*',r'\1',record)
    if not re.search('[A-Z]', title):
        continue
    rec['tit'] = title.encode('utf8')
    #pages
    rest = re.sub('.*?spacer.gif', '', record)
    pages = re.sub('.*?<strong>(.*?)<\/strong>.*', r'\1', rest)
    [rec['p1'], rec['p2']] = re.split('\-', pages)
    #pdf
    rec['pdf'] = re.sub('.*<a href="(.*?)".*', r'\1', rest)
    #abstract
    abstractlink = 'http://gesj.internet-academy.org.ge/en/'+re.sub('.*"(v_abstr.*issue.*?)".*', r'\1', rest)
    os.system("wget -q -O /tmp/gesj%s%s%s '%s'" % (year, issue, rec['p1'], abstractlink))
    absfil = open('/tmp/gesj%s%s%s' % (year, issue, rec['p1']), 'r')
    abstract = re.sub('<br *\/?>', '', ''.join(map(tfstrip, absfil.readlines())))
    rec['abs'] = re.sub('.*?<div class="indent">(.*?)<\/div>.*',  r'\1', abstract)
    recs.append(rec)
    #print rec
tocfil.close()

                

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








