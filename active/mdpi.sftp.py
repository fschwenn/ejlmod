# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest MDPI journals (Universe, Symmetry, Sensors, Instruments, Galaxies, Entropy, Atoms) via sftp
# FS 2022-02-03

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time
import pysftp
import tarfile
from refextract import  extract_references_from_string

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'
publisherpath = '/afs/desy.de/group/library/publisherdata/mdpi'
pdfpath = '/afs/desy.de/group/library/publisherdata/pdf/10.3390'
tmppath = publisherpath + '/tmp'

def tfstrip(x): return x.strip()

chunksize = 100
numberofissues = 4

publisher = 'MDPI'
jnl = sys.argv[1]
if jnl in ['proceedings', 'psf']:
    vol = sys.argv[2]
    iss = sys.argv[3]
    cnum = sys.argv[4]

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
startdate = now + datetime.timedelta(days=-90*10)
stampofstartdate = '%4d-%02d-%02d' % (startdate.year, startdate.month, startdate.day)

conferences = {u'Selected Papers from the 1st International Electronic Conference on Universe (ECU 2021)' : 'C21-02-22',
               u'Selected Papers from the 17th Russian Gravitational Conference —International Conference on Gravitation, Cosmology and Astrophysics (RUSGRAV-17)' : 'C20-06-28'}



missingpubnotes = ["10.3390/universe8020085","10.3390/sym14010130","10.3390/photonics9020061","10.3390/sym14020265","10.3390/metrology1020008","10.3390/app112411669","10.3390/e24010104","10.3390/molecules27030597","10.3390/e24010043","10.3390/sym14010180","10.3390/nano12020243","10.3390/nano11112972","10.3390/foundations1020017","10.3390/galaxies9040078","10.3390/math9182178","10.3390/e23111371","10.3390/universe6050068","10.3390/e23101353","10.3390/e23111377","10.3390/psf2021003008","10.3390/universe7010015","10.3390/galaxies9020023","10.3390/ECU2021-09310","10.3390/e24010012","10.3390/atmos12091230","10.3390/e24010101","10.3390/universe705013","10.3390/universe7050139","10.3390/e23101333","10.3390/e23101350","10.3390/photonics8120552","10.3390/sym13060978","10.3390/app11104357","10.3390/rs12203440","10.3390/sym1010000","10.3390/w12113263","10.3390/math8091469","10.3390/data5030085","10.3390/e22010111","10.3390/s20071930","10.3390/books978-3-03921-765-6","10.3390/e22010101","10.3390/quantum1020025","10.3390/universe5050099","10.3390/sym11070880","10.3390/data3040056","10.3390/universe5030080","10.3390/sym10090396","10.3390/sym10090415","10.3390/jimaging4060077","10.3390/mi8090277","10.3390/polym12051066","10.3390/s150100515","10.3390/fractalfract2040026","10.3390/geosciences11060239","10.3390/s151127905","10.3390/cli3030474"]



done = []
if jnl == 'proceedings':
    jnlfilename = 'mdpi_proc%s.%s_%s' % (vol, iss, cnum)
elif jnl == 'psf':
    jnlfilename = 'mdpi_psf%s.%s_%s' % (vol, iss, cnum)
else:
    reoldsyntax = re.compile('^([a-z]*\-\d+\-)(\d+).xml$')
    jnlfilename = '%s.%s' % (jnl, stampoftoday)
    donepath = os.path.join(publisherpath, 'done', jnl)
    for voldir in os.listdir(donepath):
        for issuedir in os.listdir(os.path.join(donepath, voldir)):
            for articledir in os.listdir(os.path.join(donepath, voldir, issuedir)):
                for articlefile in os.listdir(os.path.join(donepath, voldir, issuedir, articledir)):
                    done.append(os.path.join(tmppath, voldir, issuedir, articledir, articlefile))
                    if reoldsyntax.search(articlefile):
                        iss = '%02i' % (int(re.sub('\D', '', issuedir)))
                        afn = reoldsyntax.sub(r'\1', articlefile) + iss + reoldsyntax.sub(r'-\2.xml', articlefile)
                        adn = afn[:-4]
                        done.append(os.path.join(tmppath, voldir, issuedir, adn, afn))
    print 'already done:', len(done)


    
###clean formulas in tag
def cleanformulas(tag):
    #change html-tags into LaTeX
    for italic in tag.find_all('italic'):
        it = italic.text.strip()
        #appears within sub/sup :(
        #  italic.replace_with('$%s$' % (it))
        italic.replace_with(it)
    for sub in tag.find_all('sub'):
        st = sub.text.strip()
        sub.replace_with('$_{%s}$' % (st))
    for sup in tag.find_all('sup'):
        st = sup.text.strip()
        sup.replace_with('$^{%s}$' % (st))
    #handle MathML/LaTeX formulas
    for inlineformula in tag.find_all(['inline-formula', 'disp-formula']):
        mmls = inlineformula.find_all('mml:math')
        tms = inlineformula.find_all('tex-math')
        #if len(mmls) == 1:
        #    inlineformula.replace_with(mmls[0])
        if len(tms) == 1:
            for tm in tms:
                tmt = re.sub('  +', ' ', re.sub('[\n\t\r]', '', tm.text.strip()))
                tmt = re.sub('.*begin.document..(.*)..end.document.*', r'\1', tmt)
                inlineformula.replace_with(tmt)
        else:
            #print 'DECOMPOSE', inlineformula
            inlineformula.decompose()            
    output = tag.text.strip()
    #MML output = ''
    #MML for tt in tag.contents:
    #MML     output += unicode(tt)
    #unite subsequent LaTeX formulas
    output = re.sub('\$\$', '', output)
    return output

#extract references
def get_references(rl):
    refs =  []
    #convert individual references
    for ref in rl.find_all('ref'):
        (lt, refno) = ('', '')
        for label in ref.find_all('label'):
            lt = label.text.strip()
            lt = re.sub('\W', '', lt)
            if re.search('\[', lt):
                refno = '%s ' % (lt)
            else:
                refno = '[%s] ' % (lt)
        #journal
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : 'journal'}):
            (title, authors, pbn, doi) = ('', [], '', '')
            #authors
            for nametag in mc.find_all('name'):
                name = ''
                for gn in nametag.find_all('given-names'):
                    name = gn.text.strip()
                for sn in nametag.find_all('surname'):
                    name += ' ' + sn.text.strip()
                authors.append(name)
            #title
            for at in mc.find_all('article-title'):
                #title = at.text.strip()
                title = cleanformulas(at)
            #pubnote
            for source in mc.find_all('source'):
                pbn = source.text.strip()
            for volume in mc.find_all('volume'):
                pbn += ' ' + volume.text.strip()
            for issue in mc.find_all('issue'):
                pbn += ', No. ' + issue.text.strip()
            for year in mc.find_all('year'):
                pbn += ' (%s) ' % (year.text.strip())
            for fpage in mc.find_all('fpage'):
                pbn += ' ' + fpage.text.strip()
            for lpage in mc.find_all('lpage'):
                pbn += '-' + lpage.text.strip()
            #refextract on pbn to normalize it
            repbn = extract_references_from_string(pbn, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}")
            if repbn and 'journal_reference' in repbn[0].keys():
                #print ' [refextract] normalize "%s" to "%s"' % (pbn, repbn[0]['journal_reference'])
                pbn = repbn[0]['journal_reference']
            #DOI
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'doi'}):
                doi = pi.text.strip()
            #arXiv
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'arxiv'}):
                pbn += ', arXiv: %s' % (pi.text.strip())
            #all together            
            if doi:
                reference = [('x', refno + '%s: %s, %s, DOI: %s' % (', '.join(authors), title, pbn, doi))]
                reference.append(('a', 'doi:'+doi))
                if lt: reference.append(('o', re.sub('\D', '', lt)))
            else:
                reference = [('x', refno + '%s: %s, %s' % (', '.join(authors), title, pbn))]
            refs.append(reference)
        #book
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : ['confproc', 'book', 'thesis']}):
            (atitle, btitle, editors, authors, pbn, bpbn, doi) = ('', '', [], [], '', '', '')
            #authors/editors
            for pg in mc.find_all('person-group'):
                for nametag in mc.find_all('name'):
                    name = ''
                    for gn in nametag.find_all('given-names'):
                        name = gn.text.strip()
                    for sn in nametag.find_all('surname'):
                        name += ' ' + sn.text.strip()
                    if pg['person-group-type'] == 'author':
                        authors.append(name)
                    elif pg['person-group-type'] == 'editor':
                        editors.append(name)
            #title
            for at in mc.find_all('article-title'):
                atitle = cleanformulas(at)
            #book title
            for source in mc.find_all('source'):
                btitle = cleanformulas(source)
            #book pubnote
            for publishername in mc.find_all('publisher-name'):
                bpbn = publishername.text.strip() + ', '
            for publisherloc in mc.find_all('publisher-loc'):
                bpbn += publisherloc.text.strip() + ', '
            for year in mc.find_all('year'):
                bpbn += year.text.strip()
            #pubnote
            for fpage in mc.find_all('fpage'):
                pbn += ' ' + fpage.text.strip()
            for lpage in mc.find_all('lpage'):
                pbn += '-' + lpage.text.strip()
            #all together
            if atitle:
                refs.append([('x', refno + '%s: %s, pages %s in: %s: %s, %s' % (', '.join(authors), atitle, pbn, ', '.join(editors), btitle, bpbn))])
            else:
                refs.append([('x', refno + '%s: %s, %s' % (', '.join(authors), btitle, bpbn))])
        #web
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : ['web', 'gov']}):
            (title, authors, webref) = ('', [], '')
            #authors
            for nametag in mc.find_all('name'):
                name = ''
                for gn in nametag.find_all('given-names'):
                    name = gn.text.strip()
                for sn in nametag.find_all('surname'):
                    name += ' ' + sn.text.strip()
                authors.append(name)
            #title
            for at in mc.find_all('article-title'):
                #title = at.text.strip()
                title = cleanformulas(at)
            #webreference
            for comment in mc.find_all('comment'):
                webref += comment.text.strip()
            for dic in mc.find_all('date-in-citation'):
                webref += dic.text
            refs.append([('x', refno + '%s: %s, %s' % (', '.join(authors), title, webref))])
        #commun
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : ['commun']}):
            (title, authors, date) = ('', [], '')
            #authors
            for nametag in mc.find_all('name'):
                name = ''
                for gn in nametag.find_all('given-names'):
                    name = gn.text.strip()
                for sn in nametag.find_all('surname'):
                    name += ' ' + sn.text.strip()
                authors.append(name)
            #title
            for at in mc.find_all('source'):
                #title = at.text.strip()
                title = cleanformulas(at)
            #date
            for year in mc.find_all('year'):
                date = year.text
            refs.append([('x', refno + '%s: %s, %s' % (', '.join(authors), title, date))])            
        #other
        for mc in ref.find_all('element-citation', attrs = {'publication-type' : 'other'}):
            (doi, recid, arxiv) = ('', '', '')
            #INSPIRE links
            inspirelink = ''
            for el in mc.find_all('ext-link', attrs = {'ext-link-type' : 'uri'}):
                if el.has_attr('xlink:href'):
                    link = el['xlink:href']
                    if re.search('inspirehep.net.*IRN', link):
                        irn = re.sub('.*\D', '', link)
                        #inspire2 for recid in search_pattern(p='970__a:SPIRES-' + irn):
                        #inspire2    inspirelink += ', https://old.inspirehep.net/record/%i' % (recid)
                        #inspire2 el.decompose()
                    elif re.search('inspirehep.net.*recid', link):
                        recid = re.sub('.*\D', '', link)
                        inspirelink += ', https://old.inspirehep.net/record/%s' % (recid)
                        el.decompose()
                    elif re.search('inspirehep.net', link):
                        el.decompose()
                    elif re.search('arxiv.org', link):
                        arxiv = re.sub(' ', '', el.text.strip())
                        arxiv = re.sub('^\[', '', arxiv)
                        arxiv = re.sub('(\d)\]$', r'\1', arxiv)
                        if re.search('^\d{4}\.\d', arxiv):
                            arxiv = 'arXiv:' + arxiv
                        elif re.search('ar[xX]iv\:[a-z\-]+\/\d',  arxiv):
                            arxiv = arxiv[6:]
                        el.decompose()
            #missing spaces?
            for bold in mc.find_all('bold'):
                bt = bold.text.strip()
                bold.replace_with(' %s ' % (bt))
            #DOI
            for pi in mc.find_all('pub-id', attrs = {'pub-id-type' : 'doi'}):
                doi = pi.text.strip()
                pi.replace_with(', DOI: %s' % (doi))
            #all together
            reference = [('x', refno + cleanformulas(mc))]
            if doi:
                reference.append(('a', 'doi:'+doi))
            if recid:
                reference.append(('0', str(recid)))
            if arxiv:
                reference.append(('r', arxiv))
            if doi or recid or arxiv:
                if lt: reference.append(('o', re.sub('\D', '', lt)))
            refs.append(reference)
    return refs

#quick check whether volume is to old
def quickcheck(jnl, vol):
    if jnl == 'particles' and vol < 4: #normal run
        return False
    elif jnl == 'sensors' and vol < 21: #normal run
        return False
    elif jnl == 'axioms' and vol < 10: #normal run ARTID
        return False
    elif jnl == 'mathematics' and vol < 9: #normal run
        return False
    elif jnl == 'symmetry' and vol < 13: #normal run ARTID
        return False
    elif jnl == 'galaxies' and vol < 9: #normal run
        return False
    elif jnl == 'condensedmatter' and vol < 6: #normal run
        return False
    elif jnl == 'applsci' and vol < 11: #k5crontab
        return False
    elif jnl == 'physics' and vol < 3: #normal run
        return False
    elif jnl == 'quantumrep' and vol < 3: #normal run ARTID?
        return False
    elif jnl == 'universe' and vol < 7: #normal run
        return False
    elif jnl == 'instruments' and vol < 5: #normal run ARTID
        return False
    elif jnl == 'entropy' and vol < 23: #normal run
        return False
    elif jnl == 'atoms' and vol < 9: #normal run
        return False
    elif jnl == 'information' and vol < 12: #normal run ARTID
        return False
    elif jnl == 'photonics' and vol < 8-2:#normal run
        return False
    
    elif jnl == 'foundations' and vol < 0: #normal run
        return False

    elif jnl == 'fractalfract' and vol < 5-2:#normal run
        return False
    elif jnl == 'nanomaterials' and vol < 11-2: #k5crontab
        return False

    else:
        return True


    
if not os.path.isdir(tmppath):
    os.system('mkdir %s' % (tmppath))
print 'connect to ftp://download.mdpi.com' 
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
srv = pysftp.Connection(host="download.mdpi.com", username="mdpi_public_ftp", password="j7kzfbf9RDiJnEuX", port=9922, cnopts=cnopts)
srv.cwd('MDPI_corpus')
srv.cwd(jnl)
issuesonserver = []
for vol in srv.listdir():
    for iss in srv.listdir(vol):
        issuesonserver.append('%s/%s' % (vol, iss))
issueslocal = []
for iss in issuesonserver[-numberofissues:]:
    print 'get %s from ftp://download.mdpi.com' % (iss)
    localfilename = '%s/%s' % (tmppath, re.sub('.*\/', '', iss))
    srv.get(iss, localfilename)
    issueslocal.append(localfilename)

for localfilename in issueslocal:
    print 'read %s' % (localfilename)
    journalfeed = tarfile.open(localfilename, 'r')
    journalfeed.extractall(path=tmppath)#, numeric_owner=3770)
    journalfeed.close()


prerecs = []
for voldir in os.listdir(tmppath):
    if re.search('volume', voldir):
        for issdir in os.listdir(os.path.join(tmppath, voldir)):            
            for artdir in os.listdir(os.path.join(tmppath, voldir, issdir)):
                for artfile in os.listdir(os.path.join(tmppath, voldir, issdir, artdir)):
                    if not re.search('xml$', artfile):
                        continue
                    rec = {'jnl' : jnl.title(), 'tc' : 'P', 'keyw' : [], 'aff' : [], 'auts' : [],
                           'note' : [], 'refs' : [], 'col' : []}
                    rec['artfilename'] = os.path.join(tmppath, voldir, issdir, artdir, artfile)
                    if rec['artfilename'] in done:
                        print '   %s in done' % (artfile)
                        continue
                    rec['vol'] = re.sub('\D', '', voldir)
                    rec['iss'] = re.sub('\D', '', issdir)
                    if jnl == 'proceedings':
                        rec['jnl'] = 'MDPI Proc.'
                        rec['tc'] = 'C'
                        rec['cnum'] = cnum
                    elif jnl == 'psf':
                        rec['jnl'] = 'Phys.Sci.Forum'
                        rec['tc'] = 'C'
                        rec['cnum'] = cnum
                    elif jnl == 'condensedmatter':
                        rec['jnl'] = 'Condens.Mat.'
                    elif jnl == 'physics':
                        rec['jnl'] = 'MDPI Physics'
                    elif jnl == 'quantumrep':
                        rec['jnl'] = 'Quantum Rep.'
                    elif jnl == 'fractalfract':
                        rec['jnl'] = 'Fractal Fract.'
                    elif jnl == 'applsci':
                        rec['jnl'] = 'Appl.Sciences'
                    prerecs.append(rec)
    
recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artfilename'])
    keepit = True
    inf = codecs.EncodedFile(codecs.open(rec['artfilename'], mode='rb'), 'utf8')
    article = BeautifulSoup(''.join(inf.readlines()), features="lxml")
    inf.close()
    for meta in article.find_all('article-meta'):
        #DOI
        for aid in meta.find_all('article-id', attrs = {'pub-id-type' : 'doi'}):
            rec['doi'] = aid.text.strip()
            #checkdone    
            if rec['doi'] in done and not rec['doi'] in missingpubnotes:
                print '  %s already in done'  % (rec['doi'])
                keepit = False
        #date
        for pd in  meta.find_all('pub-date', attrs = {'pub-type' : 'epub'}):
            for year in pd.find_all('year'):
                rec['date'] = year.text.strip()
            for month in pd.find_all('month'):
                rec['date'] += '-' + month.text.strip()
            for day in pd.find_all('day'):
                rec['date'] += '-' + day.text.strip()
            #checkdate
            if rec['date'] < stampofstartdate and not rec['doi'] in missingpubnotes:
                print '  %s is older than %s' % (rec['date'], stampofstartdate)
                keepit = False
        #article type
        for ac in meta.find_all('article-categories'):
            for subj in ac.find_all('subject'):
                subjt = subj.text.strip()
                if re.search('[a-zA-Z]', subjt):
                    rec['note'].append(subjt)
                if subjt in ['Review']:
                    if not 'R' in rec['tc']:
                        rec['tc'] += 'R'
                elif subjt in ['Conference Report']:
                    rec['tc'] = 'C'
                elif subjt in ['Editorial']:
                    keepit = False
        if keepit:
            #title # xml:lang="en" ?
            for tg in meta.find_all('title-group'):
                for at in tg.find_all(['article-title', 'title']):
                    rec['tit'] = cleanformulas(at)
                for st in tg.find_all('subtitle'):
                    rec['tit'] += ': %s' % (cleanformulas(st))
            #year
            for pd in  meta.find_all('pub-date', attrs = {'pub-type' : 'collection'}):
                for year in pd.find_all('year'):
                    rec['year'] = year.text.strip()
            #volume
            for vol in meta.find_all('volume'):
                rec['vol'] = vol.text.strip()        
            #issue
            for iss in meta.find_all('issue'):
                rec['issue'] = iss.text.strip()
            #pages
            for p1 in meta.find_all('fpage'):
                rec['p1'] = p1.text.strip()
            for p2 in meta.find_all('lpage'):
                rec['p2'] = p2.text.strip()
            if not 'p1' in rec.keys():
                for p1 in meta.find_all('elocation-id'):
                    rec['p1'] = p1.text.strip()
            #license
            for permissions in meta.find_all('permissions'):
                for licence in permissions.find_all('license', attrs = {'license-type' : 'open-access'}):
                    for el in licence.find_all('ext-link', attrs = {'ext-link-type' : 'uri'}):
                        if el.has_attr('xlink:href'):
                            rec['license'] = {'url' : el['xlink:href']}
            #keywords
            for kwg in meta.find_all('kwd-group'):
                for kw in kwg.find_all('kwd'):
                    rec['keyw'].append(kw.text.strip())         
            #abstract
            for abstract in meta.find_all('abstract'):
                rec['abs'] = ''
                for p in abstract.find_all('p'):
                    rec['abs'] += cleanformulas(p)
            #emails
            emails = {}
            for an in meta.find_all('author-notes'):
                for cor in an.find_all('corresp'):
                    for email in cor.find_all('email'):
                        emails[cor['id']] = email.text.strip()
            #affiliations
            for aff in meta.find_all('aff'):
                for label in aff.find_all(['label', 'email']):
                    label.decompose()
                afftext = aff.text.strip()
                if aff.has_attr('id'):
                    rec['aff'].append('%s= %s' % (aff['id'], re.sub('[\n\t\r]', ' ', afftext)))
                else:
                    rec['aff'].append('%s' % (re.sub('[\n\t\r]', ' ', afftext)))
            #authors and collaboration
            for contrib in meta.find_all('contrib', attrs = {'contrib-type' : 'author'}):
                #authors
                for name in contrib.find_all('name'):
                    for sn in name.find_all('surname'):
                        authorname = sn.text.strip()
                    for gn in name.find_all('given-names'):
                        authorname += ', %s' % (gn.text.strip())
                    #ORCID
                    for cid in contrib.find_all('contrib-id', attrs = {'contrib-id-type' : 'orcid'}):
                        authorname += re.sub('.*\/', ', ORCID:', cid.text.strip())
                    #Email
                    if not re.search('ORCID:', authorname):
                        for xref in contrib.find_all('xref', attrs = {'ref-type' : 'corresp'}):
                            if xref['rid'] in emails.keys():
                                authorname += ', EMAIL:' + emails[xref['rid']]
                        if not re.search('EMAIL:', authorname):
                            for adr in contrib.find_all('address'):
                                for email in adr.find_all('email'):
                                    authorname += ', EMAIL:' + email.text.strip()
                    rec['auts'].append(authorname)
                    #Affiliation
                    for xref in contrib.find_all('xref', attrs = {'ref-type' : 'aff'}):
                        rec['auts'].append('=%s' % (xref['rid']))
                #collaboration
                for coll in contrib.find_all('collab'):
                    #safety check if authors are under collaboration
                    authorsundercoll = False
                    for bla in coll.find_all('contrib', attrs = {'contrib-type' : 'author'}):
                        authorsundercoll = True
                    if authorsundercoll:
                        for inst in coll.find_all('institution'):
                            rec['col'].append(inst.text.strip())
                    else:
                        for email in coll.find_all('email'):
                            email.decompose()
                        rec['col'].append(coll.text.strip())
            #references
            for rl in article.find_all('ref-list'):
                rec['refs'] = get_references(rl)
            print '  ', rec.keys()
            recs.append(rec)
            #copy pdf
            pdffilename = re.sub('xml$', 'pdf', rec['artfilename'])
            if os.path.isfile(pdffilename):
                doi1 = re.sub('[\(\)\/]', '_', rec['doi'])                
                os.system('mv %s %s/%s.pdf' % (pdffilename, pdfpath, doi1))
            print '    copied pdf file'                          

#write to disc
numofchunks = (len(recs)-1) / chunksize + 1
for chunk in range(numofchunks):
    xmlfilename = '%s-%02i_of_%i.xml' % (jnlfilename, chunk + 1, numofchunks)
    xmlf = os.path.join(xmldir, xmlfilename)
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(recs[chunk*chunksize:(chunk+1)*chunksize], xmlfile, publisher, xmlfilename[:-4])
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = '%s\n' % (xmlfilename)
    print ' + wrote %s' % (line)
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
    

#cleanup
for rec in prerecs:
    donefilename = re.sub('\/tmp', '\/done\/'+jnl, rec['artfilename'])
    targetdir = re.sub('(.*)\/.*', r'\1', donefilename)
    if not os.path.isdir(targetdir):
        os.system('mkdir -p '+targetdir)
    if not os.path.isdir(donefilename):
        os.system('mv %s %s' % (rec['artfilename'], donefilename))
print 'moved %i xml-files to done' % (len(prerecs))
os.system('rm -rf %s' % (tmppath))
            
    
