#!/usr/bin/python
#program to harvest CJP
# FS 2014-10-10

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
def tfstrip(x): return x.strip()

publisher = 'NRC Research Press'
jnl = sys.argv[1]
vol = sys.argv[2]
isu = sys.argv[3]

month = {'January' : 2, 'February' : 2, 'March' : 3, 'April' : 4, 'May' : 5, 'June' : 6, 'July' : 7, 'August' : 8, 'September' : 9, 'October' : 10, 'November' : 11, 'December' : 12}

if   (jnl == 'cjp'): 
    jnlname = 'Can.J.Phys.'
    issn = '0008-4204'

jnlfilename = jnl+vol+'.'+isu

urltrunk = 'http://www.nrcresearchpress.com'

print "get table of content of %s%s.%s ..." %(jnlname,vol,isu)
tocfilename = '/tmp/%s%s%s' % (jnl,vol,isu)
if not os.path.isfile(tocfilename):
    os.system('wget -O %s \"%s/toc/%s/%s/%s"' % (tocfilename,urltrunk,jnl,vol,isu))

tocfil = open(tocfilename,'r')
toccontent = ' '.join(map(tfstrip,tocfil.readlines()))
tocfil.close()
toccontent = re.sub('.*<h1>Table of Contents</h1>', '', toccontent )
toccontent = re.sub('10.1046/9999-9999.99999.*', '', toccontent )

note = ''
recs = []
for tline in re.split('<div class="articleGroup">', toccontent):
    if re.search('<div class="articleGroup">', tline):
        note = [ re.sub('.*<div class="articleGroup"><h2.*?>(.*?)<.*', r'\1', tline) ]
    for ttline in re.split('<div class="item clearfix">', tline):
        if re.search('href="/doi/abs.*Abstract', ttline):
            abslink = re.sub('.*href="(/doi/abs.*?)".*', r'\1', ttline)
            rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : isu, 'tc' : 'P'}
            #doi
            rec['doi']  = re.sub('.*abs/', '', abslink)
            #print '+++++++++++++++++++++++++++++++++++++++++++++++++'
            print rec['doi']
            #pages, year
            pbn = re.sub('.*<span class="italic">.*?</span>, *(.*?)<.*', r'\1', ttline)
            rec['year'] = re.sub(',.*', '', pbn)
            p1p2 = re.sub('.*: *(.*?),.*', r'\1', pbn)
            if p1p2 == pbn:
                rec['p1'] = '0'
                rec['p2'] = '0'
            else:
                if re.search('\-', p1p2):
                    [rec['p1'], rec['p2']] = re.split('\-', p1p2)
                else:
                    rec['p1'] = p1p2
                    rec['p2'] = p1p2
                    rec['pages'] = '1'
            artfilname = '/tmp/%s%s%s.%s' % (jnl, vol, isu, re.sub('/','_',rec['doi']))
            if not os.path.isfile(artfilname):
                os.system('wget -O %s \"%s%s"' % (artfilname, urltrunk, abslink))
            artfil = open(artfilname,'r')
            alines = artfil.readlines()
            for aline in alines:
                #title
                if re.search('<meta name="dc.Title" content="', aline):
                    rec['tit'] = re.sub('.*<meta name="dc.Title" content="(.*?)".*', r'\1', aline.strip())
                #PACS
                if re.search('<meta name="dc.Subject" content="', aline):
                    pacs = re.sub('.*<meta name="dc.Subject" content="(.*?)".*', r'\1', aline.strip())
                    rec['pacs'] = re.split('; *', pacs)
                #published
                if re.search('<meta name="dc.Date" scheme="WTN8601" content="', aline):
                    dates = re.split(' ', re.sub('.*<meta name="dc.Date" scheme="WTN8601" content="(.*?)".*', r'\1', aline.strip()))
                    rec['date'] = '%s-%02i-%02i' % (dates[2], month[dates[1]], int(dates[0]))
                #language
                if re.search('<meta name="dc.Language" content="', aline):
                    language = re.sub('.*<meta name="dc.Language" content="(.*?)".*', r'\1', aline.strip())
                    if language == 'fr':
                        rec['language'] = 'French'
                #abstract
                if re.search('<h2 id="absHdr">', aline):
                    rec['abs'] = re.sub('.*<h2 id="absHdr">.*?<p.*?>(.*?)<\/p>.*', r'\1', aline.strip())
                    if re.search('PACS Nos.: ', rec['abs']):
                        pacss = re.sub('.*PACS Nos.: *', '', rec['abs'])
                        rec['abs'] = re.sub('PACS Nos.*', '', rec['abs'])
                        rec['pacs'] = re.split(' *, *', pacss)                            
                #authors and affiliations
                if re.search('<p class="author">', aline):
                    rec['autaff'] = []
                    autaff = re.sub('.*<p class="author">(.*?)<p class="editor">.*', r'\1', aline.strip())
                    parts = re.split(' *<p class="fulltext affiliation"> *', autaff)
                    affdict = {}
                    #affiliations
                    for part in parts[1:]:
                        if part[:5] == '<sup>':
                            key = re.sub('^<sup>(.*?)<\/sup>.*', r'\1', part)
                        else:
                            key = '' 
                        aff = re.sub('<\/p>.*', '', part)
                        affdict[key] = re.sub('.*?<\/sup>', '', aff)
                    #authors
                    authors = re.sub('</?a.*?>', '', parts[0])
                    authors = re.sub('</sup><sup>', ',', authors)
                    for author in re.split(' *</sup> *', authors):
                        if len(author) > 4:
                            author = re.sub(' *</p>.*', '', author)
                            aparts = re.split(',?<sup>', author)
                            if len(aparts) > 1:
                                autplusaff = [re.sub('(.*) (.*)', r'\2, \1', aparts[0])]
                                for key in re.split(',', aparts[1]):
                                    if affdict.has_key(key):
                                        autplusaff.append(affdict[key])
                                rec['autaff'].append(autplusaff)                                    
                            else:
                                for apart in re.split(' *, *', author):
                                    autplusaff = [re.sub('(.*) (.*)', r'\2, \1', apart)]
                                    if affdict.has_key(''):
                                        autplusaff.append(affdict[''])
                                    rec['autaff'].append(autplusaff) 
            #references
            ablock = ''.join(alines)  
            if re.search('>References<', ablock):
                rec['refs'] = []
                ablock = re.sub('\n', '', ablock)
                ablock = re.sub('.*>References<', '', ablock)
                for ref in re.split('</li>', ablock):
                    if re.search('<span class="numbering">', ref):
                        iref = []
                        if re.search('>CrossRef<', ref):
                            doi = re.sub('.*key=(10.*?)".*>CrossRef<.*', r'\1', ref)
                            doi = re.sub('%2F', '/', doi)
                            iref.append(('a', doi))
                            number = re.sub('.*<span class="numbering"> *(.*?) *<.*', r'\1', ref)
                            iref.append(('o', number))
                        else:
                            text = re.sub('.*?<div.*?>(.*?)</div>.*', r'\1', ref)
                            text = re.sub('\r', '', text)
                            text = re.sub(' +', ' ', text)
                            text = re.sub('<.*?>', '', text)
                            iref.append(('x', text))
                        rec['refs'].append(iref)
            artfil.close()
            #write record
            recs.append(rec)

xmlf = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile = open(xmlf, 'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs ,xmlfile, publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml' + "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
