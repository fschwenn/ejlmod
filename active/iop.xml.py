z# -*- coding: UTF-8 -*-
# converts IOP xml files into dok format

import os
import sys
import xml.dom.minidom
import xml.sax
myParser = xml.sax.make_parser()
import urllib
#import Recode
#reload(ejlmod)
import ejlmod2
import re
import time
import codecs
from shutil import copyfile 
from bs4 import BeautifulSoup
import urllib2
import urlparse

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
lproc = '/afs/desy.de/user/l/library/proc'
publisher = 'IOP'

try:
    iopf = "iop" + sys.argv[1]
    print sys.argv[1]
except:
    iopf = 'iop' + str(time.localtime().tm_yday)

regexpiopurl = re.compile('http...iopscience.iop.org.')
regexpdxdoi = re.compile('http...dx.doi.org.')

file = "/afs/desy.de/group/library/publisherdata/iop/alert.stacks2_" + sys.argv[1]
#xmlfile = open(os.path.join(xmldir,'TEST-FS-'+iopf+'.xml'), 'w')

collapseWs = re.compile('[\n \t]+')
#initialBlank = re.compile('([A-Z]) ')
initialEnd = re.compile(r'([A-Z])\b')

#INSPIRE convention instead of DPBN as in springer.py
jnl = {'1538-3881': 'Astron.J.',
      '0004-637X': 'Astrophys.J.',
      '1538-4357': 'Astrophys.J.',
      '2041-8205': 'Astrophys.J.',
      '0067-0049': 'Astrophys.J.Supp.',
      '0264-9381': 'Class.Quant.Grav.',
      '1009-9271': 'Chin.J.Astron.Astrophys.',
      '1009-1963': 'Chin.Phys.',
      '1674-1056': 'Chin.Phys.',
      '1674-1137': 'Chin.Phys.',
      '0256-307X': 'Chin.Phys.Lett.',
      '0253-6102': 'Commun.Theor.Phys.',
      '0143-0807': 'Eur.J.Phys.',
#      '0295-5075': 'Europhys.Lett.',
      '0295-5075': 'EPL',
      '1751-8121': 'J.Phys.',
      '1742-6596': 'J.Phys.Conf.Ser.',
      '0954-3899': 'J.Phys.',
      '1475-7516': 'JCAP ',
      '1126-6708': 'JHEP ',
      '1748-0221': 'JINST ',
      '1742-5468': 'JSTAT ',
      '0957-0233': 'Measur.Sci.Tech.',
      '1367-2630': 'New J.Phys.',
      '0031-9120': 'Phys.Educ.',
      '1063-7869': 'Phys.Usp.',
      '0034-4885': 'Rep.Prog.Phys.',
      '1674-4527': 'Res.Astron.Astrophys.',
      '1402-4896': 'Phys.Scripta',
      '2399-6528': 'J.Phys.Comm.',
}

cnumdict = {'12th Workshop on Resistive Plate Chambers and Related Detectors (RPC2014)': 'C14-02-23.2',
            '12th Workshop on Resistive Plate Chambers and Related Detectors': 'C14-02-23.2',
            'International Conference on Instrumentation for Colliding Beam Physics (INSTR14)': 'C14-02-24',
            'Topical Workshop on Electronics for Particle Physics 2013 (TWEPP-13)': 'C13-09-23',
            '13th Topical Seminar on Innovative Particle and Radiation Detectors (IPRD13)': 'C13-10-07',
            'Precision Astronomy with Fully Depleted CCDS (PACCD2013)': 'C13-11-18.1',
            '10th International Conference on Position Sensitive Detectors (PSD10)': 'C14-09-07',
            '10th International Conference on Position Sensitive Detectors': 'C14-09-07',
            'Workshop on Intelligent Trackers (WIT2014)': 'C14-05-14',
            'TWEPP2014': 'C14-09-22.7',
            '7th International Workshop on Semiconductor Pixel Detectors for Particles and Imaging': 'C14-09-01.3',
            '16th International Workshop on Radiation Imaging Detectors': 'C14-06-22.3',
            'Precision Astronomy with Fully Depleted CCDS(2014)': 'C14-12-04.1',
            '2nd International Summer School on Intelligent Signal Processing for Frontier Research and Industry': 'C14-07-15',
            '17th International Workshop on Radiation Imaging Detectors': 'C15-06-28.1',
            'Light Detection in Noble Elements (LIDINE 2015)': 'C15-08-28',
            '13th Workshop on Resistive Plate Chambers and Related Detectors (RPC2016)': 'C16-02-22.3',
            '17th International Symposium on Laser-Aided Plasma Diagnostics (LAPD17)' : 'C15-09-27.1',
            'TWEPP2015': 'C15-09-28',
            'International Workshop on Fast Cherenkov Detectors - Photon detection, DIRC design and DAQ (DIRC2015)' : 'C15-11-11.2',
            '4th International Conference Frontiers in Diagnostics Fix Technologies (ICFDT4)': 'C16-03-30.5',
            '18th International Workshop on Radiation Imaging Detectors (IWORID2016)' : 'C16-07-03.1',
            '14th Topical Seminar on Innovative Particle and Radiation Detectors' : 'C16-10-03',
            'International Workshop on Semiconductor Pixel Detectors for Particles and Imaging (Pixel 2016)' : 'C16-09-05.3',
            '14th Topical Seminar on Innovative Particle and Radiation Detectors (IPRD16)' : 'C16-10-03',
            'Topical Workshop on Electronics for Particle Physics (TWEPP2016)' : 'C16-09-26.4',
            'International Conference on Instrumentation for Colliding Beam Physics (INSTR17)' : 'C17-02-27'}



#tocxml = xml.dom.minidom.parse(file)
print file
tocxml = xml.dom.minidom.parse(file,myParser)
recs = {}                         # dictionary of all records, key: pubnote
nr = 1
refprog = 'python ' + os.path.join(lproc,"Ejl/ref.iop.py")

def getAllText(anynode):
    text = []
    def recursive(n):
        if  n.parentNode.tagName in ('SUB', 'SUP'):
            try:
                text.append('(' + n.data + ')')
            except: pass
        else:
            text.append((n.nodeType == n.TEXT_NODE and n.data) or "")
        try:
            text.append((n.tagName == 'IMG'  and n.attributes['ALT'].value) or "")
        except: pass
        for c in n.childNodes: recursive(c)
    recursive(anynode)
#    texts = ''.join(text)
    texts = ''.join(text)
#    texts = collapseWs.sub(' ', texts)
    return texts

        
for node in tocxml.getElementsByTagName('stk_header'):
    rec = {'note' : []}
    tit = ''
    issn = node.getElementsByTagName('issn')[0].firstChild.data
    if jnl.has_key(issn):
        rec['jnl'] = jnl[issn]
        if issn in ['1742-6596']:
            tc = ['C']
        else:
            tc = ['P']
    else:
        print 'unknown ISSN:', issn
        

    for attrnode in node.getElementsByTagName('attributes'):
        art_type = attrnode.attributes['art_type'].value
        if art_type == 'rev': tc = ['R']
        elif art_type == 'misc': tc = ['']
    for focusnode in node.getElementsByTagName('art_focus'):
        if focusnode.attributes['alt'].value == 'Proceeding Article':
            tc = ['C']
        try:
            rec['note'].append(focusnode.attributes['alt'].value)
        except:
            pass
        try:
            comm = focusnode.attributes['group'].value
            rec['comments'] = [comm]
            if comm in cnumdict.keys():
                rec['cnum'] = cnumdict[comm]
        except:
            pass
    try:
        rec['vol'] = node.getElementsByTagName('volume')[0].firstChild.data
        if issn == '1674-1056':
            rec['vol'] = 'B'+rec['vol']
        elif issn == '1674-1137':
            rec['vol'] = 'C'+rec['vol']
        elif issn == '1751-8121':
            rec['vol'] = 'A'+rec['vol']
        elif issn == '0954-3899':
            rec['vol'] = 'G'+rec['vol']
    except:
        pass
    try:
        issue = node.getElementsByTagName('issue')[0].firstChild.data
        if issn == '1402-4896' and issue[0] == 'T':
            rec['vol'] = issue
        else:
            rec['issue'] = issue
            if issue.startswith("S"): #we have a supplememnt 
                rec['jnl'] += " Suppl."             
    except:
        pass

    datecover = node.getElementsByTagName('date_cover')[0].firstChild.data
    rec['year'] = datecover[0:4]
    try:
        if rec['jnl'] in ['JCAP ', 'JHEP ', 'JSTAT ']:
            rec['vol'] = datecover[2:4] + datecover[5:7]
    except: pass

    try:
        rec['artnum'] = node.getElementsByTagName('artnum')[0].firstChild.data
        if issn == '1748-0221' and rec['artnum'][0] == 'C':
            rec['tc'] = ['C']
    except:
        pass
    rec['doi'] = node.getElementsByTagName('doi')[0].firstChild.data

    pag = node.getElementsByTagName('pages')[0]
    try:
        rec['pages'] = pag.attributes['extent'].value
    except:
        pass
    rec['p1'] = pag.attributes['start'].value
    try:
        rec['p2'] = pag.attributes['end'].value
    except KeyError: pass

    for idnode in node.getElementsByTagName('external_id'):
        try:
            idnode.attributes['type'].value == 'arxive'
            rec['arxiv'] = idnode.firstChild.data.split('v')[0]
            print rec['arxiv']
        except:
            pass
    
    for datenode in node.getElementsByTagName('date_online'):
        try:
            rec['date'] = datenode.attributes['fulltext'].value 
        except:
            rec['date'] = datenode.attributes['header'].value 
    
    rec['tit'] = ''
    for tnode in node.getElementsByTagName('title_full'):
        for c in tnode.childNodes:
            if c.nodeName == 'footnote':
                footnote = tnode.removeChild(c)
                try:
                    rec['note'].append(footnote.firstChild.data)
                except:
                    pass
        rec['tit'] += getAllText(tnode)
    rec['tit']  = rec['tit'] 
    rec['tit']  = collapseWs.sub(' ', rec['tit'])
    rec['typ'] = ''

    authors = []
    afid = ''
    kwd_list = []
    for kwds in node.getElementsByTagName('subjects'):
        for kwd in kwds.getElementsByTagName('kwd_main'):
            try:
                kwd_list.append(kwd.firstChild.data)
            except:
                pass
            
    if kwd_list != []: rec["keyw"] = kwd_list   
    
    for au in node.getElementsByTagName('author_granular'):
        nlfname = ''
        nllname = ''
        try:
            #rec['col'] = au.getElementsByTagName('group')[0].firstChild.data
            rec['col'] = getAllText(au.getElementsByTagName('group')[0])
            continue
        except:
            try:
                #rec['col'] = au.getElementsByTagName('group')[0].firstChild.firstChild.data
                rec['col'] = getAllText(au.getElementsByTagName('group')[0].firstChild)
                continue
            except:
                pass
        try:
            fname = au.getElementsByTagName('given')[0].firstChild.data
            #fname = fname.encode('utf8..spidoc', 'replace')
            fname = initialEnd.sub(r'\1.',fname)
            fname = fname.replace('. ', '.')
            fname = fname.replace('..', '.')
            if 'non_latin' in au.getElementsByTagName('given')[0].attributes.keys():
                nlfname = au.getElementsByTagName('given')[0].attributes['non_latin'].value
        except:
            fname = ''
        try:
            lname = getAllText(au.getElementsByTagName('surname')[0])            
            if 'non_latin' in au.getElementsByTagName('surname')[0].attributes.keys():
                nllname = au.getElementsByTagName('surname')[0].attributes['non_latin'].value
#        lname = au.getElementsByTagName('surname')[0].firstChild.data
            #lname = lname.encode('utf8..spidoc', 'replace')
        except: 
            continue
        afido = afid
        try:
            afid = au.attributes["affil"].value
            afid = afid.replace(',','; =')
        except:
            afid = ''
        if (afid != afido) and afido:
            authors.append('=' + afido)           
        
        if 'orcid' in au.attributes.keys():
            orcid = 'ORCID:'+au.attributes['orcid'].value
            finalauthor = lname + ', ' + fname +  ', ' + orcid
        else:
            finalauthor = lname + ', ' + fname
        if nllname + nlfname != '':
            finalauthor += ', CHINESENAME: ' + nllname + ' ' +  nlfname
        authors.append(finalauthor)

#    if afid and afido:
    if afid:
        authors.append('=' + afid)
    rec['auts'] = authors
    afido = afid = ''

    if not node.getElementsByTagName('author_granular'):
        for au in node.getElementsByTagName('author'):
            try:
                aut = getAllText(au)
#                aut = au.firstChild.data
            except AttributeError:
                continue
            if 'Collaboration' in aut:
                rec['col'] = aut
                continue
            blank = aut.rfind(' ')
            if blank > 0:
                fname = aut[:blank].replace('. ', '.')
                fname = initialEnd.sub(r'\1.',fname).replace('..', '.')
                lname = aut[blank+1:]
                authors.append(lname + ', ' + fname)
            else:
                authors.append(aut)
            try:
                afid = au.attributes["affil"].value
                afid = afid.replace(',','; =')
                authors.append('=' + afid)
            except:
                pass
        rec['auts'] = authors
        
    rec['aff'] = []
    affid = ''
    for afnode in node.getElementsByTagName('affil'):
        try:
            affid = afnode.attributes["id"].value
        except:
            pass
        orgname = ''
        for orgnode in afnode.childNodes:
            if orgnode.nodeType == orgnode.TEXT_NODE:
                orgname += orgnode.data
#            orgname = afnode.firstChild.data
        orgname = orgname.replace('\n', ' ')
        orgname = orgname.replace('University', 'U.')
        orgname = orgname.replace(',', ' -')
        if affid:
            orgname = affid + "= " + orgname
        rec['aff'].append(orgname)
        affid = ''
#        except AttributeError:
#            pass
    for oanode in node.getElementsByTagName('open_access'):
        rec['licence'] = {
            'url' : oanode.attributes['url'].value,
            'statement' : oanode.attributes['license_type'].value}
        if issn in ['XXX1742-6596', 'XXX1367-2630']:
            rec['FFT'] = 'http://iopscience.iop.org/%s/pdf/%s.pdf' % (rec['doi'][8:], re.sub('\/', '_', rec['doi'][8:]))
            rec['FFT'] = 'http://iopscience.iop.org/article/%s/pdf' % (rec['doi'])
    rec['tc'] = tc
    abstxt = ''
    #references
    refurl = "http://iopscience.iop.org/article/%s/meta" % (rec['doi'])
    print '  lynx %s' % (refurl)
    try:
        page = BeautifulSoup(urllib2.urlopen(refurl))
        time.sleep(11)
        #get rid of footnotes
        for ul in page.body.find_all('ul', attrs = {'class' : 'clear-list wd-content-footnotes'}):
            ul.replace_with('')
        rec['refs'] = []
        for li in page.body.find_all('li', attrs = {'class' : 'indices-list'}):
            for a in li.find_all('a',  attrs = {'class' : 'indices-id'}):
                nummer = a.text
                a.replace_with(nummer + ' ')
            for a in li.find_all('a',  attrs = {'title' : 'CrossRef'}):
                if a.has_attr('href'):
                    doi = regexpdxdoi.sub(', DOI: ', a['href'])
                    a.replace_with(doi)
            for a in li.find_all('a',  attrs = {'title' : 'IOPScience'}):
                if a.has_attr('href'):
                    doi = regexpiopurl.sub(', DOI: 10.1088/', a['href'])
                    a.replace_with(doi)
            for a in li.find_all('a',  attrs = {'title' : 'IOPscience'}):
                if a.has_attr('href'):
                    doi = regexpiopurl.sub(', DOI: 10.1088/', a['href'])
                    a.replace_with(doi)
            for a in li.find_all('a'):
                if a.has_attr('href'):
                    link = ', %s: %s' % (a.text, a['href'])
                    a.replace_with(link)
            ref = li.text
            if regexpdxdoi.search(ref):
                ref = regexpdxdoi.sub('DOI: ', ref)
            if regexpiopurl.search(ref):
                ref = regexpiopurl.sub('DOI: 10.1088/', ref)
            rec['refs'].append([('x', ref)])
    except:
        print 'no references'

    for absnode in node.getElementsByTagName('header_text'):
        try:
            if absnode.attributes['heading'].value.upper() == 'ABSTRACT':
                abstxt = getAllText(absnode).encode('utf8')
                abstxt = collapseWs.sub(' ', abstxt)
        except KeyError: pass

        abstxt = abstxt.replace(';', ',')
        rec['abs'] = abstxt.replace('"', "'")
        try:            
            rec["pbn"] = rec['jnl'] + rec['vol'] + rec['p1']
            recs[nr] = rec
            nr+=1
        except:
            pass
        #print rec

    orgname = ''

# FS brand neu (2014-07-18), schlampig geschrieben und nur duerftig  gecheckt!
    #refprog = 'python ' + os.path.join(lproc,"Ejl/ref.iop.py") + ' "' + str(rec["doi"]) + '"'
    #os.system(refprog)    #  extract and write refs (subscribed jnls)
    refprog += ' "' + str(rec["doi"]) + '"'

def sort_iop(recs):
    """iop records unsorted in xml. sort them by the pbn"""
    recs_sorted = []
    sorted_list = sorted(recs.iteritems(), key=lambda x:x[1]["pbn"]) 
    for entry in sorted_list: 
        recs_sorted.append(recs[entry[0]])
    return recs_sorted


xmlf = os.path.join(xmldir,iopf+'.xml')
#xmlfile = open(xmlf, 'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(sort_iop(recs) ,xmlfile,'IOP')
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = iopf+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()

#print "---REFERENCES---"
#print refprog
#os.system(refprog)    #  extract and write refs (subscribed jnls)

