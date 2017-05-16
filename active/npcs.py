# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest NONLINEAR PHENOMENA IN COMPLEX SYSTEMS
# FS 2013-01-28

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
from removehtmlgesocks import akzenteabstreifen
from removehtmlgesocks import removehtmlgesocks


ejdir = '/afs/desy.de/user/l/library/dok/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

def tfstrip(x): return x.strip()

publisher = 'Education and Upbringing'
jnl = 'npcs'
vol = sys.argv[1]
year = str(int(vol)+1997)
issue = sys.argv[2]

jnlfilename = jnl+vol+'.'+issue

issn = '1817-2458'
jnlname = 'Nonlin.Phenom.Complex Syst.'


urltrunk = "http://www.j-npcs.org/abstracts"



print "get table of content of %s%s.%s ..." %(jnlname,vol,issue)
#os.system("lynx -source \"%s.toc\"|grep 'href.* rel=.abstract' > %s/%s.toc" % (urltrunk,tmpdir,jnlfilename))
if not os.path.isfile(tmpdir+"/"+jnlfilename+".toc"):
    os.system("lynx -source \"%s/vol%sno%s.html\" > %s/%s.toc" % (urltrunk,year,issue,tmpdir,jnlfilename))

print "read table of contents..."
tocfil = open(tmpdir+"/"+jnlfilename+".toc",'r')
articleIDs = []


typecode = 'P'
note = ''
recnr = 1
recs = []
for line in  map(tfstrip,tocfil.readlines()):
    #print line
    if re.search('pp\. *\d',line):
        pages = re.sub('.*pp\. *([\d\-]+).*',r'\1',line)
    if re.search('HREF.*Abstract',line):
        url = re.sub('.*HREF=.*?(vol.*?html).*Abstract.*',r'\1',line)
        artfilname = "%s/%s.%s" %(tmpdir,jnlfilename,recnr)
        if not os.path.isfile(artfilname):
            print "lynx -source \"%s/%s\" > %s\n" %(urltrunk,url,artfilname)
            os.system("lynx -source \"%s/%s\" > %s" %(urltrunk,url,artfilname))
        artfil = open(artfilname,'r')
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['vol'] = vol
        rec['issue'] = issue
        rec['typ'] = ''
        rec['jnl'] = jnlname
        keywordline = ''
        #rec['pdf'] = urltrunk+'/'+articleID+'.pdf'
        #rec['filename'] = rec['pdf']
        rec['note'] = []
        if re.search('\-',pages):
            (rec['p1'],rec['p2'])  = re.split('\-',pages)
        else:
            rec['p1'] = rec['p2'] = pages
        rec['refs'] = []
        rec['tc'] = "P"
        rec['year'] = year
        flagabs = False
        flagkeyw = False
        title = ''
        for aline in  map(tfstrip,artfil.readlines()):
            #print aline
            #keywords 
            if flagkeyw:
                keywordline += ' '+re.sub('<\/P>.*','',aline)
            #title
            if re.search('<B>',aline):
                rec['tit'] = re.sub('.*<B> *','',removehtmlgesocks(akzenteabstreifen(aline)))
            elif rec.has_key('tit') and not re.search('<\/B>',rec['tit']):
                rec['tit'] +=  ' '+ re.sub('^ +','',removehtmlgesocks(akzenteabstreifen(aline)))
            #abstract-flags
            elif re.search('<P>',aline) and not rec.has_key('abs') and not flagabs and rec.has_key('tit'):
                flagabs = True
                rec['abs'] = re.sub('.*<P>','',removehtmlgesocks(akzenteabstreifen(aline)))
            elif flagabs:
                rec['abs'] += re.sub('<P>.*','',removehtmlgesocks(akzenteabstreifen(aline)))
                if re.search('[a-z].*<P>',aline) or re.search('^ *<BR> *$',aline):
                    flagabs = False
            #authors and affiliations
            elif re.search('<I>',aline) and not rec.has_key('abs') and rec.has_key('tit'):
                authors = re.sub('.*<I> *','',removehtmlgesocks(akzenteabstreifen(aline)))
                authors = re.sub('<\/I>.*','',authors)
                authors = re.sub(',? and ',', ',authors)
                for aut in re.split(' *, *',authors):
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
                    #print '  ',aut
                    rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', aut))
            #keywords
            elif rec.has_key('abs') and re.search('<I>Key words',aline):
                keywordline = ''
                flagkeyw = True
            elif flagkeyw and re.search('<\/P>',aline):
                flagkeyw = False
            #PDF:
            elif re.search('HREF.* PDF',aline):
                if re.search('.*HREF=.*?(cgi.*pdf).>.*',aline):
                    link = re.sub('.*HREF=.*?(cgi.*pdf).>.*',r'\1',aline)                
                    rec['pdf'] = 'http://www.j-npcs.org/'+link
                else:
                    link = re.sub('.*HREF=.*?(online.*pdf).>.*',r'\1',aline)                
                    rec['pdf'] = 'http://www.j-npcs.org/'+link
                #rec['FFT'] = rec['pdf']
                rec['filename'] = rec['pdf']
                doi1 = re.sub('.*\/(.*)\.pdf',r'\1',link)
        #write record        
        rec['tit'] = removehtmlgesocks(akzenteabstreifen(re.sub(' *<\/B> *','',rec['tit'])))
        rec['tit'] = re.sub('<br>','',rec['tit'])
        rec['tit'] = re.sub('\. *$','',rec['tit'])
        rec['tit'] = re.sub('<img.*?>','???',rec['tit'])
        rec['keyw'] = re.split(' *, *',re.sub('^ ','', removehtmlgesocks(akzenteabstreifen(keywordline))))
        print rec
        if rec.has_key('abs'):
            if len(rec['abs'])>5:
                rec['abs'] = re.sub('<sub>(.*?)<\/sub>',r'_\1',rec['abs'])
                rec['abs'] = re.sub('<sup>(.*?)<\/sup>',r'^\1',rec['abs'])
                rec['abs'] = re.sub('<sub>(.*?)<\/sub>',r'_\1',rec['abs'])
                rec['abs'] = re.sub('<em>(.*?)<\/em>',r'\1',rec['abs'])
                rec['abs'] = re.sub('<\/?[a-z].*?>','',rec['abs'])
                rec['abs'] = re.sub('<img.*?>','???',rec['abs'])
            elif rec.has_key('note'):
                rec['note'].append('record information might be incomplete')
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
