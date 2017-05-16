#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest ARMENIAN JOURNAL OF PHYSICS
# FS 2012-06-01

import os
import ejlmod2
import re
import sys
import unicodedata
import string



ejdir = '/afs/desy.de/user/l/library/dok/ejl'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'National Academy of Sciences of Armenia'
jnl = 'armjp'
vol = sys.argv[1]
#issue = sys.argv[2]
year = str(int(vol)+2007)

jnlfilename = jnl+vol
jnlname = 'Armenian J.Phys.'
issn = "1829-1171"

#urltrunk = 'http://www.flib.sci.am/eng/journal/Phys'
urltrunk = 'http://ajp.asj-oa.am'


recnr = 1
print "get table of content of %s%s ..." %(jnlname,vol)
#print "lynx -source \"%s/PV%sIss%s.html\" > %s/%s.toc" % (urltrunk,vol,issue,tmpdir,jnlfilename)
#os.system("lynx -source \"%s/PV%sIss%s.html\" > %s/%s.toc" % (urltrunk,vol,issue,tmpdir,jnlfilename))
tocfilname = "%s/%s.toc" % (tmpdir,jnlfilename)
if not os.path.isfile(tocfilname):
    os.system('lynx -source "%s/view/year/%s.html" > %s' % (urltrunk, year, tocfilname))
tocfil = open(tocfilname, 'r')
#for tline in  map(tfstrip,tocfil.readlines()):
tocline = re.sub('\s\s+',' ',' '.join(map(tfstrip,tocfil.readlines())))
recs = []
for tline in re.split(' *<p> *',tocline):
    if re.search('span class="person_name"',tline):
        #print tline
        if re.search('Letter of Radik Martirosyan', tline):
            continue
        rec = {}
        rec['auts'] = []
        rec['aff'] = []
        rec['year'] = year
        rec['vol'] = vol
        rec['typ'] = ''
        rec['jnl'] = jnlname        
        rec['note'] = []
        rec['tc'] = "P"
        rec['keyw'] = []
        rec['tit'] = re.sub('.*?<a href.*?> *(.*?)\.? *<\/a>.*',r'\1',tline)
        rec['tit'] = re.sub(' *<\/?em> *', '', rec['tit'])
        authors  = re.sub('.*?<span class="person_name">(.*)<\/span>.*',r'\1',tline)
        authors  = re.sub(' *and +','; ',authors)
        authors = re.sub('<.*?>', '', authors)
        #print rec,authors
        #authors = re.sub('(.*?), (.*?),',r'\1, \2;'.authors)
        for aut in re.split(' *; *', authors):
            aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
            aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
            #rec['auts'].append(re.sub('^(.*) (.*?)$', r'\2, \1', aut))            
            rec['auts'].append(aut)            
        if rec['auts'] == []: continue
        if re.search('<\/a>.*pp\.? *\d+ *\- *\d+',tline):
            rec['p1'] = re.sub('.*?<\/a>.*pp\.? *(\d+) *\- *(\d+).*',r'\1',tline)
            rec['p2'] = re.sub('.*?<\/a>.*pp\.? *(\d+) *\- *(\d+).*',r'\2',tline)
        else:
            rec['p1'] = rec['p2'] = re.sub('.*?<\/a>.*p\.? *(\d+).*',r'\1',tline)
        rec['issue'] = re.sub('.*Armenian Journal of Physics, \d+ \((\d+)\).*', r'\1', tline)
        link = re.sub('.*?<a href=\"(.*?)\".*',r'\1',tline)
        #more detais from abstract page
        print "%s%s (%s) %s" % (rec['jnl'],vol,year,rec['p1'])
        artfilname = tmpdir+"/"+jnlfilename+"."+rec['p1']
        if not os.path.isfile(artfilname):
            os.system("lynx -source \"%s\" > %s" %(link,artfilname))
        artfil = open(artfilname,'r')
        for aline in  map(tfstrip,artfil.readlines()):
            if re.search('<meta name="eprints.datestamp"', aline):
                rec['date'] = re.sub('.*content="(.*?) .*', r'\1', aline)
            if re.search('href.*\.pdf',aline):
                rec['FFT'] = re.sub('.*href=\"(.*?\.pdf)\".*',r'\1',aline)
                rec['link'] = link
            if re.search('<h2>Abstract.*<\/p>',aline):
                rec['abs'] = re.sub('.*<h2>Abstract.*?<p.*?> *(.*?) *<\/p>.*',r'\1',aline)
            if re.search('<meta name="DC.subject"', aline):
                rec['keyw'].append(re.sub('.*content="\d*\.(.*)".*', r'\1', aline))
            #if re.search('Subjects.*<\/a>',aline):
            #    subject = re.sub('.*Subjects.*?html\">(.*?)<\/a>.*',r'\1',aline)
            #    rec['note'].append(re.sub('Physics > \d*\.','',subject))
            if re.search('You seem to be attempting to access an item that has been removed from the repository',aline):
                rec['note'].append('item that has been removed')
            if re.search('creativecommons.org', aline):
                rec['licence'] = {'url' : re.sub('.*(http.*?)".*', r'\1', aline)}
        #write record
        print "REC",rec
        recs.append(rec)

xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = open(xmlf,'w')
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
