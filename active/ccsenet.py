#!/usr/bin/python
#program to harvest CCSENET
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
tmpdir = '/tmp'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
def tfstrip(x): return x.strip()

publisher = 'Canadian Center of Science and Education'
jnl = sys.argv[1]
vol = sys.argv[2]
isu = sys.argv[3]


if   (jnl == 'apr'): 
    jnlname = 'Appl.Phys.Res.'
    issn = '1916-9639'
elif (jnl == 'jmr'):
    jnlname = 'J.Math.Res.'
    issn = '1916-9795'

jnlfilename = jnl+vol+'.'+isu

urltrunk = 'http://ccsenet.org/journal/index.php/%s' % (jnl)


recnr = 1
recs = []
print "get table of content of %s%s.%s ..." %(jnlname,vol,isu)
#toclink = os.popen("lynx -source \"%s/issue/archive\"|grep 'href.*Vol.* %s,.* %s'" % (urltrunk,vol,isu)).read().rstrip()
os.system('wget -O /tmp/%s%s%s \"%s/issue/archive\"' % (jnl,vol,isu,urltrunk))
toclink = os.popen("grep 'href.*Vol.* %s,.* %s' /tmp/%s%s%s" % (vol,isu,jnl,vol,isu)).read().rstrip()
print toclink
if re.search('Vol',toclink):
    year = re.sub('.*\((20\d+)\).*',r'\1',toclink)
    toclink = re.sub('.*href=\"(.*?)\">.*',r'\1',toclink)
    #os.system("lynx -source \"%s\" > %s/%s.toc" % (toclink,tmpdir,jnlfilename))
    os.system("wget -O   %s/%s.toc \"%s\" " % (tmpdir,jnlfilename,toclink))
else:
    print "Issue not yet online"
    #year = '2012'
    #toclink = "http://ccsenet.org/journal/index.php/apr/issue/view/665"
    #os.system("wget -O   %s/%s.toc \"%s\" " % (tmpdir,jnlfilename,toclink))
    sys.exit()


tocfil = open("%s/%s.toc" % (tmpdir,jnlfilename),'r')
for tline in  re.split('<.td>', ''.join(map(tfstrip,tocfil.readlines()))):
    #articles
    if re.search(' class=\"tocTitle\">',tline):
        tline = removehtmlgesocks(tline)
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['year'] = year
        rec['vol'] = vol
        rec['issue'] = isu
        rec['typ'] = ''
        rec['jnl'] = jnlname
        rec['note'] = []
        rec['tc'] = "P"
        rec['tit'] = re.sub('.*\">(.*)<\/a>.*',r'\1',tline)
        articlelink = re.sub('.*href=\"(.*?)\">.*',r'\1',tline)
    elif re.search(' class=\"tocPages\">',tline):
        rec['p1'] = re.sub('.* class=\"tocPages\">[pP](\d+)<.*',r'\1',tline)
        print "%s%s (%s) %s" % (jnlname,rec['vol'],year,rec['p1'])
        #more informations from article page
        artfilname = "%s/%s.%s" %(tmpdir,jnlfilename,rec['p1'])
        if not os.path.isfile(artfilname):
            #os.system("lynx -source \"%s\" > %s" %(articlelink,artfilname))
            os.system("wget -O %s \"%s\" " %(artfilname,articlelink))
        artfil = open(artfilname,'r')
        for aline in  map(tfstrip,artfil.readlines()):
            if re.search('<div id=\"authorString\">',aline):
                authors = re.sub('.*<div id=\"authorString\">(.*)<\/div>.*',r'\1',removehtmlgesocks(aline))
                authors = re.sub('<\/?em>','',authors)
                for aut in re.split(' *, *',authors):
                    #print ".",aut
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
                    rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', aut))
            elif re.search('href.*PDF',aline):
                rec['pdf'] = re.sub('.*href=\"(.*?)\".*',r'\1',aline)
            elif re.search('DC.Identifier.DOI',aline):
                rec['doi'] = re.sub('.*content=\"(10.*?)\".*',r'\1',aline)
                doi1 = re.sub('(\(|\)|\/)','_',rec['doi'])
            elif re.search('DC.Description',aline):
                rec['abs'] = re.sub('.*content=\" *(.*?) *\".*',r'\1',aline)
            elif re.search('DC.Language',aline):
                language = re.sub('.*content=\" *(.*?) *\".*',r'\1',aline)
                if not (language == 'en'):
                    if (language == 'fr'):
                        rec['tit'] += ' (In French)'
                    else:
                        rec['tit'] += ' (In %s???)' % language
        #write record
        recs.append(rec)
        recnr += 1

xmlf = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile = open(xmlf, 'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs ,xmlfile, publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename + "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
