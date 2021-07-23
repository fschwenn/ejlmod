#program to harvest "Revista Mexicana de Fisica"
# -*- coding: UTF-8 -*-
## FS 2012-05-30

import os
import ejlmod2
import codecs
import re
import sys
from removehtmlgesocks import removehtmlgesocks

tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

def tfstrip(x): return x.strip()

publisher = 'Sociedad Mexicana de Fisica'
volume = sys.argv[1]
issue = sys.argv[2]
jnl = 'Rev.Mex.Fis.'
jnlfilename = 'rmf'+volume+'.'+issue

if volume[0] == 'E':
    urltrunc = 'http://rmf.smf.mx/page/rmf-e_anteriores?volume='
    #more metadate on http://www.scielo.org.mx/scielo.php?script=sci_issues&pid=1870-3542&lng=es&nrm=iso
elif volume[0] == 'S':
    urltrunc = 'http://rmf.smf.mx/page/rmf-s_anteriores?volume='
else:
    urltrunc = 'http://rmf.smf.mx/page/rmf_anteriores?volume='


print "get table of content..."
os.system("wget -q -O %s/%s.toc '%s%s&issue=%s'" %(tmpdir,jnlfilename,urltrunc,re.sub('[ES]', '', volume),issue))
fil = open(tmpdir+"/"+jnlfilename+".toc",'r')
active = False
i = 0
recs = []
for line in  fil.readlines():
    if re.search('<\/dl>',line):
        active = False
    elif active:
        if re.search('<dt>',line):
            title = re.sub('.*<dt> *(.*) *<\/dt>.*',r'\1',removehtmlgesocks(line.strip()))
            title = re.sub('<sup>(.*?)<\/sup>',r'^\1',title)
            title = re.sub('<sub>(.*?)<\/sub>',r'_\1',title)
        elif re.search('<dd>',line):
            auts = []
            for aut in re.split(', +',re.sub('.*<dd> *(.*) *,?<br.*',r'\1',removehtmlgesocks(line.strip()))):
                aut = re.sub(',', '', aut)
                auts.append(re.sub('([A-Z])\. ',r'\1.',re.sub('(.*[A-Z]\.) ([A-Z].*)',r'\2, \1',aut)))
        elif re.search('href=',line):
            i += 1
            rec = {'vol' : volume, 'issue' : issue, 'jnl' : jnl, 'tc' : 'P'}
            yearpage = re.sub('.*b> *\((\d*\) \d+).*',r'\1',line.strip())
            try:
                (rec['year'],rec['p1']) = re.split('\) ',yearpage)
            except:
                continue
            rec['tit'] = title
            rec['link'] = re.sub('.*href=.(.*?pdf).>.*','http://rmf.smf.mx'+r'\1',line.strip())
            rec['FFT'] = re.sub('.*href=.(.*?pdf).>.*','http://rmf.smf.mx'+r'\1',line.strip())
            rec['auts'] = auts
            rec['licence'] = {'statement' : 'CC-BY-NC'}
            print rec
            recs.append(rec)
    elif re.search('<h2>Contenido',line):
        active = True

fil.close()



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












