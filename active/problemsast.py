# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest PROBLEMS OF ATOMIC SCIENCE AND TECHNOLOGY
# FS 2012-06-01

import os
import ejlmod2
import codecs
import re
import sys
import unicodedata
import string
from removehtmlgesocks import removehtmlgesocks



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejdir = '/afs/desy.de/user/l/library/dok/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

def tfstrip(x): return x.strip()

publisher = 'Kharkov Institute of Physics and Technology'
year = sys.argv[1]
issue = sys.argv[2]

jnl = 'past'
jnlname = 'Prob.Atomic Sci.Technol.'
issn = '1562-6016'
jnlfilename = jnl+year+'.'+issue


urltrunk = 'http://vant.kipt.kharkov.ua'

recs = []
recnr = 1
print "get table of content ..."
#os.system("lynx -source \"%s/CONTENTS/CONTENTS_%s_%s.html\"  > %s/%s.toc" % (urltrunk,year,issue,tmpdir,jnlfilename))
os.system("lynx -dump \"%s/CONTENTS/CONTENTS_%s_%s.html\"  > %s/%s.toc" % (urltrunk,year,issue,tmpdir,jnlfilename))
    
tocfil = open("%s/%s.toc" % (tmpdir,jnlfilename),'r')

#tocline = re.sub('\s\s+',' ',' '.join(map(tfstrip,tocfil.readlines())))
#for tline in re.split(' *<tr> *',tocline):    
subject =  ''
for tline in  map(tfstrip,tocfil.readlines()):
    if re.search('^ *\([p@]',tline):
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['vol'] = year
        rec['issue'] = issue
        rec['typ'] = ''
        rec['jnl'] = jnlname        
        rec['note'] = []
        rec['year'] = year
        if subject != '': rec['note'].append(subject)
        rec['tc'] = 'P'
        rec['tit'] = ''
        pages = re.sub(' *\([p@]\. *(.*?)\).*',r'\1',tline)
        rec['p1'] = re.sub('^(\d+) *\- *(\d+)',r'\1',pages)
        rec['p2'] = re.sub('^(\d+) *\- *(\d+)',r'\2',pages)
        print "%s%s (%s) %s-%s" %(jnlname,rec['vol'],year,rec['p1'],rec['p2'])
        rec['pdf'] = "%s/ARTICLE/VANT_%s_%s/article_%s_%s_%s.pdf" % (urltrunk,year,issue,year,issue,rec['p1'])
        doi1 = "article_%s_%s_%s" % (year,issue,rec['p1'])
        link = "ANNOTAZII_%s/annotazii_%s_%s_%s.html" % (year,year,issue,rec['p1'])
        artfilname = tmpdir+"/"+jnlfilename+"."+str(recnr)
        if not os.path.isfile(artfilname):
            print "lynx -source \"%s/%s\" > %s" %(urltrunk,link,artfilname)
            #os.system("lynx -source \"%s/%s\" > %s" %(urltrunk,link,artfilname))
            os.system("lynx -dump \"%s/%s\" > %s" %(urltrunk,link,artfilname))
        artfil = open(artfilname,'r')
        #artline = re.sub('\s\s+',' ',' '.join(map(tfstrip,artfil.readlines())))
        #for aline in re.split(' *<tr> *',artline):
        flagaut = flagabs = flagaff = flagtit = False        
        affiliations =''
        abstract = ''
        for aline in map(tfstrip,artfil.readlines()):
            if re.search('^ *(\(Received |\**E.mail)',aline):
                aline = ''
                flagaff = False
                flagabs = True            
            if re.search('^ *PAST.*'+year,aline):
                flagtit = True
            elif flagtit and re.search('[A-Z][A-Z][A-Z]+',aline):
                if (len(re.sub('[A-Z ]','',aline)) / float(len(re.sub(' ','',aline))) < .3):
                    rec['tit'] += aline 
                #print "%6.3f %s" % ( len(re.sub('[A-Z ]','',aline)) / float(len(re.sub(' ','',aline))),aline)
            elif (rec['tit'] != '') and (rec['auts'] == []) and re.search('[a-z]',aline):
                flagaut = True
                flagtit = False
            if flagaff: 
                aline = re.sub(' *\^(\d+)', r';Aff\1=',aline)
                aline = re.sub(' *(\d)([A-Z])', r';Aff\1=\2',aline)
                affiliations += ' '+aline
                if re.search('^ *$',aline):
                    flagaff = False
                    flagabs = True            
            if flagaut:
                if not re.search(', *$',aline): 
                    flagaut = False
                    flagaff = True
                aline = re.sub('^ *','',aline)
                aline = re.sub('\*','',aline)
                #workaround to distingiush komma between authors and markers
                aline = re.sub(',(\d+)',r';\1',aline)
                aline = re.sub(',(\d+)',r';\1',aline)
                aline = re.sub(',(\d+)',r';\1',aline)
                aline = re.sub(',(\d+)',r';\1',aline)
                for aut in re.split(' *, *',aline):
                    if re.search('\d',aut):
                        marker = re.sub('.* *\^?(\d.*)',r'\1',aut)
                    else:
                        marker = ''
                    aut = re.sub(' *\^?\d.*', '', aut)
                    if (len(aut) > 2):
                        rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', aut))
                        if not (marker == ''):
                            for mark in re.split(' *; *',marker):
                                if mark != '':
                                    rec['auts'].append("=Aff"+mark)
            if flagabs and re.search('[a-z]',aline):
                if re.search('PACS\:',aline):
                    flagabs = False
                    rec['pacs'] = re.sub('.*PACS\: *(.*)',r'\1',aline)
                    rec['pacs'] = re.sub('\. ','.',rec['pacs'])
                    rec['pacs'] = re.sub('(\d\d)',r'\1.',rec['pacs'])
                    rec['pacs'] = re.sub('\.+','.',rec['pacs'])
                    rec['pacs'] = re.split(' *[;,]',rec['pacs'])
                else:
                    abstract += aline
            if flagabs and (len(abstract) > 5) and re.search('^ *$',aline):
                flagabs = False
        #write record
        rec['tit'] = re.sub('  +',' ',rec['tit'])
        rec['abs'] = re.sub('  +',' ',abstract)
        affiliations = re.sub('  +',' ',affiliations)
        for aff in re.split(' *; *',affiliations):
            if (len(aff) > 5):
                rec['aff'].append(re.sub('^ *','',aff))
        #print "REC",rec
        recnr += 1
        recs.append(rec)

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
