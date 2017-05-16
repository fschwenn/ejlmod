# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest International Press Boston
# FS 2012-06-01

import codecs
import os
import ejlmod2
import re
import sys
import unicodedata
import string
from removehtmlgesocks import removehtmlgesocks



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
printer = "l00ps5 "
def tfstrip(x): return x.strip()

publisher = 'International Press'
jnl = sys.argv[1]
vol = sys.argv[2]
isu = sys.argv[3]

jnlfilename = jnl+vol+'.'+isu


#issueflag: 0 = Homepage komplett harvesten; ansonsten 1 = gewuenschtes issue. -1 = ungewuenschtes issue
if   (jnl == 'atmp'): 
    jnlname = 'Adv.Theor.Math.Phys.'
    issn = '1095-0761'
    url = "http://www.intlpress.com/%s/%s-issue_%s_%s.php" % (jnl.upper(),jnl.upper(),vol,isu)
    issueflag = 0
elif (jnl == 'cntp'):
    jnlname = 'Commun.Num.Theor.Phys.'
    issn = '1931-4523'
    url = "http://www.intlpress.com/%s/%s-vol-%s.php" % (jnl.upper(),jnl.upper(),vol)
    issueflag = -1
elif (jnl == 'ajm'):
    jnlname = 'Asian J.Math.'
    issn = '1093-6106'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
    issueflag = -1
elif (jnl == 'jdg'):
    jnlname = 'J.Diff.Geom.'
    issn = '0022-040X'
    year = str(int(vol) / 3 + 1982)
    url = "http://www.intlpress.com/%s/%s/%s-v%s.php" % (jnl.upper(),year,jnl.upper(),vol)
    issueflag = 0
elif (jnl == 'cag'):
    jnlname = 'Commun.Anal.Geom.'
    issn = '1019-8385'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
    issueflag = 0
elif (jnl == 'cjm'): #fall 2012
    jnlname = 'Cambridge J.Math.'
    issn = '2168-0930'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
    issueflag = 0
elif (jnl == 'cms'):
    jnlname = 'Commun.Math.Sci.'
    issn = '1539-6746'
    year = str(int(vol)+2002)
    url = "http://www.intlpress.com/%s/%s/issue%s-%s" % (jnl.upper(),year,vol,isu)
    issueflag = 0
elif (jnl == 'jsg'):
    jnlname = 'J.Sympl.Geom.'
    issn = '1527-5256'
    url = "http://www.intlpress.com/%s/%s-v%s.php" % (jnl.upper(),jnl.upper(),vol)
    issueflag = 0
elif (jnl == 'mrl'): # fulltext via http://www.intlpress.com/_newsite/site/pub/files/_fulltext/journals/mrl/
    jnlname = 'Math.Res.Lett.'
    issn = '1073-2780'
    url = "http://www.intlpress.com/_newsite/site/pub/pages/journals/items/%s/content/vols/00%s/000%s/index.php" % (jnl,vol,isu)

if len(vol) == 1: vol = '0'+vol
url = "http://intlpress.com/site/pub/pages/journals/items/%s/content/vols/00%s/000%s/body.html" % (jnl,vol,isu)


recnr = 1
print "get table of content of %s%s.%s ..." %(jnlname,vol,isu)
print "lynx -source \"%s\"" % (url)
os.system("lynx -source \"%s\" > %s/%s.toc" % (url,tmpdir,jnlfilename))
tocfil = open("%s/%s.toc" % (tmpdir,jnlfilename),'r')
tocline = re.sub('  +',' ',' '.join(map(tfstrip,tocfil.readlines())))

recs = []
for tline in re.split(' *(<\/div>) *',tocline):    
    tline =re.sub('<\/em>','</i>', re.sub('<em>','<i>',tline))
    #print tline
    if re.search('topheadingblock',tline):
        year = re.sub('.*h2_pagehd_volume.*?\(\D*(2\d+)\).*',r'\1',tline)
        #if (issueflag != 0):
        #    if re.sub('.*Number (\d+) .*',r'\1',tline) == isu:
        #        issueflag = 1
        #    else:
        #        issueflag = -1
        print 'year=',year
    elif re.search('<H3>Volume',tline):
        year = re.sub('.*<H3>Volume.*?(20\d+).*',r'\1',tline)
    #elif (issueflag >= 0) and re.search('<div class="list_item">',tline):
    elif  re.search('<div class="list_item">',tline):
        #tline = removehtmlgesocks(tline)
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['year'] = year
        rec['vol'] = vol
        rec['typ'] = ''
        rec['jnl'] = jnlname
        rec['note'] = []
        rec['tc'] = "P"
        rec['tit'] = re.sub('.*<p> *(.*?) *<\/p>.*',r'\1',tline)
        rec['tit'] = re.sub('<sub>(.*?)<\/sub>',r'_\1',rec['tit'])
        rec['tit'] = re.sub('<sup>(.*?)<\/sup>',r'^\1',rec['tit'])
        link = re.sub('.*href=.*?site\/(.*)index.html.>.*',r'http://intlpress.com/site/\1body.html',tline)
        print link
        os.system("lynx -source \"%s\" > %s/%s.%i" % (link,tmpdir,jnlfilename,recnr))
        artfil = open("%s/%s.%i" % (tmpdir,jnlfilename, recnr),'r')
        artline = re.sub('  +',' ',' '.join(map(tfstrip,artfil.readlines())))
        artfil.close()
        affhash = {}
        for aline in re.split(' *(<\/div>) *',artline):
            if re.search('contentitem_doi',aline):
                doi = re.sub('.*dx.doi.org.*?(10.*?)<.*',r'\1',aline)
                rec['doi'] = re.sub('&#47;','/',doi)
            if re.search('contentitem_pages',aline):
                pages = re.sub('.*Pages.*?(\d.*?)<\/p>.*',r'\1',aline)
                rec['p1'] = re.sub('^(\d+)\D.*',r'\1',pages)
                rec['p2'] = re.sub('.*\D(\d+)',r'\1',pages)
                print '  %s %s (%s) %s%s%s' % (jnlname,vol,year,rec['p1'],'-',rec['p2'])
            if re.search('contentitem_authors',aline):
                #aline = removehtmlgesocks(aline)
                for part in re.split(' *<\/p> *',aline):
                    if re.search('contentitem_authors',part):
                        autaff = re.sub('.*contentitem_authors.> *','',part)
                        if re.search('\(',part):
                            aut = re.sub(' *\(.*','',autaff)
                            if not re.search(',',aut):
                                aut = re.sub('(.*) (.*)',r'\2, \1',aut)
                            affs = re.sub('.*?\(','',autaff)
                            rec['auts'].append(aut)
                            for aff in re.split(' *; *',affs):
                                if affhash.has_key(aff):
                                    rec['auts'].append('='+affhash[aff])
                                else:
                                    affnr = str(len(affhash)+1)
                                    rec['auts'].append('='+affnr)
                                    rec['aff'].append(affnr+'= '+aff)
                                    affhash[aff] = affnr
                        else:
                            rec['auts'].append(autaff)
            if re.search('contentitem_abstract',aline):
                rec['abs'] = re.sub('.*contentitem_abstract.> *(.*?)</p>.*',r'\1',aline)
            if re.search('contentitem_keywords',aline):
                rec['keyw'] = re.split(', ',re.sub('.*contentitem_keywords.> *(.*?)</p>.*',r'\1',aline))
            if re.search('>Full Text',aline):
                rec['pdf'] = re.sub('.*href.*?\/site(.*?pdf)" target.*',r'http://intlpress.com/site\1',aline)
                print recnr,rec        
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
