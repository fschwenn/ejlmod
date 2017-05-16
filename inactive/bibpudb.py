#!/usr/bin/python
# -*- coding: UTF-8 -*-
#bib-pubdbvm1
from invenio.search_engine import search_pattern
from invenio.search_engine import get_record
from invenio.search_engine import get_fieldvalues
from afftranslator2 import *

import ejlmod2

import codecs
import re
import time
import datetime
import os
import sys
import urllib2
import urlparse
import xml.etree.ElementTree as ET


chunksize = 80

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
    searchurl = 'http://inspirehep.net/search?ln=en&cc=Conferences&ln=en&cc=Conferences&p=' + confsearch + '&action_search=Search&sf=conferencestartdate&so=d&rm=&rg=25&sc=0&of=xm'
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
        notes.append(note)
    print confsearch
    print notes
    return notes
        
    

#harvest pubdb for new records with DESY-DOI
def requestarticles(timespan):
    startdate = now + datetime.timedelta(days=-timespan)
    stampofstartdate = '%4d%02d%02d' % (startdate.year, startdate.month, startdate.day)
    jnlfilename = 'desypubdb-%s.%s' % (stampofstartdate, timespan)    
    recids = search_pattern(p="005:%s->2050 0247_a:10.3204* and not 9131_1:'G:(DE-HGF)POF3-620 980:unrestricted not 980:deleted'" % (stampofstartdate))
    #recids = search_pattern(p="001:295330")

    return (recids, jnlfilename)

#use authority records to get ORCID or INSPIRE-ID
def getpersonalidentifiersfrompip(pip):
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
def translatearticles(recids):
    done =  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir)))
    done += map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/%i/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, now.year-1)))
    done += map(tfstrip,os.popen("grep '^3.*DOI' %s/onhold/*desypubdb*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir)))
    #print done
    print '%i DOIs in done' % (len(done))    
    recs = {}
    print 'found %i records' % (len(recids))
    for recid in recids:        
        print '---%i---' % (recid)
        doiindone = False
        pubdbrecord = get_record(recid)
        confnote = ''
        rec = {'note' : [], 'tc' : '', 'rn' : [], 'MARC' : []}
        #type code
        skiprecord = False
        for tc in get_fieldvalues(recid, '980__a'):
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
                break
            elif tc in ['habil', 'Priv. Doz.']:
                rec['tc'] = 'T'
                thesismark = [('b', 'Habilitation')]
                break
            elif tc in ['intrep', 'notes', 'preprint', 'report']:
                continue
            elif tc == 'journal':
                rec['tc'] = 'P'
            elif tc == 'book':
                rec['tc'] = 'B'
            elif tc == 'contb':
                rec['tc'] = 'S'
            if tc == 'review':
                rec['tc'] += 'R'
            if tc == 'contrib':
                rec['tc'] = 'C'
                break
            if tc == 'lecture':
                rec['tc'] += 'L'
            if tc == 'proc':
                rec['tc'] = 'K'
                break
        if skiprecord:
            continue
        #DOI
        if pubdbrecord.has_key('024'):
            for entry in pubdbrecord['024']:
                isdoi = False
                isdesydoi = False
                for subentry in entry[0]:
                    if subentry[0] == '2' and subentry[1] in ['doi', 'DOI', 'datacite_doi']:
                        isdoi = True
                    #take only DESY-DOI
                    if subentry[0] == 'a':
                        doi = re.sub('http:\/\/dx.doi.org\/', '', subentry[1])
                        if re.search('^10.3204\/', subentry[1]):
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
        #reportnumber
        for rns in get_fieldvalues(recid, '088__a'):
            if rec['tc'] == 'C' and re.search('DESY\-PROC', rns):
                print 'skip reportnumber - probably from proceedings entry'
                continue
            for rn in re.split(' *; +', rns):
                if re.search('arXiv', rn):
                    rec['arxiv'] = rn
                else:
                    rec['rn'].append(rn)
                    if re.search('DESY\-THESIS', rn): rec['note'].append(rn)
        #title
        for tit in get_fieldvalues(recid, '245__a'):
            rec['tit'] = tit
        #abstract
        for abs in get_fieldvalues(recid, '520__a'):
            rec['abs'] = abs
        #POF
        for pof in get_fieldvalues(recid, '9130_v'):
            rec['note'].append(pof)
        for pof in get_fieldvalues(recid, '9131_v'):
            rec['note'].append(pof)
        #experiment
        for exp in get_fieldvalues(recid, '693__a'):
            rec['note'].append('EXPERIMENT=%s' % (exp))
        #FFT
        if pubdbrecord.has_key('856'):
            for entry in pubdbrecord['856']:
                oa = False
                pdf = False
                for subentry in entry[0]:
                    if subentry[0] == 'y' and subentry[1] == 'OpenAccess':
                        oa = True
                    elif subentry[0] == 'u' and re.search('http.*bib\-pubdb1.desy.de.*pdf$', subentry[1]):
                        pdf = True
                        link = subentry[1]
                if oa and pdf:
                    rec['FFT'] = link
        #licence
        for lic in get_fieldvalues(recid, '915__a'):
            if re.search('Creative Commons Attribution', lic):
                lic = re.sub('Creative Commons Attribution *', '', lic)                
                rec['licence'] = {'licence' : re.sub(' ', '-', lic)}
        #date
        for dat in get_fieldvalues(recid, '260__c'):
            rec['date'] = dat
        #conference note
        if pubdbrecord.has_key('111'):
            confnote = ''
            confsearch = '980__a%3ACONFERENCES'
            for subentry in get_fieldvalues(recid, '1112_a'):
                confnote += subentry + ', '
                if confdict.has_key(subentry):
                    rec['cnum'] = confdict[subentry]
            for subentry in get_fieldvalues(recid, '1112_c'):
                confnote += subentry + ', '
                confsearch += '+111__c%3A%2F' + subentry + '%2F'
            for subentry in get_fieldvalues(recid, '1112_d'):
                confnote += subentry 
                parts = re.split(' +\- +', subentry)
                confsearch += '+111__x%3A' + parts[0] + '+111__y%3A' + parts[1]
        ### publication note
        #book publication info
        if rec['tc'] in ['K', 'B', 'T']:
            if pubdbrecord.has_key('260'):
                for entry in pubdbrecord['260']:
                    rec['MARC'].append(('260', entry[0]))
        #cnum 
        if rec['tc'] in ['C', 'K']:
            for cnum in get_fieldvalues(recid, '1112_0'):
                rec['cnum'] = cnum
        #pages
        for prange in get_fieldvalues(recid, '300__a'):
            if re.search('^(\d+)\-(\d+)$', prange):
                pages = re.split('\-', prange)
                rec['p1'] = pages[0] 
                rec['p2'] = pages[1]
            elif rec['tc'] in ['T', 'B', 'K']:
                if re.search('^(\d+)$', prange):
                    rec['pages'] = int(prange)
        #journal
        for jnl in get_fieldvalues(recid, '773__t'):
            rec['jnl'] = jnl
        #volume
        for vol in get_fieldvalues(recid, '773__v'):
            rec['vol'] = vol
        #year
        for year in get_fieldvalues(recid, '773__y'):
            rec['year'] = year
        #isbn
        for isbn in get_fieldvalues(recid, '020__a'):
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
        if pubdbrecord.has_key('910'):
            for entry in pubdbrecord['910']:
                (affkey, aff) = ('', '')
                for subentry in entry[0]:
                    if subentry[0] == 'b':
                        affkey = subentry[1]
                    elif subentry[0] == 's' and not subentry[1] == 'Externes Institut':
                        aff = subentry[1]
                    elif subentry[0] == 'a' and not subentry[1] == 'Externes Institut':
                        aff = subentry[1]
                if aff and affkey:
                    if affdict.has_key(affkey):
                        affdict[affkey].append(aff)
                    else:
                        affdict[affkey] = [aff]
        #authors
        for marcfield in ['100', '700']:
            if pubdbrecord.has_key(marcfield):
                for entry in pubdbrecord[marcfield]:
                    (author, affkey, role) = ('', '', '')
                    marc = []
                    for subentry in entry[0]:
                        if subentry[0] == 'a':
                            marc.append(('a', subentry[1]))
                        elif subentry[0] == 'b':
                            #conferences get ICNs in pubdb ?
                            #if rec['tc'] in ['C', 'K']:
                            #    subfield = 'u'
                            #else:
                            subfield = 'v'
                            affkey = subentry[1]
                            if affdict.has_key(affkey):
                                for aff in affdict[affkey]:
                                    marc.append((subfield, aff))
                        elif subentry[0] == 'e':
                            if subentry[1] == 'Thesis advisor':
                                role = 'advisor'
                            elif subentry[1] == 'Editor':
                                role = 'editor'
                        elif subentry[0] == '0' and re.search('PIP', subentry[1]):
                            marc += getpersonalidentifiersfrompip(subentry[1])                        
                    if role == 'editor':
                        marc.append(('e', 'ed.'))
                    if role == 'advisor':
                        rec['MARC'].append(('701', marc))
                    else:
                        rec['MARC'].append((marcfield, marc))
        #thesis informations
        if rec['tc'] == 'T':
            for entry in pubdbrecord['502']:
                for subentry in entry[0]:
                    if subentry[0] == 'c':
                        thesismark.append(('c', bestmatch(subentry[1], 'ICN')[0][1]))
                    elif subentry[0] == 'd':
                        thesismark.append(subentry)
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
    (recids, jnlfilename) = requestarticles(timespan)
    records = translatearticles(recids)
    #split too large xmls
    for tc in records.keys():
        if len(tc) == 1 and len(records[tc]) > chunksize:        
            for i in range(0, len(records[tc]), chunksize):
                records[tc + str(i)] = records[tc][i:i+chunksize]
            del records[tc]                                    
    for tc in records.keys():
        #if not tc[0] in ['T', 'C', 'K']:
        #    continue
        #write xml-file
        xmlf    = os.path.join(xmldir, '%s.%s.xml' % (jnlfilename, tc))
        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')    
        ejlmod2.writeXML(records[tc], xmlfile, publisher)
        xmlfile.close()   
        #retrival
        retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
        retfiles_text = open(retfiles_path,"r").read()
        line = "%s.%s.xml\n" % (jnlfilename, tc)
        if not line in retfiles_text: 
            retfiles = open(retfiles_path,"a")
            retfiles.write(line)
            retfiles.close()



