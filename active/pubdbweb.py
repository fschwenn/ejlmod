#!/usr/bin/python
# -*- coding: UTF-8 -*-
#bib-pubdbvm1
#pubdbvm1
from afftranslator2 import *

import ejlmod2

import unicodedata
import codecs
import re
import time
import datetime
import os
import sys
import urllib2
import urllib
import urlparse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

chunksize = 80
rpp = 25
#to avoid "too many results" split the timespan of the search
maxtimespan = 5 * 999

confdict = {'12th International Conference on Elastic and Diffractive Scattering Forward Physics and QCD' : 'C07-05-21.2',
            '12th International Conference on Elastic and Diffractive Scattering: Forward Physics and QCD' : 'C07-05-21.2',
            '38th International Symposium on Multiparticle Dynamics' : 'C08-09-15.2',
            '38th International Symposium on Multiparticle Dynamics ' : 'C08-09-15.2',
            'Magellan Workshop' : 'C16-03-17',
            '7th International Particle Accelerator Conference, Busan, 2016-05-08 - 2016-05-13' : 'C16-05-08'}


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
publisher = 'Deutsches Elektronen-Synchrotron'

now = datetime.datetime.now()


#look for conference in INSPIRE
def inspireconf(confsearch):
    notes = []
    searchurl = 'http://old.inspirehep.net/search?ln=en&cc=Conferences&ln=en&cc=Conferences&p=' + confsearch + '&action_search=Search&sf=conferencestartdate&so=d&rm=&rg=25&sc=0&of=xm'
    print searchurl
    try:
        inspirexml = urllib2.urlopen(searchurl).read()
        conferences = ET.fromstring(inspirexml)
    except:
        conferences = ET.fromstring('<mist></mist>')
        print '!'
    for record in conferences.findall('{http://www.loc.gov/MARC21/slim}record'):
        note = ''
        for entry in record.findall('{http://www.loc.gov/MARC21/slim}datafield'):
            if entry.attrib['tag'] == '111':                
                for subentry in entry:
                    if subentry.attrib['code'] == 'g':
                        note += '3c: %s ?' % (subentry.text)
                for subentry in entry:
                    if subentry.attrib['code'] == 'a':
                        note += ' (%s)' % (subentry.text)                        
        try:
            note.encode('ascii')
            notes.append(note)
        except:
            print note
    print confsearch
    print notes
    return notes
        
    

#harvest pubdb for new records with DESY-DOI
def requestarticles(timespan):
    numoftimespans = (timespan-1) / maxtimespan + 1
    pages = []
    for i in range(numoftimespans):
        if i == numoftimespans-1:
            startdate = now + datetime.timedelta(days=-timespan)
        else:
            startdate = now + datetime.timedelta(days=-(i+1)*maxtimespan)
        stopdate = now + datetime.timedelta(days=-i*maxtimespan)                                            
        stampofstartdate = '%4d%02d%02d' % (startdate.year, startdate.month, startdate.day)
        stampofstopdate = '%4d%02d%02d' % (stopdate.year, stopdate.month, stopdate.day)
        print '==={ %i/%i }==={ %s->%s }===' % (i+1, numoftimespans, stampofstartdate, stampofstopdate)
        tocurl = 'https://bib-pubdb1.desy.de/search?ln=en&cc=VDB&p=005%3A' + stampofstartdate + '-%3E' + stampofstopdate + '+0247_a%3A10.3204*+and+not+9131_1%3AG%3A(DE-HGF)POF3-620++not+980%3Auser&f=&action_search=Search&c=VDB&c=&sf=&so=d&rm=&rg=' + str(rpp) + '&sc=0&of=xm&jrec=1'
        #only theses
        tocurl = 'https://bib-pubdb1.desy.de/search?ln=en&cc=VDB&p=0247_a%3A10.3204*+and+260__c%3A202*+and+980__a%3Aphd+and+not+9131_1%3AG%3A(DE-HGF)POF3-620++not+980%3Auser&f=&action_search=Search&c=VDB&c=&sf=&so=d&rm=&rg=' + str(rpp) + '&sc=0&of=xm&jrec=1'
        print '  ={ %s }===' % (tocurl)
        pages.append(BeautifulSoup(urllib2.urlopen(tocurl), features="lxml"))
        try:
            numberofresults = int(re.sub('\D', '', pages[-1].contents[1]))
            print len(pages), stampofstartdate, numberofresults
            numofpages = (numberofresults-1) / rpp + 1
            for pagenum in range(numofpages-1):
                time.sleep(2)
                print '---{ %i/%i }---' % (pagenum+2, numofpages)
                tocurl = 'https://bib-pubdb1.desy.de/search?ln=en&cc=VDB&p=005%3A' + stampofstartdate + '-%3E2050+0247_a%3A10.3204*+and+not+9131_1%3AG%3A(DE-HGF)POF3-620++not+980%3Auser&f=&action_search=Search&c=VDB&c=&sf=&so=d&rm=&rg=' + str(rpp) + '&sc=0&of=xm&jrec=' + str((pagenum+1)*rpp+1)
                #only theses
                tocurl = 'https://bib-pubdb1.desy.de/search?ln=en&cc=VDB&p=0247_a%3A10.3204*+and+260__c%3A202*+and+980__a%3Aphd+and+not+9131_1%3AG%3A(DE-HGF)POF3-620++not+980%3Auser&f=&action_search=Search&c=VDB&c=&sf=&so=d&rm=&rg=' + str(rpp) + '&sc=0&of=xm&jrec=' + str((pagenum+1)*rpp+1)
                pages.append(BeautifulSoup(urllib2.urlopen(tocurl), features="lxml"))
        except:
            print '  no records found'
    records = []
    for page in pages:
        for rec in page.find_all('record'):
            records.append(rec)
    jnlfilename = 'desypubdb-%s.%s' % (stampofstartdate, timespan)    
    return (records, jnlfilename)

#use authority records to get ORCID or INSPIRE-ID
def getpersonalidentifiersfrompip(pip):

    #geht nicht per Web
    
    for precid in search_pattern(p='980__a:AUTHORITY 0247_a:%s' % (pip)):
        marc = []
        personrecord = get_record(precid)
        for entry in personrecord['024']:
            typ = False
            for subentry in entry[0]:
                if subentry[0] == '2' and subentry[1] == 'ORCID':
                    typ = 'ORCID'
                elif subentry[0] == '2' and subentry[1] == 'P:(SzGeCERN)INSPIRE':
                    typ = 'INSPIRE'
                elif subentry[0] == 'a':
                    identifier = subentry[1]
            if typ == 'ORCID':
                marc.append(('j', 'ORCID:%s' % (identifier)))
            elif typ == 'INSPIRE':
                marc.append(('i', identifier))
    return marc
    

#transform pubdb-MARC structure to INSPIRE (via ejlmod2)
def tfstrip(x): return x.strip()
def translatearticles(pubdbrecords):
    done =  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir)))
    done += map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/%i/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, now.year-1)))
    done += map(tfstrip,os.popen("grep '^3.*DOI' %s/onhold/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir)))
    done += map(tfstrip,os.popen("grep '^3.*DOI' %s/zu_punkten/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir)))
    done += map(tfstrip,os.popen("grep '^3.*DOI' %s/zu_punkten/enriched/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir)))
    #print done
    #done = [] #tempo
    print '%i DOIs in done' % (len(done))    
    recs = {}
    print 'found %i records' % (len(pubdbrecords))
    i = 0
    for pubdbrecord in pubdbrecords:
        i += 1
        for cf in pubdbrecord.find_all('controlfield', attrs = {'tag' : '001'}):
            recid = cf.text
            print '---{ %i/%i }---{ %s }---' % (i, len(pubdbrecords), recid)
        doiindone = False
        confnote = ''
        rec = {'note' : [], 'tc' : '', 'rn' : [], 'MARC' : []}
        #type code
        skiprecord = False
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '980', 'ind1' : ' ', 'ind2' : ' '}):
            tc = df.subfield.text
            if tc in ['media', 'physobj', 'sware', 'dataset', 'formtmp',
                      'images', 'abstract', 'minutes', 'news', 'patent',
                      'project', 'refs', 'talk', 'comm', 'event', 'course', 'conf',
                      'web', 'award']:
                print 'skip tc=%s' % (tc)
                skiprecord = True
                break
            if tc in ['diploma', 'magister', 'master', 'poster', 'bachelor', 'exam']:
                print 'skip tc=%s' % (tc)
                skiprecord = True
                break
            elif tc == 'phd':
                rec['tc'] = 'T'
                thesismark = [('b', 'PhD')]
                #skiprecord = True #tempo
                break
            elif tc in ['habil', 'Priv. Doz.']:
                rec['tc'] = 'T'
                thesismark = [('b', 'Habilitation')]
                #skiprecord = True #tempo
                break
            elif tc in ['intrep', 'notes', 'preprint', 'report']:
                continue
            elif tc == 'journal':
                rec['tc'] = 'P'
                #skiprecord = True #tempo
                #break #tempo
            elif tc == 'book':
                rec['tc'] = 'B'
                #skiprecord = True #tempo
                #break #tempo
            elif tc == 'contb':
                rec['tc'] = 'S'
                #skiprecord = True #tempo
                #break #tempo
            if tc == 'review':
                rec['tc'] += 'R'
                #skiprecord = True #tempo
                #break #tempo
            if tc == 'contrib':
                rec['tc'] = 'C'
                #skiprecord = True #tempo
                break
            if tc == 'lecture':
                rec['tc'] += 'L'
                #skiprecord = True #tempo
                #break #tempo
            if tc == 'proc':
                rec['tc'] = 'K'
                #skiprecord = True #tempo
                break
        if skiprecord:
            continue
        #DOI
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '024', 'ind1' : '7', 'ind2' : ' '}):
            isdoi = False
            isdesydoi = False
            for sf in df.find_all('subfield', attrs = {'code' : '2'}):
                if sf.text in ['doi', 'DOI', 'datacite_doi']:
                    isdoi = True
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                doi = re.sub('htt.*doi.org\/', '', sf.text)
                if re.search('^10.3204\/', doi):
                    isdesydoi = True
            if isdoi:
                if isdesydoi:
                    rec['doi'] = doi
                else:
                    rec['MARC'].append(('0247', [('2', 'DOI'), ('a', doi)]))
            if doi in done:
                doiindone = True
                break
        if doiindone:
            print '%s already done' % (doi)
            continue
        elif 'doi' in rec.keys():
            done.append(doi)
        #reportnumber
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '088', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rns = sf.text
                if (rec['tc'] == 'C' and re.search('DESY\-PROC', rns)) or (rec['tc'] == 'S'):
                    print 'skip reportnumber - probably from proceedings entry'
                    continue
                for rn in re.split(' *; +', rns):
                    if re.search('arXiv', rn):
                        rec['arxiv'] = rn
                    else:
                        rec['rn'].append(rn)
                        if re.search('DESY\-THESIS', rn): rec['note'].append(rn)
            rec['note'].append(rns)
        #title
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '245', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['tit'] = sf.text
        #abstract
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '520', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['abs'] = sf.text
        #POF
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '913', 'ind1' : '0', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'v'}):
                rec['note'].append(sf.text)
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '913', 'ind1' : '1', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'v'}):
                rec['note'].append(sf.text)
        #experiment
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '693', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                rec['note'].append('EXPERIMENT=%s' % (sf.text))
        #FFT
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '856'}):
            oa = False
            pdf = False
            for sf in df.find_all('subfield', attrs = {'code' : 'y'}):
                if sf.text  == 'OpenAccess':
                    oa = True
            for sf in df.find_all('subfield', attrs = {'code' : 'u'}):
                if re.search('http.*bib\-pubdb1.desy.de.*pdf$', sf.text):
                    pdf = True
                    link = sf.text
            if oa and pdf:
                if (not rec.has_key('FFT')) and (not re.search('title', link)) and rec['tc'] in ['C', 'T', 'K']:
                    try:
                        oafilename = re.sub('.*\/', '', link) + '?subformat=pdfa'
                        urllib.urlretrieve(link, '/afs/desy.de/group/library/www/html/pdf/'+oafilename)
                        rec['FFT'] = 'http://www-library.desy.de/pdf/'+oafilename
                    except:
                        print 'could not download "%s"' % (link)
        #licence
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '915', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                if re.search('Creative Commons Attribution', sf.text):
                    lic = re.sub('Creative Commons Attribution *', '', sf.text)                
                    rec['licence'] = {'licence' : re.sub(' ', '-', lic)}
        #date
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '260', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'c'}):
                rec['date'] = sf.text
        #conference note
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '260', 'ind1' : '2'}):
            confnote = ''
            confsearch = '980__a%3ACONFERENCES'
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                confnote += sf.text + ', '
                if confdict.has_key(sf.text):
                    rec['cnum'] = confdict[sf.text]
            for sf in df.find_all('subfield', attrs = {'code' : 'c'}):
                confnote += sf.text + ', '
                confsearch += '+111__c%3A%2F' + sf.text + '%2F'
            for sf in df.find_all('subfield', attrs = {'code' : 'd'}):
                confnote += sf.text
                parts = re.split(' +\- +', sf.text)
                confsearch += '+111__x%3A' + parts[0] + '+111__y%3A' + parts[1]
        ### publication note
        #book publication info
        if rec['tc'] in ['K', 'B', 'T']:
            for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '260', 'ind1' : ' ', 'ind2' : ' '}):
                entry = []
                for sf in df.find_all('subfield'):
                    entry.append((sf['code'], sf.text))
                rec['MARC'].append(('260', entry))
        #cnum 
        if rec['tc'] in ['C', 'K']:
            for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '111', 'ind1' : '2', 'ind2' : ' '}):
                for sf in df.find_all('subfield', attrs = {'code' : '0'}):
                    rec['cnum'] = sf.text
        #pages
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '300', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : ''}):
                if re.search('^(\d+)\-(\d+)$', sf.text):
                    pages = re.split('\-', sf.text)
                    rec['p1'] = pages[0] 
                    rec['p2'] = pages[1]
                elif rec['tc'] in ['T', 'B', 'K']:
                    if re.search('^(\d+)$', sf.text):
                        rec['pages'] = int(sf.text)
        #journal
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '773', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 't'}):
                rec['jnl'] = sf.text
            for sf in df.find_all('subfield', attrs = {'code' : 'v'}):
                rec['vol'] = sf.text
            for sf in df.find_all('subfield', attrs = {'code' : 'y'}):
                rec['year'] = sf.text
        #isbn
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '022', 'ind1' : ' ', 'ind2' : ' '}):
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                isbn = sf.text
                if (rec['tc'] == 'C' and re.search('DESY\-PROC', rns)) or (rec['tc'] == 'S'):
                    print 'skip ISBN - probably from proceedings entry'
                    continue
                marc = []
                if re.search('electronic', isbn):
                    marc = [('b', 'Online')]
                if re.search('print', isbn):
                    marc = [('b', 'Print')]
                else:
                    marc = []
                isbn = re.sub('^ISBN *', '', isbn)
                isbn = re.sub(' .*', '', isbn)
                isbn = re.sub('\-', '', isbn)
                marc.append(('a', isbn))
                if rec['tc'] in ['B', 'K']:
                    rec['MARC'].append(('020', marc))
                else:
                    rec['MARC'].append(('773', [('z', isbn)]))
        #affiliations
        affdict = {}
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '910', 'ind1' : ' ', 'ind2' : ' '}):
            (affkey, aff) = ('', '')
            for sf in df.find_all('subfield', attrs = {'code' : 'b'}):
                affkey = sf.text
            for sf in df.find_all('subfield', attrs = {'code' : 's'}):
                if sf.text != 'Externes Institut':
                    aff = sf.text
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                if sf.text != 'Externes Institut':
                    aff = sf.text
            if aff and affkey:
                if affdict.has_key(affkey):
                    affdict[affkey].append(aff)
                else:
                    affdict[affkey] = [aff]
        #authors
        for df in pubdbrecord.find_all('datafield', attrs = {'tag' : ['100', '700']}):
            (author, affkey, role) = ('', '', '')
            marc = []
            for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
                marc.append(('a', sf.text))
            for sf in df.find_all('subfield', attrs = {'code' : 'b'}):
                affkey = sf.text
                if affdict.has_key(affkey):
                    for aff in affdict[affkey]:
                        marc.append(('v', aff))
            for sf in df.find_all('subfield', attrs = {'code' : 'e'}):
                if sf.text == 'Thesis advisor':
                    role = 'advisor'
                elif sf.text == 'Editor':
                    role = 'editor'
                elif sf.text == 'Reviewer':
                    role = 'reviewer'
            for sf in df.find_all('subfield', attrs = {'code' : '0'}):
                if re.search('PIP', sf.text):
                    print 'can not get PIP via web'
                    #marc += getpersonalidentifiersfrompip(sf.text)                        
            if role == 'editor':
                marc.append(('e', 'ed.'))
            elif role == 'advisor':
                rec['MARC'].append(('701', marc))
            elif role == 'reviewer':
                #rec['MARC'].append(('701', marc))
                pass        
            else:
                rec['MARC'].append((df['tag'], marc))
        #thesis informations
        if rec['tc'] == 'T':
            for df in pubdbrecord.find_all('datafield', attrs = {'tag' : '502'}):
                for sf in df.find_all('subfield', attrs = {'code' : 'c'}):
                    thesismark.append(('c', bestmatch(sf.text, 'ICN')[0][1]))
                for sf in df.find_all('subfield', attrs = {'code' : 'd'}):
                    thesismark.append(('d', sf.text))
            rec['MARC'].append(('502', thesismark))
        #fake journal
        if not rec.has_key('jnl'):
            rec['jnl'] = 'BOOK'
        #group records according to typecode and individual conferences
        if rec.has_key('cnum'):
            section = rec['cnum']
        else:
            section = rec['tc']
            if confnote:
                rec['note'].append(confnote)
                rec['note'] += inspireconf(confsearch)
        if recs.has_key(section):
            recs[section].append(rec)
        else:
            recs[section] = [rec]
        print rec            
    return recs
    

if __name__ == '__main__':
    usage = """
        python bibpuddb.py [timespan to harvest]
    """
    if len(sys.argv) > 2:
        print "Too many arguments given!!!"
        sys.exit(2)
    elif len(sys.argv) == 2:
        try:
            timespan = int(sys.argv[1])
        except:
            print '"%s" is not a number' % (timespan)
            sys.exit(2)
    else:
        timespan = 9

    (pubdbrecords, jnlfilename) = requestarticles(timespan)
    records = translatearticles(pubdbrecords)
    #split too large xmls
    for tc in records.keys():
        if len(tc) <= 1 and len(records[tc]) > chunksize:        
            for i in range(0, len(records[tc]), chunksize):
                records[tc + str(i)] = records[tc][i:i+chunksize]
            del records[tc]                                    
    for tc in records.keys():
        if not tc or not tc[0] in ['T']:
            continue
        #write xml-file
        xmlf    = os.path.join(xmldir, '%s.%s.xml' % (jnlfilename, tc))
        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')    
        ejlmod2.writenewXML(records[tc], xmlfile, publisher, xmlf[:-4])
        xmlfile.close()   
        #retrival
        retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
        retfiles_text = open(retfiles_path,"r").read()
        line = "%s.%s.xml\n" % (jnlfilename, tc)
        if not line in retfiles_text: 
            retfiles = open(retfiles_path,"a")
            retfiles.write(line)
            retfiles.close()



