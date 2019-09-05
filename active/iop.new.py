# -*- coding: UTF-8 -*-
# checks for new ftp-feeds from IOP and converts them
# FS 2019-05-07

import os
import sys
import re
import time
import codecs
from bs4 import BeautifulSoup
import urllib2
import urlparse
import ejlmod2
import tarfile
import shutil

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ftpdir = '/afs/desy.de/group/library/preprints/incoming/IOP'
iopdirtmp = '/afs/desy.de/group/library/publisherdata/iop/tmp'
iopdirdone = '/afs/desy.de/group/library/publisherdata/iop/done'
pdfdir = '/afs/desy.de/group/library/publisherdata/pdf'
publisher = 'IOP'

#ISSN to journal name
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
       '0295-5075': 'EPL',
       '1757-899X': 'IOP Conf.Ser.Mater.Sci.Eng.',
       '1751-8121': 'J.Phys.',
       '0953-4075': 'J.Phys.',
       '2399-6528': 'J.Phys.Comm.',
       '0953-8984': 'J.Phys.Condens.Matter',
       '1742-6596': 'J.Phys.Conf.Ser.',
       '0954-3899': 'J.Phys.',
       '1475-7516': 'JCAP',
       '1126-6708': 'JHEP',
       '1748-0221': 'JINST',
       '1742-5468': 'JSTAT',
       '0957-0233': 'Measur.Sci.Tech.',
       '0026-1394': 'Metrologia',
       '1367-2630': 'New J.Phys.',
       '0951-7715': 'Nonlinearity',
       '0031-9120': 'Phys.Educ.',
       '0031-9155': 'Phys.Med.Biol.',
       '1402-4896': 'Phys.Scripta',
       '1063-7869': 'Phys.Usp.',
       '0741-3335': 'Plasma Phys.Control.Fusion',
       '1538-3873': 'Publ.Astron.Soc.Pac.',
       '0034-4885': 'Rep.Prog.Phys.',
       '1674-4527': 'Res.Astron.Astrophys.',
       '0036-0279': 'Russ.Math.Surveys',
       '0953-2048': 'Supercond.Sci.Technol.'}
jnl['2516-1067'] = 'Plasma Res.Express'

#uninteresting journals in feed
jnlskip = {'2058-8585' : 'Flexible and Printed Electronics'}

#CNUMs for conferences in JINST
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
            'International Conference on Instrumentation for Colliding Beam Physics (INSTR17)' : 'C17-02-27',
            'Precision Astronomy with Fully Depleted CCDS (PACCD2016)' : 'C16-12-01.1',
            '19th International Workshop on Radiation Imaging Detectors (IWORID2017)' : 'C17-07-02.5',
            '11th International Conference on Position Sensitive Detectors (PSD11)' : 'C17-09-03.2',
            'Calorimetry for the High Energy Frontier (CHEF2017)' : 'C17-10-02.3',
            'XII International Symposium on Radiation from Relativistic Electrons in Periodic Structures (RREPS-17)' : 'C17-09-18.6',
            'International Workshop on Fast Cherenkov Detectors - Photon detection, DIRC design and DAQ (DIRC2017)' : 'C17-08-07.6',
            'Light Detection in Noble Elements (LIDINE2017)' : 'C17-09-22',
            'XII International Symposium on Radiation from Relativistic Electrons in Periodic Structures (RREPS-17)' : 'C17-09-18.6',
            '24th International congress on x-ray optics and microanalysis (ICXOM24)' : 'C17-09-25.6',
            '20th International Workshop On Radiation Imaging Detectors' : 'C18-06-24.2',
            '5th International Conference Frontiers in Diagnostcs Technologies (ICFDT)' : 'C18-10-03.1',
            'The 9th International Workshop on Semiconductor Pixel Detectors for Particles and Imaging' : 'C18-12-10'}


#check for new ftp-feeds
todo = []
for datei in os.listdir(ftpdir):
    if datei in os.listdir(iopdirdone):
        print '%s already in done' % (datei)
    else:
        todo.append(datei)
print '%i packages to do: %s' % (len(todo), ', '.join(todo))
if not todo:
    sys.exit(0)

#extract the feeds:
for directory in todo:
    for datei in os.listdir(os.path.join(ftpdir, directory)):
        print 'extracting %s' % (os.path.join(ftpdir, directory, datei))
        journalfeed = tarfile.open(os.path.join(ftpdir, directory, datei), 'r:gz')
        journalfeed.extractall(path=iopdirtmp)
        journalfeed.close()

collapseWs = re.compile('[\n \t]+')
#initialBlank = re.compile('([A-Z]) ')
initialEnd = re.compile(r'([A-Z])\b')
#convert xml-tags to LaTex-style        
def fsunwrap(tag):
    try: 
        for sup in tag.find_all('SUP'):
            cont = sup.string
            sup.replace_with('^'+cont)
    except:
        print 'fsunwrap-sup-problem'
    try: 
        for sub in tag.find_all('SUB'):
            cont = sub.string
            sub.replace_with('_'+cont)
    except:
        print 'fsunwrap-sub-problem'
    return tag

#convert individual article        
def convertarticle(issn, vol, isu, artid):
    if issn in jnl.keys():
        rec = {'jnl' : jnl[issn], 'note' : [], 'keyw' : [], 'aff' : [], 'refs' : []}
        if issn in ['1742-6596']:
            tc = ['C']
        elif issn in ['0034-4885']:
            tc = ['PR']
        else:
            tc = ['P']
    elif issn in jnlskip.keys():
        print 'skip journal "%s"' % (jnlskip[issn])
        return []
    else:
        print 'do not know journal with ISSN:%s' % (issn)
        sys.exit(0)
        rec = {'jnl' : issn, 'note' : [], 'keyw' : [], 'aff' : [], 'refs' : []}
    ###read metadata
    if os.path.isfile(os.path.join(iopdirtmp, issn, vol, isu, artid, '.article')):
        inf = open(os.path.join(iopdirtmp, issn, vol, isu, artid, '.article'))
        article = BeautifulSoup(''.join(inf.readlines()))
        inf.close()
        #article type
        for attrnode in article.find_all('attributes'):        
            if attrnode.has_attr('art_type'):
                if attrnode['art_type'] == 'rev':
                    tc = ['R']
                elif attrnode['art_type'] == 'misc': 
                    tc = ['']
        #conference
        for focusnode in article.find_all('art_focus'):
            if focusnode.has_attr('alt'):
                if focusnode['alt'] == 'Proceeding Article':
                    tc = ['C']
                rec['note'].append(focusnode['alt'])
            if focusnode.has_attr('group'):
                comm = focusnode['group']
                rec['comments'] = [comm]
                if comm in cnumdict.keys():
                    rec['cnum'] = cnumdict[comm]
        #volume
        for volumenode in article.find_all('volume'):
            rec['vol'] = volumenode.text.strip()
            if issn in ['1674-1056', '0953-4075']:
                rec['vol'] = 'B'+rec['vol']
            elif issn == '1674-1137':
                rec['vol'] = 'C'+rec['vol']
            elif issn == '1751-8121':
                rec['vol'] = 'A'+rec['vol']
            elif issn == '0954-3899':
                rec['vol'] = 'G'+rec['vol']
        #issue
        for issuenode in article.find_all('issue'):
            issue = issuenode.text.strip()
            if issn == '1402-4896' and issue[0] == 'T':
                rec['vol'] = issue
            else:
                rec['issue'] = issue
                if issue.startswith("S"): #we have a supplememnt 
                    rec['jnl'] += " Suppl."                     
        #year
        for datenode in article.find_all('date_cover'):
            datecover = datenode.text.strip()
            rec['year'] = datecover[0:4]
            if rec['jnl'] in ['JCAP ', 'JHEP ', 'JSTAT ']:
                rec['vol'] = datecover[2:4] + datecover[5:7]
        #article number
        for artnumnode in article.find_all('artnum'):
            rec['artnum'] = artnumnode.text.strip()
        #DOI
        for doinode in article.find_all('doi'):
            rec['doi'] = doinode.text.strip()
        #pages
        for pagenode in article.find_all('pages'):
            if pagenode.has_attr('extent'):
                rec['pages'] = pagenode['extent']
            if pagenode.has_attr('start'):
                rec['p1'] = pagenode['start']
            if pagenode.has_attr('end'):
                rec['p2'] = pagenode['end']
        #arXiv number
        for idnode in article.find_all('external_id'):
            if idnode.has_attr('type') and idnode['type'] == 'arxive':
                rec['arxiv'] = re.sub('v.*', '', idnode.text.strip())
        #date
        for datenode in article.find_all('date_online'):
            if datenode.has_attr('fulltext'):
                rec['date'] = datenode['fulltext']
            elif datenode.has_attr('header'):
                rec['date'] = datenode['header']
            else:
                print 'no date for %s' % (rec['doi'])
        #title
        for titnode in article.find_all('title_full'):
            for footnode in titnode.find_all('footnote'):
                rec['note'].append(footnode.text.strip())
                footnode.replace_with('')
            fsunwrap(titnode)
            rec['tit'] = titnode.text.strip()
            rec['tit']  = collapseWs.sub(' ', rec['tit'])
        #keywords
        for kwnode in article.find_all('kwd_main'):
            rec['keyw'].append(kwnode.text.strip())
        #authors
        authors = []
        afid = ''
        for aunode in article.find_all('author_granular'):
            #name
            (fname, nlfname, nllname, lname) = ('', '', '', '')
            for group in aunode.find_all('group'):
                rec['col'] = group.text
            for fnamenode in aunode.find_all('given'):
                fname = re.sub('\.\.', '.', initialEnd.sub(r'\1.', fnamenode.text))
                if fnamenode.has_attr('non_latin'):
                    nlfname = fnamenode['non_latin']
            for lnamenode in aunode.find_all('surname'):
                lname = lnamenode.text
                if lnamenode.has_attr('non_latin'):
                    nllname = lnamenode['non_latin']
            #affiliation
            afido = afid
            afi = ''
            if aunode.has_attr('affil'):
                afid = aunode['affil'].replace(',','; =')
            if (afid != afido) and afido:
                authors.append('=' + afido)         
            #ORCID and combine
            if aunode.has_attr('orcid'):
                orcid = 'ORCID:' + aunode['orcid']
                finalauthor = lname + ', ' + fname +  ', ' + orcid
            else:
                finalauthor = lname + ', ' + fname
            if nllname + nlfname != '':
                finalauthor += ', CHINESENAME: ' + nllname + ' ' +  nlfname
            if re.search('[a-zA-Z]', finalauthor):
                authors.append(finalauthor)
        if afid:
            authors.append('=' + afid)
        rec['auts'] = authors
        (afid, afido) = ('', '')
        if not authors:
            for aunode in article.find_all('author'):
                aut = aunode.text.strip()
                if 'Collaboration' in aut:
                    rec['col'] = aut
                    continue
                authors.append(aut)
                if aunode.has_attr('affil'):
                    afid = aunode['affil'].replace(',','; =')
                    authors.append('=' + afid)
            rec['auts'] = authors
        #affiliations
        (affid, orgname) = ('', '')
        for afnode in article.find_all('affil'):
            if afnode.has_attr('id'):
                affid = afnode['id']
            rec['aff'].append('%s= %s' % (affid, collapseWs.sub(' ', afnode.text.strip())))
        #Open Access
        for oanode in article.find_all('open_access'):
            rec['licence'] = {'url' : oanode['url']}
            rec['FFT'] = 'http://iopscience.iop.org/article/%s/pdf' % (rec['doi'])
        #typecode
        rec['tc'] = tc
        try:
            if issn == '1748-0221' and rec['p1'][0] == 'C':
                rec['tc'] = ['C']
        except:
            pass
        #abstract
        for absnode in article.find_all('header_text', attrs = {'heading' : 'Abstract'}):
            fsunwrap(absnode)
            rec['abs'] = collapseWs.sub(' ', absnode.text.strip())    
        ###read references
        if os.path.isfile(os.path.join(iopdirtmp, issn, vol, isu, artid, '.refs')):
            inf = open(os.path.join(iopdirtmp, issn, vol, isu, artid, '.refs'))
            references = BeautifulSoup(''.join(inf.readlines()))
            inf.close()
            for reference in references.find_all('reference'):
                for x in reference.find_all('ref_citation'):
                    ref = [('x', x.text.strip())]
                #detailed only if there is a DOI to 'ensure' that it is matched
                for refdoi in reference.find_all('ref_doi'):
                    ref.append(('a', 'doi:' + refdoi.text.strip()))
                    for ref_year in reference.find_all('refyear'):
                        ref.append(('y', refyear.text.strip()))
                    for ref_authors in reference.find_all('refauthors'):
                        ref.append(('h', refauthors.text.strip()))
                    #for refjournal in reference.find_all('ref_journal'):
                    #   pbn = refjournal.text.strip()
                    #   for refvolume in reference.find_all('ref_volume'):
                    #       pbn += ',' + refvolume.text.strip()
                    #   for refstartpage in reference.find_all('ref_start_page'):
                    #       pbn += ',' + refstartpage.text.strip()
                    #   ref.append(('s', pbn))
                rec['refs'].append(ref)
        else:
            print '   no references for ', rec['doi'], rec['tit']
        ###check for fulltext
        for datei in os.listdir(os.path.join(iopdirtmp, issn, vol, isu, artid)):
            if re.search('\.pdf$', datei):
                pdfsrc = os.path.join(iopdirtmp, issn, vol, isu, artid, datei)
                pdfdst = os.path.join(pdfdir, re.sub('[\/\(\)]', '_', rec['doi']) + '.pdf')
                if os.path.isfile(pdfdst):
                    print '   fulltext found but no nead to copy'
                else:
                   try:
                        shutil.copy(pdfsrc, pdfdst)
                        print '   fulltext found and copied'
                   except:
                       print '   fulltext found but not copied!'
                       print pdfsrc
                       print pdfdst
        ###
        print '.', rec['doi'], rec.keys()        
        return rec
    else:
        return {}













        
#scan extracted directories
for issn in os.listdir(iopdirtmp):
    if re.search('\d\d\d\d\-\d\d\d\d', issn):
        for vol in os.listdir(os.path.join(iopdirtmp, issn)):
            if re.search('\d', vol):
                recs = []
                issues = []
                for isu in os.listdir(os.path.join(iopdirtmp, issn, vol)):
                    if re.search('\d', isu):
                        print '------{ ISSN:%s VOL:%s ISU:%s}------' % (issn, vol, isu)
                        issues.append(isu)
                        for artid in os.listdir(os.path.join(iopdirtmp, issn, vol, isu)):
                            if re.search('\d', artid):
                                rec = convertarticle(issn, vol, isu, artid)
                                if rec: recs.append(rec)
                if recs:
                    if issn in jnl.keys():
                        if 'vol' in recs[0].keys():
                            iopf = 'iop-%s-%s%s_%s' % ('_'.join(todo), re.sub(' ', '', jnl[issn]), recs[0]['vol'], '.'.join(issues))
                        else:
                            iopf = 'iop-%s-%s%s_%s' % ('_'.join(todo), re.sub(' ', '', jnl[issn]), vol, '.'.join(issues))                 
                    else:
                        iopf = 'iop-%s-%s%s_%s' % ('_'.join(todo), re.sub(' ', '', issn), vol, '.'.join(issues))

                    if not issn in jnlskip.keys():
                        xmlf = os.path.join(xmldir,iopf+'.xml')
                        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
                        ejlmod2.writeXML(recs ,xmlfile,'IOP')
                        xmlfile.close()
                  
                        #retrival
                        retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
                        retfiles_text = open(retfiles_path,"r").read()
                        line = iopf+'.xml'+ "\n"
                        if not line in retfiles_text: 
                            retfiles = open(retfiles_path,"a")
                            retfiles.write(line)
                            retfiles.close()
                print '   %s with %i records\n' % (iopf, len(recs))

#if everything went fine, move the files to done
for directory in todo:
    shutil.copytree(os.path.join(ftpdir, directory), os.path.join(iopdirdone, directory))    
shutil.rmtree(iopdirtmp)
print 'done :-)'
    
