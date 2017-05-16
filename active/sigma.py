# -*- coding: utf-8 -*-
#program to harvest "Symmetry, Integrability and Geometry: Methods and Applications (SIGMA)"
# FS 2012-05-30

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

publisher = 'SIGMA'
year = sys.argv[1]
firstarticle = int(sys.argv[2])
jnl = 'SIGMA'
jnlfilename = 'sigma'+year+'_'+str(firstarticle)






print "get table of content..."
os.system("wget -q -O %s/%s.toc http://www.emis.de/journals/SIGMA/%s/" %(tmpdir,jnlfilename,year))
tocfil = open(tmpdir+"/"+jnlfilename+".toc",'r')
for line in  tocfil.readlines():
    if re.search('Volume',line):
        vol = re.sub('.*Volume (\d+).*',r'\1',line).strip()
    if re.search('SIGMA.*HREF',line):
        lastarticle = int(re.sub('.*HREF=\"(\d+).*',r'\1',line))
        break
tocfil.close()

recs = []
for i in range(firstarticle,lastarticle+1):
    rec = {}
    rec['typ'] = ''
    rec['jnl'] = jnl
    rec['vol'] = vol
    rec['year'] = year
    rec['tc'] = "P"
    rec['p1'] = rec['p2'] = rec['artnum'] = "%03i" %(i)
    auts = []
    affs = []
    print "get article %s%s (%s) %03i" %(jnl, vol, year, i)
    artfilename = "%s/%s.%03i" %(tmpdir,jnlfilename,i)
    if not os.path.isfile(artfilename):
        os.system("wget -q -O %s http://www.emis.de/journals/SIGMA/%s/%03i" %(artfilename,year,i))
    artfil = open(artfilename,'r')
    flautaff = False
    flabs = False
    flkw = False
    flref = False
    for line in map(tfstrip,artfil.readlines()):
        line = removehtmlgesocks(line)
        #informations in one line
        if re.search('http\:\/\/arxiv.org',line) and not flref:
            rec['arxiv'] = re.sub('.*arXiv\:(\d+\.\d+).*',r'\1',line)
            rec['pages'] = re.sub('.*, *(\d+) pages.*',r'\1',line)
        if re.search('http\:\/\/dx.doi.org',line) and not flref:
            rec['doi'] = re.sub('.*dx.doi.org\/(10.3842.SIGMA.*?)\".*',r'\1',line)
            doi1 = re.sub('(\(|\)|\/)','_',rec['doi'])
        elif re.search('^<H3>',line) and not  re.search('<A HREF',line):
            rec['tit'] = re.sub('<H3>(.*)<\/H3>',r'\1',line)
        elif re.search('<BIG>.*pdf',line):
            line = re.sub('.*HREF=\"(.*pdf)\".*',r'\1',line)
            rec['filename'] = "http://www.emis.de/journals/SIGMA/%s/%03i/%s" %(year,i,line)
            rec['pdf'] = rec['filename'] 
        elif re.search('<I>Contribution to.*Proceedings',line):
            rec['comments'] = [ "Conference: "+re.sub('.*\.\.\/(.*?)\.html.*',r'\1',line) ]
            rec['tc'] = "C"
        #informations spread over several lines (start/end marking)
        if re.search('<BLOCKQUOTE>',line): 
            flautaff = True
        elif re.search('(<\/BLOCKQUOTE>|<BIG>)',line): 
            flautaff = False
            rec['auts'] = auts
            rec['aff'] = affs
        if re.search('<B>Abstract',line):  
            flabs = True
            abs = ""
        elif re.search('<\/P>',line):  flabs = False
        if re.search('<B>Key words',line): 
            flkw = True
            kws = []
        if re.search('<B>References',line): 
            flref = True
            rec['refs'] = []
            refno = 0
            #reffile.write('add;\n DOI = '+rec['doi']+';\n')
            #reffile.write(' SOURCE = '+publisher+';\n')
        elif re.search('<\/OL>',line): 
            flref = False
            #reffile.write(';\n')
        #informations spread over several lines (getting informations)
        if flautaff:
            if re.search('<B>',line):
                line = re.sub('<\/?[PB]>', '', line)
                line = re.sub(' and ', ', ', line)
                line = re.sub('<SMALL><SUP>(\w+)<\/SUP><\/SMALL>', r', =Aff\1', line)
                line = re.sub('<SUP><SMALL>(\w+)<\/SMALL><\/SUP>', r', =Aff\1', line)
                for au in re.split(' *, *',line):
                    auts.append(re.sub('^(.*) (.*?)$', r'\2, \1', au))
            elif re.search('<I>',line):
                line = re.sub('<BR><SMALL><SUP>(\w+)\)<\/SUP> *<I> *', r'Aff\1= ', line)
                line = re.sub('<BR><SMALL><I> *', r'', line)
                line = re.sub('<\/I><\/SMALL>','',line)
                affs.append(line)
        elif flabs:
            abs += ' '+re.sub('(<P><B>Abstract<\/B>|<BR>)','',line)            
            rec['abs'] = re.sub(' +', ' ',re.sub('<\/?[IB]>','',abs))
        elif flkw:
            if re.search('<\/P>',line): flkw = False
            parts = re.split('; ', re.sub('(.*<\/B>|<\/?[PIB]>)','',line))
            for part in parts:
                if len(part)>1: kws.append(part)
            rec['keyw'] = kws
        elif flref:
            #line = re.sub('<A HREF=\"http\:\/\/arxiv.org.*?\">','',line)
            #line = re.sub('<\/?[ABI]>','',line)
            if re.search('^<LI>',line):
                refno += 1
                raffle = re.sub('<LI>','',line)
                iref = [('o', str(refno))]
            elif refno > 0:
                raffle += line
            if refno > 0 and re.search('<\/LI>',raffle):
                #print raffle
                if re.search('arxiv.org',raffle):
                    refbull = re.sub('.*arxiv.org.*?>(.*?)<.*',r'\1',raffle)
                    iref.append(('r', refbull))
                if re.search('dx.doi.org',raffle):
                    refdoi = re.sub('.*dx.doi.org\/(10.*?)\".*',r'\1',raffle)
                    raffle = re.sub('<A HREF.*?>','',raffle) # +' (doi: '+refdoi+')'
                    iref.append(('a', refdoi))
                raffle = re.sub(';',',',raffle)
                iref.append(('m', re.sub('.*?<LI>(.*?)<\/LI>.*',r'\1',raffle)))
                if len(iref) == 1:
                    iref = [('x', re.sub('.*?<LI>(.*?)<\/LI>.*',r'\1',raffle))]
                rec['refs'].append(iref)
    #write record
    print rec
    recs.append(rec)

                

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








