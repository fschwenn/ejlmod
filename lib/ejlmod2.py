# -*- coding: utf-8 -*-
import xml.dom.minidom
import re
import os
import subprocess
import datetime
import platform
import unicodedata

from collclean_lib import coll_cleanforthe
from collclean_lib import coll_clean710
from collclean_lib import coll_split
try:
    # needed to remove the print-commands from /usr/lib/python2.6/site-packages/refextract/references/engine.py
    from refextract import  extract_references_from_string
except:
    #for running on PubDB
    print 'could not import extract_references_from_string'


#from collclean import clean710

#mappings for refferences in JSON to MARC 
mappings = [('doi', 'a'),
            ('collaborations', 'c'),
            ('document_type', 'd'),
            ('author', 'h'),
            ('isbn', 'i'),
            ('texkey', 'k'),
            ('misc', 'm'),
            ('journal_issue', 'n'),
            ('label', 'o'),
            ('linemarker', 'o'),
            ('reportnumber', 'r'),
            ('journal_reference', 's'),
            ('title', 't'),
            ('urls', 'u'),
            ('raw_ref', 'x'),
            ('year', 'y')]

#auxiliary function to strip lines
def tgstrip(x): return x.strip()

def kapitalisiere(string):
    if re.search('[a-z]', string):
        return string
    else:
        acronyms = ['LHC', 'CFT', 'QCD', 'QED', 'QFT', 'ABJM', 'NLO', 'LO', 'NNLO', 'IIB', 'IIA', 'MSSM', 'NMSSM', 'SYM', 'WIMP', 'ATLAS', 'CMS', 'ALICE', 'RHIC', 'DESY', 'HERA', 'CDF', 'D0', 'BELLE', 'BABAR', 'BFKL', 'DGLAP', 'SUSY', 'QM', 'UV', 'IR', 'BRST', 'PET', 'GPS', 'NMR', 'XXZ', 'CMB', 'LISA', 'CPT', 'KEK', 'TRIUMF', 'PHENIX', 'VLBI', 'NGC', 'SNR', 'HESS', 'AKARI', 'GALEX', 'ESO', 'J-PARC', 'CERN', 'XFEL', 'FAIUR', 'ILC', 'CLIC', 'SPS', 'BNL', 'CEBAF', 'SRF', 'LINAC', 'HERMES', 'ZEUS', 'H1', 'GRB', 'GSI']
        word_list = re.split(' +', string)
        final = [word_list[0].capitalize()]
        for word in word_list[1:]:
            if word.upper() in acronyms:
                final.append(word.upper())
            elif len(word) > 3:
                final.append(word.capitalize())
            else:
                final.append(word.lower())
        return " ".join(final)

#FS: try to get arXiv-number from ADS for some journals
def arXivfromADS(rec):
    adslink = 'http://adsabs.harvard.edu/doi/' + rec['doi']
    print 'try '+adslink+' to get arXiv-number'
    for adsline in os.popen("lynx -source \"%s\"|grep citation_arxiv_id" % (adslink)).readlines():
        if re.search('arxiv',adsline):
            rec['arxiv'] = re.sub('.*content="(.*)".*', r'\1', adsline).strip()
            if rec.has_key('note'):
                if type(rec['note']) == type(['Liste']):
                    rec['note'].append('arXiv number from ADS (not from publisher!)')
                else:
                    rec['note'] = [rec['note'],'arXiv number from ADS (not from publisher!)']
            else:
                rec['note'] = ['arXiv number from ADS (not from publisher!)']
    return


#FS:
#add experiment line for existing collaboration
#and try to find experiment in title
colexpdictfilename = '/afs/desy.de/user/l/library/lists/expcolFS'
colexpdictfile = open(colexpdictfilename,'r')
colexpdict = {}
expexpdict = {}
for colexpline in colexpdictfile.readlines():
    parts = re.split(';',colexpline.strip())
    colexpdict[re.sub(' *Collabo.*','',parts[0]).upper()] = parts[1:]
    if not re.search(' and ',parts[0]):
        expexpdict[re.sub(' *Collabo.*','',parts[0])] = re.sub(' *experiment.*','',parts[1])
colexpdictfile.close()

def findexperiment(rec):
    if rec.has_key('col'):
        #print "COL=",rec['col']
        collaboration = re.sub(' *Collabo.*','',rec['col']).upper()
        if colexpdict.has_key(collaboration):
            rec['exp'] = colexpdict[collaboration]
            #print "EXP=",rec['exp']
    else:
        experiments = []
        for exp in expexpdict.keys():
            if re.search('(\W|^)'+exp+'($|\W)',rec['tit']):
            #if (exp != 'DO') and re.search(exp,rec['tit']):
                experiments.append(expexpdict[exp] + '')
        if len(experiments) > 0:
            rec['exp'] = experiments
            print "EXP=",rec['exp']
    return


#FS:
#get abstract from arXiv (e.g. Intl. Press;)
def getabsfromarxiv(rec):
    absdir = '/afs/desy.de/group/library/publisherdata/abs/'
    bull = re.sub('.*\: ','',rec['arxiv'])
    print " get abstract for %s from arXiv" % (bull)
    arxivpage = os.popen("lynx -source \"http://export.arxiv.org/abs/%s\"" % (bull)).read().replace('\n',' ')
    abstract = re.sub('.*<span class=\"descriptor\">Abstract\:<\/span> *(.*) *<\/blockquote>.*',r'\1',arxivpage )
    abstract = re.sub('  +',' ',abstract)
    rec['abs'] = re.sub(';',',',abstract)
    return



#new stuff: writeXML
inspirefc = {'e':'Experiment-HEP', 'i':'Instrumentation', 
             'b':'Accelerators', 'x':'Experiment-Nucl', 
             'n':'Theory-Nucl', 'c':'Computing', 
             'a':'Astrophysics', 'p':'Phenomenology-HEP', 
             'o':'General Physics', 'g':'Gravitation and Cosmology', 
             'l':'Lattice', 'm':'Math and Math Physics', 
             'o':'Other', 'q':'General Physics', 
             's' : 'Data Analysis and Statistics', 't':'Theory-HEP'}
inspiretc = {'P':'Published', 'C':'ConferencePaper', 
             'R':'Review', 'T':'Thesis', 
             'B':'Book', 'S': 'BookChapter', 
             'K': 'Proceedings', 'O': 'Note', 
             'L' : 'Lectures', 'I':'Introductory'}


#translating HTML entities
htmlentity = re.compile(r'&#x.*?;')
def lam(x):                                                
    x  = x.group()
    return unichr(int(x[3:-1], 16))



def validxml(string):
    if type(string) == type(()):
        return tuple([validxml(part) for part in string])
    elif type(string) == type([]):
        return [validxml(part) for part in string]
    else:
        #print '--->',string
        string = htmlentity.sub(lam, string)
        string = re.sub('&','&amp;',string)
        string = re.sub('>','&gt;',string)
        string = re.sub('<','&lt;',string)
        string = re.sub('"','&quot;',string)
        string = re.sub('\'','&apos;',string)
        return re.sub('  +', ' ', string)


def marcxml(marc,liste):
    if len(marc) < 5: marc += ' '
    if len(marc) < 5: marc += ' '
    #print marc,liste
    xmlstring = ' <datafield tag="%s" ind1="%s" ind2="%s">\n' % (marc[:3],marc[3],marc[4])
    for tupel in liste:
        if tupel[1] is not None:
            if type(tupel[1]) == type([]):
                for element in tupel[1]:
                    if element != '':
                        xmlstring += '  <subfield code="%s">%s</subfield>\n' % (tupel[0], validxml(element).strip())
            else:
                if tupel[1] != '':
                    try:
                        xmlstring += '  <subfield code="%s">%s</subfield>\n' % (tupel[0],validxml(tupel[1]).strip())
                    except:
                        print 'ERROR in function "marcxml"'
                        print marc, liste
    xmlstring += ' </datafield>\n'
    #avoid empty xml entries
    if re.search('<subfield code="[a-z]">',xmlstring):
        return xmlstring
    else:
        return ''

#translates '27 February 2013' to '2013-02-27'
def datetodate(date):
    months = ['JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
    months2 = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    parts = re.split(' +', date.strip())
    if len(parts) == 3:
        try:
            return '%4i-%02i-%02i' % (int(parts[2]), months.index(parts[1].upper())+1, int(parts[0]))
        except:
            return '%4i-%02i-%02i' % (int(parts[2]), months2.index(parts[1].upper())+1, int(parts[0]))
    elif len(parts) == 2:
        try:
            return '%4i-%02i' % (int(parts[1]), months.index(parts[0].upper())+1)
        except:
            try:
                return '%4i-%02i' % (int(parts[1]), months2.index(parts[0].upper())+1)
            except:
                return '%4i' % (int(parts[1]))


def writeXML(recs,dokfile,publisher):
    dokfile.write('<collection>\n')
    i = 0
    for rec in recs:
        if rec['jnl'] in ['Astron.Astrophys.', 'Mon.Not.Roy.Astron.Soc.', 
                          'Astronom.J.', 'Adv.Astron.', 'Astron.Nachr.']:
            arXivfromADS(rec)

        liste = []
        i += 1
        print rec
        if rec.has_key('arxiv') and re.search('v[0-9]+$', rec['arxiv']):
            rec['arxiv'] = re.sub('v[0-9]+$', '', rec['arxiv'])
        xmlstring = '<record>\n'
        #direct marc first (retinspire takes the first DOI?)
        if rec.has_key('MARC'):
            for marc in rec['MARC']:
                xmlstring += marcxml(marc[0], marc[1])
        #
        if rec.has_key('tit'):
            xmlstring += marcxml('245',[('a',kapitalisiere(rec['tit'])), ('9',publisher)])
        if rec.has_key('otits'):
            for otit in rec['otits']:
                xmlstring += marcxml('246', [('a',kapitalisiere(otit)), ('9',publisher)])
        if rec.has_key('transtit'):
            xmlstring += marcxml('242',[('a',kapitalisiere(rec['transtit'])), ('9',publisher)])
        if rec.has_key('langauge'):
            print rec
            xmlstring += marcxml('041',[('a',rec['langauge'])])
        if rec.has_key('abs'):
            xmlstring += marcxml('520',[('a',rec['abs']), ('9',publisher)])
        if rec.has_key('keyw'):
            for kw in rec['keyw']:
                #xmlstring += marcxml('6531',[('a',kw), ('9','publisher')])
                xmlstring += marcxml('6531',[('a',kw), ('9','author')])
        if rec.has_key('authorkeyw'):
            for kw in rec['authorkeyw']:
                xmlstring += marcxml('6531',[('a',kw), ('9','author')])
        if rec.has_key('jnl'):
            liste = [('p',rec['jnl'])]
            if rec.has_key('year'):
                liste.append(('y',rec['year']))
            elif rec.has_key('date'):
                liste.append(('y',re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])))
            if rec.has_key('p1'):
                if rec.has_key('p2'):
                    if rec['p1'] != rec['p2']:
                        liste.append(('c',rec['p1']+'-'+rec['p2']))
                    else:
                        liste.append(('c',rec['p1']))
                    if not rec.has_key('pages'):
                        try:
                            if rec['p1'] != rec['p2']:
                                xmlstring += marcxml('300',[('a',str(int(rec['p2'])-int(rec['p1'])+1))])
                        except:
                            pass
                else:
                    liste.append(('c',rec['p1']))
            elif rec.has_key('seq'):
                liste.append(('c',rec['seq']))
            elif rec.has_key('wsp_seq'):
                liste.append(('c',rec['wsp_seq']))
            elif rec.has_key('artnum'):
                liste.append(('c',rec['artnum']))
            if rec.has_key('vol'): liste.append(('v',rec['vol']))
            if rec.has_key('pbnrep'): liste.append(('r',rec['pbnrep']))
            if rec.has_key('issue'): liste.append(('n',rec['issue']))
            if rec.has_key('cnum'): liste.append(('w',rec['cnum']))
            xmlstring += marcxml('773',liste)
        if rec.has_key('jnl2') and rec.has_key('vol2'):
            liste = [('p',rec['jnl2'])]
            if rec.has_key('year2'):
                liste.append(('y',rec['year2']))
            elif rec.has_key('date'):
                liste.append(('y',re.sub('.*([12]\d\d\d.*', r'\1', rec['date'])))
            if rec.has_key('p1p22'):
                rec['p1p22'] = re.sub('–', '-', rec['p1p22'])
                liste.append(('c',rec['p1p22']))
            if rec.has_key('vol2'): liste.append(('v',rec['vol2']))
            if rec.has_key('issue2'): liste.append(('n',rec['issue2']))
            if rec.has_key('cnum'): liste.append(('w',rec['cnum']))
            xmlstring += marcxml('773',liste)
        if rec.has_key('bookseries'):
            xmlstring += marcxml('490', rec['bookseries'])
        if rec.has_key('isbns'):
            for isbn in rec['isbns']:
                xmlstring += marcxml('020', isbn)
        elif rec.has_key('isbn'):
            xmlstring += marcxml('020',[('a', re.sub('\-', '', rec['isbn']))])
        if rec.has_key('doi'):
            xmlstring += marcxml('0247',[('a',rec['doi']), ('2','DOI'), ('9',publisher)])
            #special euclid:
            if re.search('^20.2000\/euclid\.', rec['doi']):
                xmlstring += marcxml('035', [('9', 'EUCLID'), ('a', rec['doi'][8:])])
        if rec.has_key('hdl'):
            xmlstring += marcxml('0247',[('a',rec['hdl']), ('2','HDL'), ('9',publisher)])
        elif len(liste) > 2 or rec.has_key('isbn') or rec.has_key('isbns'):
            pseudodoi = '20.2000/'+re.sub(' ','_','-'.join([tup[1] for tup in liste]))
            if rec.has_key('isbn'):
                pseudodoi += '_' + rec['isbn']
            elif rec.has_key('isbns'):
                for tupel in rec['isbns'][0]:
                    if tupel[0] == 'a':
                        pseudodoi += '_' + tupel[1]
            xmlstring += marcxml('0247',[('a',pseudodoi), ('2','NODOI'), ('9',publisher)])
        if rec.has_key('pages'):
            if type(rec['pages']) == type('999'):
                xmlstring += marcxml('300',[('a',rec['pages'])])
            elif type(rec['pages']) == type(u'999'):
                xmlstring += marcxml('300',[('a',rec['pages'])])
            elif type(rec['pages']) == type(999):
                xmlstring += marcxml('300',[('a',str(rec['pages']))])
        if rec.has_key('date'):
            if re.search('[a-zA-Z] ', rec['date']):
                rec['date'] = datetodate(rec['date'])
            recdate = re.sub('\/','-',rec['date'])
            if re.search('\d\d\-\d\d\-\d\d\d\d', recdate):
                parts = re.split('\-', recdate)
                recdate = '%s-%s-%s' % (parts[2], parts[1], parts[0])
            parts = re.split('\-', recdate)
            if len(parts) > 1:
                if len(parts[1]) == 1:
                    parts[1] = '0' + parts[1]
                if len(parts) > 2 and len(parts[2]) == 1:
                    parts[2] = '0' + parts[2]
                recdate = '-'.join(parts)
            if 'B' in rec['tc']:
                xmlstring += marcxml('260',[('c', recdate), ('t', 'published'), ('b', publisher)])
            else:
                xmlstring += marcxml('260',[('c', recdate), ('t', 'published')])
        elif rec.has_key('year'):
            if 'B' in rec['tc']:
                xmlstring += marcxml('260',[('c',rec['year']), ('t', 'published'), ('b', publisher)])
            else:
                xmlstring += marcxml('260',[('c',rec['year']), ('t', 'published')])
        if rec.has_key('tc'):
            for tc in rec['tc']:
                if tc != '':
                    xmlstring += marcxml('980',[('a',inspiretc[tc])])
        if rec.has_key('fc'):
            for fc in rec['fc']:
                xmlstring += marcxml('65017',[('a',inspirefc[fc]),('2','INSPIRE')])
        if rec.has_key('pacs'):
            for pacs in rec['pacs']:
                xmlstring += marcxml('084',[('a',pacs), ('2','PACS')])
        if rec.has_key('col'):
            if type(rec['col']) != type([]):
                rec['col'] = [rec['col']]
            newcolls = []
            for col in rec['col']:
                for original in coll_split(col):
                    (coll, author) = coll_cleanforthe(original)
                    coll = coll_clean710(coll)
                    newcolls.append(coll)
                    if author:
                        print 'found author%s in collaboration strin %s' % (author, original)
            for col in newcolls:
                xmlstring += marcxml('710',[('g',col)])
                if not rec.has_key('exp') and colexpdict.has_key(col):
                    xmlstring += marcxml('693',[('e',colexpdict[col])])
        if rec.has_key('arxiv'):
            if re.search('^[0-9]',rec['arxiv']):
                rec['arxiv'] = 'arXiv:'+rec['arxiv']
            xmlstring += marcxml('037',[('a',rec['arxiv']),('9','arXiv')])
            xmlstring += marcxml('980',[('a','arXiv')])
        if rec.has_key('rn'):
            for rn in rec['rn']:
                xmlstring += marcxml('037', [('a', rn)])
        if rec.has_key('exp'):
            xmlstring += marcxml('693',[('e',rec['exp'])])
        if rec.has_key('pdf'):
            xmlstring += marcxml('8564',[('u',rec['pdf']), ('y','Fulltext')])
        if rec.has_key('FFT'):
            xmlstring += marcxml('FFT',[('a',rec['FFT']), ('d','Fulltext'), ('t','INSPIRE-PUBLIC')])
        elif rec.has_key('fft'):
            xmlstring += marcxml('fft',[('a',rec['FFT']), ('d','Fulltext'), ('t','INSPIRE-PUBLIC')])
        if rec.has_key('link'):
            xmlstring += marcxml('8564',[('u', rec['link'])])
        if rec.has_key('licence'):
            entry = []
            if rec['licence'].has_key('statement'):
                entry.append(('a',rec['licence']['statement']))
            elif rec['licence'].has_key('url') and re.search('creativecommons.org', rec['licence']['url']):
                statement = re.sub('.*licen[cs]es', 'CC', rec['licence']['url']).upper()
                statement = re.sub('.LEGALCODE', '', statement)
                statement = re.sub('.DEED...', '', statement)
                entry.append(('a', re.sub('\/', '-', re.sub('\/$', '', statement))))
            if rec['licence'].has_key('url'):
                entry.append(('u',rec['licence']['url']))
            if rec['licence'].has_key('organization'):
                entry.append(('b',rec['licence']['organization']))
            if rec['licence'].has_key('material'):
                entry.append(('3',rec['licence']['material']))
            xmlstring += marcxml('540', entry)
        if rec.has_key('supervisor'):
            marc = '701'
            for autaff in rec['supervisor']:
                autlist = [('a',shapeaut(autaff[0]))]
                for aff in autaff[1:]:
                    if re.search('ORCID', aff):
                        autlist.append(('j', aff))
                    elif re.search('EMAIL', aff):
                        autlist.append(('m', re.sub('EMAIL:', '', aff)))
                    else:
                        autlist.append(('u', aff))
                xmlstring += marcxml(marc, autlist)
        if rec.has_key('autaff'):
            marc = '100'
            for autaff in rec['autaff']:
                if re.search('\([eE]d\.\)', autaff[0]):
                    autlist = [('a', shapeaut(re.sub(' *\([eE]d\.\) *','',autaff[0]))), ('e','ed.')]
                else:
                    autlist = [('a',shapeaut(autaff[0]))]
                for aff in autaff[1:]:
                    if re.search('ORCID', aff):
                        autlist.append(('j', aff))
                    elif re.search('EMAIL', aff):
                        autlist.append(('m', re.sub('EMAIL:', '', aff)))
                    else:
                        autlist.append(('v', aff))
                xmlstring += marcxml(marc, autlist)
                marc = '700'
        elif rec.has_key('auts'):
            affdict = {}
            tempaffs = []
            if rec.has_key('aff'):
                for aff in rec['aff']:
                    if re.search('=',aff):
                        parts = re.split('= *',aff)
                        affdict[parts[0]] = parts[1]
                    else:
                        tempaffs.append(('v',aff))
            #print affdict
            longauts = []
            rec['auts'].reverse()
            preventry = ' '
            for entry in rec['auts']:
                if entry == '':
                    continue
                #print '--', entry
                if entry[0] == '=':
                    if preventry[0] != '=':
                        tempaffs = []
                    affs = re.split('; ',entry)
                    affs.reverse()
                    for aff in affs:
                        if affdict.has_key(aff[1:]):
                            tempaffs.insert(0,('v',affdict[aff[1:]]))
                    #print tempaffs
                else:
                    if re.search('\([eE]d\.\)',entry):
                        aut = [('a', shapeaut(re.sub(' *\([eE]d\.\) *','',entry))), ('e','ed.')]
                    else:
                        author = shapeaut(entry)
                        aut = []
                        if re.search('CHINESENAME', author):
                            aut.append(('q', re.sub('.*, CHINESENAME: ', '', author)))
                            author = re.sub(', CHINESENAME.*', '', author)
                        elif re.search('ORCID', author):
                            aut.append(('j', re.sub('\.$', '', re.sub('.*, ',  '', author))))
                            author = re.sub(', ORCID.*', '', author)
                        elif re.search('EMAIL', author):
                            aut.append(('m', re.sub('.*, EMAIL:',  '', author)))
                            author = re.sub(', EMAIL.*', '', author)
                        aut.append(('a', author))
                    if (len(tempaffs) == 0) and (len(affdict) > 0):
                        tempaffs = [('v',affdict[affdict.keys()[0]])]
                    longauts.insert(0,aut+tempaffs)
                preventry = entry
            marc = '100'
            for aut in longauts:
                xmlstring += marcxml(marc,aut)
                marc = '700'
        if rec.has_key('refs'):
            print 'extracting %i refs for record %i of %i' % (len(rec['refs']),i,len(recs))
            for ref in rec['refs']:
                #print '  ->  ', ref
                if len(ref) == 1 and ref[0][0] == 'x':
                    try:
                        for ref2 in extract_references_from_string(ref[0][1], override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}"):
                            entryaslist = [('9','refextract')]
                            for key in ref2.keys():
                                for mapping in mappings:
                                    if key == mapping[0]:
                                        for entry in ref2[key]:
                                            entryaslist.append((mapping[1], entry))
                            xmlstring += marcxml('999C5',entryaslist)
                    except:
                        print 'UTF8 Problem in Referenzen'
                        ref01 = unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', ref[0][1])).encode('ascii','ignore'),'utf-8')
                        for ref2 in extract_references_from_string(ref01, override_kbs_files={'journals': '/opt/invenio/etc/docextract/journal-titles-inspire.kb'}, reference_format="{title},{volume},{page}"):
                            entryaslist = [('9','refextract')]
                            for key in ref2.keys():
                                for mapping in mappings:
                                    if key == mapping[0]:
                                        for entry in ref2[key]:
                                            entryaslist.append((mapping[1], entry))
                            xmlstring += marcxml('999C5',entryaslist)
                else:
                    xmlstring += marcxml('999C5',ref)
        xmlstring += marcxml('980',[('a','HEP')])
        #temporary informations used for selection process
        if rec.has_key('comments'):
            for comment in rec['comments']:
                xmlstring += marcxml('599',[('a',comment)])
        if rec.has_key('note'):
            for comment in rec['note']:
                xmlstring += marcxml('599',[('a',comment)])
        if rec.has_key('typ'):
            xmlstring += marcxml('599',[('a',rec['typ'])])
        xmlstring += '</record>\n'
        try:
            dokfile.write(xmlstring)
        except:
            dokfile.write(xmlstring.encode("utf8", "ignore"))
    dokfile.write('</collection>\n')
    return


def shapeaut(author):
    if not re.search(',', author):
        if re.search('(.*) (van den|van der|van de|de la) (.*)', author):
            author = re.sub('(.*) (van den|van der|van de|de la) (.*)',r'\2 \3, \1',author).strip()
        elif re.search('(.*) (van|van|de|von|del|du) (.*)', author):
            author = re.sub('(.*) (van|van|de|von|del|du) (.*)',r'\2 \3, \1',author).strip()
        else:
            author = re.sub('(.*) (.*)',r'\2, \1',author).strip()
    author = re.sub(' ([A-Z]) ',r' \1. ', author)
    author = re.sub(' ?([A-Z])$',r'\1.', author)
    author = re.sub('([A-Z] ?\.)[ \-]([A-Z] ?\.?)',r'\1\2', author)
    author = re.sub(', *', ', ', author.strip())
    if not re.search('[a-z]', author):
        author = author.title()
    return author

