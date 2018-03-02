# converts Springer xml files into dok format
# writes abs and ref files

import os
import xml.dom.minidom
import urllib
import ejlmod2
#import Recode
import time
import re
import sys
import codecs

#reload(Recode)
sprdir = '/afs/desy.de/group/library/publisherdata/springer'
#sprdir = '/home/data/SPRINGER'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
#xmldir = '/afs/desy.de/user/s/schwenn/inspire/ejl'
publisher = 'Springer'
cyear = time.localtime().tm_year - 1         # current year - 1
#cday = time.localtime().tm_yday
cday = sys.argv[1]
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


# uninteresting journals:


jw = ['00153', '11105', '00426', '10853']


#INSPIRE convention instead of DPBN as in springer.py
jc = {'00006': ['aaca', 'Adv.Appl.Clifford Algebras'],
      '00023': ['ahp', 'Annales Henri Poincare'],
      '13324': ['anmp', 'Anal.Math.Phys.'],
      '00159': ['aar', 'Astron.Astrophys.Rev.'],
      '11443': ['al', 'Astron.Lett.'],
      '11444': ['ar', 'Astron.Rep.'],
      '11755': ['ab', 'Astrophys.Bull.'],
      '00339': ['apa', 'Appl.Phys.'], #HAL
      '00340': ['apb', 'Appl.Phys.'], #HAL
      '10509': ['ass', 'Astrophys.Space Sci.'],
      '7395': ['assp', 'Astrophys.Space Sci.Proc.'],
      '10511': ['ast', 'Astrophysics'],
      '11953': ['blpi', 'Bull.Lebedev Phys.Inst.'],
      '11954': ['brasp', 'Bull.Russ.Acad.Sci.Phys.', 'Izv.Ross.Akad.Nauk Ser.Fiz. '],
      '13538': ['bjp', 'Braz.J.Phys.'],
      '11534': ['cejp', 'Central Eur.J.Phys.'], # stopped 2014
      '00220': ['cmp', 'Commun.Math.Phys.'],
      '11470': ['cmmp', 'Comput.Math., Math.Phys.'],
      '11434': ['csb', 'Chin.Sci.Bull.'],
      '11446': ['dok', 'Dokl.Phys.'],
      '10050': ['epja', 'Eur.Phys.J.'],
      '10051': ['epjb', 'Eur.Phys.J.'],
      '10052': ['epjc', 'Eur.Phys.J.'],
      '10053': ['epjd', 'Eur.Phys.J.'],
      '13129': ['epjh', 'Eur.Phys.J.'],
      '13360': ['epjp', 'Eur.Phys.J.Plus'],
      '11734': ['epjst', 'Eur.Phys.J.ST'],
      '10582': ['czjp', 'Czech.J.Phys.'], # stopped 2006
      '00601': ['fbs', 'Few Body Syst.'],
      '11467': ['fpc', 'Front.Phys.(Beijing)'],
      '10686': ['ea', 'Exper.Astron.'],
      '10701': ['fp', 'Found.Phys.'],
      '10702': ['fpl', 'Found.Phys.Lett.'], # stopped 2006
      '10714': ['grg', 'Gen.Rel.Grav.'],
      '12267': ['gc', 'Grav.Cosmol.'],
      '10751': ['hypfin', 'Hyperfine Interact.'],
      '10740': ['hite', 'High Temperature', 'Teplofizika Vysokikh Temperatur'],
      '12648': ['ijp', 'Indian J.Phys.'],
      '10786': ['iet', 'Instrum.Exp.Tech.'],
      '10773': ['ijtp', 'Int.J.Theor.Phys.'],
      '11958': ['jcp', 'J.Contemp.Phys.', 'Izv.Akad.Nauk Arm.SSR Fiz.'],
      '11447': ['jetp', 'J.Exp.Theor.Phys.', 'Zh.Eksp.Teor.Fiz.'],
      '10723': ['jgc', 'J.Grid Comput.'],
      '10909': ['jltp', 'J.Low.Temp.Phys.'],
      '11448': ['jtpl', 'JETP Lett.', 'Pisma Zh.Eksp.Teor.Fiz.'],
      '13130': ['jhep', 'JHEP'],
      '40042': ['jkps', 'J.Korean Phys.Soc.'],
      '10958': ['jms', 'J.Math.Sci.', 'Zap.Nauchn.Semin.'],
      '10853': ['jmsme', 'J.Mater.Sci.'],
      '11490': ['lasp', 'Laser Phys.'], # stopped 2012
      '11005': ['lmp', 'Lett.Math.Phys.'],
      '11040': ['mpag', 'Math.Phys.Anal.Geom.'],
      '11018': ['mt', 'Meas.Tech.'],
      '11972': ['mupb', 'Moscow Univ.Phys.Bull.'],
      '11452': ['plpr', 'Plasma Phys.Rep.', 'Fiz.Plasmy'],
      '11450': ['pan', 'Phys.At.Nucl.', 'Yad.Fiz.'],
      '11496': ['ppn', 'Phys.Part.Nucl.', 'Fiz.Elem.Chast.Atom.Yadra'],
      '11497': ['ppnl', 'Phys.Part.Nucl.Lett.', 'Pisma Fiz.Elem.Chast.Atom.Yadra'],
      '11451': ['ptss', 'Sov.Phys.Solid State', 'Fiz.Tverd.Tela'],
      '12043': ['pramana', 'Pramana'],
      '11182': ['rpj', 'Russ.Phys.J.', 'Izv.Vuz.Fiz.'],
      '11503': ['rjmp', 'Russ.J.Math.Phys.'],
#      '11425': ['sica', 'Sci.China A'],
      '11425': ['sica', 'Sci.China Math.'],
#      '11433': ['sicg', 'Sci.China G'],
      '11433': ['sicg', 'Sci.China Phys.Mech.Astron.'],
      '11207': ['soph', 'Solar Phys.'],#HAL
      '11214': ['ssr', 'Space Sci.Rev.'],
      '11232': ['tmp', 'Theor.Math.Phys.', 'Teor.Mat.Fiz.'],
      '11454': ['tp', 'Tech.Phys.'],
      '11455': ['tpl', 'Tech.Phys.Lett.'],
      '00016': ['pip', 'Phys.Perspect.'],
      '40509': ['qsmf', 'Quant.Stud.Math.Found.'],
      '40010': ['pnisia', 'Proc.Nat.Inst.Sci.India (Pt.A Phys.Sci.)'],
      '41365': ['nst', 'Nucl.Sci.Tech.'],
       '0426': ['stmp', 'Springer Tracts Mod.Phys.'],
       '5304': ['lnp', 'Lect.Notes Phys.'],
       '0304': ['lnm', 'Lect.Notes Math.'],
       '0361': ['spprph', 'Springer Proc.Phys.'], 
      '10533': ['spprma', 'Springer Proc.Math.'], #Lieferung
      '10781': ['fias', 'FIAS Interdisc.Sci.Ser.'],
      '10502': ['fimono', 'Fields Inst.Monogr.'], #Fields Institute Monographs
      '10503': ['ficomm', 'Fields Inst.Commun.'], #Fields Institute Communications
       '8389': ['nophsc', 'Nonlin.Phys.Sci.'], # stopped 2013?
       '4813': ['prmaph', 'Prog.Math.Phys.'],
       '0840': ['grtecoph', 'Graduate Texts Contemp.Phys.'], # stopped 2005
       '6001': ['futhph', 'Fundam.Theor.Phys.'],
       '0720': ['thmaph', 'Theor.Math.Phys.'], #???
       '0848': ['asasli', 'Astron.Astrophys.Lib.'],
       '5267': ['paacde', 'Part.Accel.Detect.'],
       '4308': ['adteph', 'Adv.Texts Phys.'], # stopped 2007
       '3052': ['acph', 'Accel.Phys.'], # stopped 1998
       '4890': ['eist', 'Einstein Studies'], #stopped 2012
       '5664': ['assl', 'Astrophys.Space Sci.Libr.'],
       '6316': ['mpstud', 'Math.Phys.Stud.'],
       '8431': ['gtip', 'Grad.Texts Math.'],
      '11006': ['matnot', 'Math.Notes'],
      '41781': ['csbg', 'Comput.Softw.Big Sci.'],
      '10967': ['jrnc', 'J.Radioanal.Nucl.Chem.'],
      '40485': ['epjti', 'EPJ Tech.Instrum.'],
      '41114': ['lrr', 'Living Rev.Rel.'],
      '8790' : ['sprthe', 'BOOK']}

#folgende Zeile unbeding loeschen
#jc = {'0304': ['lnm', 'Lect. Notes Math. ']}

collapseWs = re.compile('[\n \t]+')

def getAllText(anynode):
    text = []
    def recursive(n):
        t1 = ((n.nodeType == n.TEXT_NODE and n.data) or "")
        if t1:
            if n.parentNode.nodeName in ('Subscript', 'Superscript'):
                t1 = '(' + t1 + ')'
        text.append(t1)
#        text.append((n.nodeType == n.TEXT_NODE and n.data) or "")
#        try:
#            text.append((n.tagName == 'IMG'  and n.attributes['ALT'].value) or "")
#        except: pass
        for c in n.childNodes: recursive(c)
    recursive(anynode)
    textall = ''.join(text)
    textall = collapseWs.sub(' ', textall)
    return textall

def getAllTextplusTeX(anynode):
    text = []
    def recursive(n):
        t1 = ((n.nodeType == n.TEXT_NODE and n.data) or "")
        if t1:
            if n.parentNode.nodeName in ('Subscript') and collapseWs.sub(' ', t1) != ' ':
                t1 = '$_{' + t1 +'}$'                
            elif n.parentNode.nodeName in ('Superscript') and collapseWs.sub(' ', t1) != ' ':
                t1 = '$^{' + t1 +'}$'
            elif  n.parentNode.nodeName == 'Emphasis':
                if n.parentNode.parentNode.nodeName in ('Subscript'):
                    t1 = '$_{' + t1 +'}$'               
                elif n.parentNode.parentNode.nodeName in ('Superscript') and collapseWs.sub(' ', t1) != ' ':
                    t1 = '$^{' + t1 +'}$'
        text.append(t1)
        for c in n.childNodes: 
            if c.nodeName == 'EquationSource':
                if c.attributes["Format"].value == 'TEX':
                    text.append(re.sub('\$\$','$',c.childNodes[0].data))
            else:
                recursive(c)
    recursive(anynode)
    textall = ''.join(text)
    textall = collapseWs.sub(' ', textall)
    textall = re.sub(' +\$(\^|_)',r'$\1',textall)
    textall = re.sub(' *\$\$','',textall)
    textall = re.sub('(_|\^)\{([^\}]*?)\}_\{',r'\1{\2',textall)
    return textall

def xmlExtract():
    """ extracts dok record of single article (or chapter) from xml file"""
    
#    artxml = xml.dom.minidom.parse(file)
    rec = {}
    #type code
    rec['tc'] = 'P'
    #ArticleCategory esp. Editorials
    for node in artxml.getElementsByTagName('ArticleCategory'):
        if not rec.has_key('note'): 
            rec['note'] = []
        try:
            rec['note'].append(node.firstChild.data)
            if node.firstChild.data == 'Review':
                rec['tc'] = 'R'
        except:
            pass
    rec['jnl'] = jc[jnr][1]
    if rec['jnl'] == '41114':
        rec['tc'] = 'R'
    if rec['jnl'] == '8790':
        rec['tc'] = 'T'
    if len(jc[jnr]) > 2:
        rec['jnl2'] = jc[jnr][2]
	
    rec['vol'] = vol
    if re.search('ISU=',d3):
        rec['issue'] = iss
        print 'ISSUE=',rec['issue']
#    collapseWs = re.compile('(?<=\S)[ \t]+')
#    collapseWs = re.compile('[\n \t]+')
    ti = ''
    #ti = getAllText(artxml.getElementsByTagName('ArticleTitle')[0])
    ti = artxml.getElementsByTagName('ArticleTitle') # (FS)
    cti = artxml.getElementsByTagName('ChapterTitle') # Chapter title
    if ((ti == []) and (cti != [])): # (FS)
        ti = artxml.getElementsByTagName('ChapterTitle') # (FS)
        try:
            rec['vol'] = getAllText(artxml.getElementsByTagName('BookVolumeNumber')[0]) # get Volumbenumber from XML-file for books(FS)
        except:
            rec['vol'] = ''
            rec['vol'] = re.sub('\-','',getAllText(artxml.getElementsByTagName('BookElectronicISBN')[0])) # get Volumbenumber from XML-file for books(FS)             
    if isbook: ti =cti
    ti = getAllTextplusTeX(ti[0]) # (FS)
    run_title = artxml.getElementsByTagName('RunningTitle')
    if run_title !=[]: ti = getAllTextplusTeX(run_title[0]) # for lnp 
    rec["tit"] = ti
    for node in artxml.getElementsByTagName('AuthorGroup'):
        auths = node.getElementsByTagName('Author')
        authors = []
        aff = ''
        nachname = []
        for au in auths:
            affo = aff
            try:
                aff = au.attributes["AffiliationIDS"].value
                aff = aff.replace(' ', '; =')
            except:
                aff = ''
            if (aff != affo) and affo:
                authors.append('=' + affo)
                
            lname = au.getElementsByTagName('FamilyName')[0].firstChild.data
            aut = (lname)
            fnames = []
            try:
                for fnnode in au.getElementsByTagName('GivenName'):
                    fnames.append(fnnode.firstChild.data)
                    fname = ' '.join(fnames)
                    fname = fname.replace('. ', '.')
                    aut = (lname + ', ' + fname)
            except:
                print 'No GivenName for %s' % (lname)
            #orcid 
            try:
                orcid = au.attributes["ORCID"].value
                orcid = re.sub('.*\/', ', ORCID:', orcid)
                aut = aut + orcid
            except:
                pass
            authors.append(aut)
    try:
        if aff:
            authors.append('=' + aff)
    except:
        pass
    try:
        rec["auts"] = authors
    except:
        rec["auts"] = []
        
    rec['aff'] = affil = []
    for node in artxml.getElementsByTagName('Affiliation'):
        affid = node.attributes["ID"].value
	if ("ID" in affid): continue # (FS) Editor has AffIDxx but 'real' author has Affxx 
        orgname = ''
        try:
            orgname = node.getElementsByTagName('OrgDivision')[0].firstChild.data + ' - '
        except:
	    pass  
#            continue #(FS) I commented this because there there are OrgName's without OrgDivision's
        try:
            orgname += node.getElementsByTagName('OrgName')[0].firstChild.data
        except:
            continue
        if orgname.find('University of ') > -1:
            orgname = orgname.replace('University of ', '')
            if orgname.find(' and ') > -1:
                orgname = orgname.replace(' and ', ' U. and ')
            else:
                orgname += ' U.'
        #(FS) a lot of informations have been ignored so far
        try:
            for node2 in node.getElementsByTagName('OrgAddress')[0].childNodes:
                if node2.hasChildNodes():                    
                    orgname += ', '+ node2.firstChild.nodeValue
        except:
            print "problems with OrgAddress!"
        orgname = orgname.replace('University', 'U.')
        orgname = orgname.replace(',', ' -')
        affil.append(affid + "= " + orgname)
    rec['aff'] = affil
    try:
        for node in artxml.getElementsByTagName('ArticleNote'):
            arxiv = node.getElementsByTagName("RefSource")[0].firstChild.data
            if (re.search('[0-9]{4}\.[0-9]{4}',arxiv)!=None):
                rec['arxiv'] = arxiv
    except:
        print "no arxiv-bull (don't worry)"
    rec["year"] = ''
    try:
        rec["doi"] = artxml.getElementsByTagName('ArticleDOI')[0].firstChild.data
    except: #(FS) for Books: Chapter=Article 
        rec["doi"] = artxml.getElementsByTagName('ChapterDOI')[0].firstChild.data
    for cdate in artxml.getElementsByTagName('CoverDate'):
        rec["year"] = str(cdate.getElementsByTagName('Year')[0].firstChild.data)
    if artxml.getElementsByTagName('CoverDate')==[]: # (FS) For books: get year from Copyright
	    rec["year"] = str(artxml.getElementsByTagName('CopyrightYear')[0].firstChild.data)
    try:
        rec["p1"] = artxml.getElementsByTagName('ArticleFirstPage')[0].firstChild.data
    except:
    	try: #(FS) for Books: Chapter=Article
        	rec["p1"] = artxml.getElementsByTagName('ChapterFirstPage')[0].firstChild.data
    	except:
        	rec['p1'] = ''
    try:
    	#rec["seq"] = artxml.getElementsByTagName('ArticleSequenceNumber')[0].firstChild.data
        #ArticleSequenceNumber nicht immer gleich ArticleCitationID
    	rec["seq"] = artxml.getElementsByTagName('ArticleCitationID')[0].firstChild.data
        if jnr == '13130': 
            rec["seq"] = '%03i' % (int(rec["seq"]))
        if rec.has_key('p1'):
            del rec['p1']
    except: 
        rec["seq"] = '' 
        try:
            print 'articleID instead of pagination', rec['doi']
            rec["p2"] = artxml.getElementsByTagName('ArticleLastPage')[0].firstChild.data
            if jnr in ['13130', '10050', '10052', '10053', '10051', '13360', '00159', '11433']: #JHEP allways starts with page 1
                rec['pages'] = rec["p2"]
                print 'e[%s] ' % (rec['jnl'])
                if rec['jnl']=='JHEP':
                    rec['p1'] = re.sub('.*\)','',rec['doi'])
                    del rec['p2']
                elif (rec['jnl']=='Astron.Astrophys.Rev.'):
                    rec['p1'] = re.sub('^0*','',rec['doi'].split("-")[-2])
                    del rec['p2']
                elif (rec['jnl']=='Eur. Phys. J.'):
                    rec['p1'] = rec['seq']
                    del rec['p2']
                else:
                    rec['p1'] =  artxml.getElementsByTagName('ArticleCitationID')[0].firstChild.data
                    del rec['p2']
            print rec['p1']
        except:
            try: #(FS) for Books: Chapter=Article
                rec["p2"] = artxml.getElementsByTagName('ChapterLastPage')[0].firstChild.data
            except:
                rec['p2'] = ''
    try:
        if jnr in ['10050','10051','10052','10053','13129']:
            if jnr == '10050': rec["vol"] = 'A'
            elif jnr == '10051': rec["vol"] = 'B'
            elif jnr == '10052': rec["vol"] = 'C'
            elif jnr == '10053': rec["vol"] = 'D'
            elif jnr == '13129': rec["vol"] = 'H'
            rec["vol"] += artxml.getElementsByTagName('VolumeIDStart')[0].firstChild.data
        elif jnr == '00039': 
            rec["vol"] = 'A' + artxml.getElementsByTagName('VolumeIDStart')[0].firstChild.data
        elif jnr == '00040': 
            rec["vol"] = 'B' + artxml.getElementsByTagName('VolumeIDStart')[0].firstChild.data
        print "VOLUME",rec["vol"],jnr
    except: 
        pass
    abst = artxml.getElementsByTagName('Abstract')
    try:
        abst = artxml.getElementsByTagName('Abstract')
        abstxt = getAllTextplusTeX(abst[0].getElementsByTagName('Para')[0])
        #print '[ABS]',abstxt
        #abstxt = abstxt.encode('utf8')
        rec["abs"] = abstxt.replace(';', ',').replace('"', '\'')
    except:
        rec["abs"] = ''
    for kwg in artxml.getElementsByTagName('KeywordGroup'):
        try:
            hd = kwg.getElementsByTagName('Heading')[0].firstChild.data
        except: continue
        k = []
        if hd[0:4] == 'PACS':
            for kw in kwg.getElementsByTagName('Keyword'):
                pacs = kw.firstChild.data.split(' ')[0][0:8]
                #print "  1|"+pacs+"|\n"
                k.append(pacs)
            rec["pacs"] = k
        if hd in['K',  'Keywords']:
            for kw in kwg.getElementsByTagName('Keyword'):
                k.append(getAllTextplusTeX(kw))
            rec["keyw"] = k
    try:
        for hist in artxml.getElementsByTagName('ArticleHistory'):
            for date in hist.getElementsByTagName('OnlineDate'):
                datey = date.getElementsByTagName('Year')[0].firstChild.data
                datem = date.getElementsByTagName('Month')[0].firstChild.data
                dated = date.getElementsByTagName('Day')[0].firstChild.data
                if len(datem) < 2: datem = '0'+datem
                if len(dated) < 2: dated = '0'+dated
                rec['date'] = '%s-%s-%s' % (datey,datem,dated)
    except:
        print 'could not extract publication date'
        
    
    for anote in artxml.getElementsByTagName('ArticleNote'):
        try:
            if anote.getElementsByTagName('Heading')[0].firstChild.data in ['PACS', 'PACS Nos']:
                ap = anote.getElementsByTagName('SimplePara')[0].firstChild.data
                rec["pacs"] = re.split(' *; *',str(ap))
        except:
            pass
        for snote in anote.getElementsByTagName('SimplePara'):
            #snotedata = snote.firstChild.data
            snotedata = getAllText(snote)
            #Errata
            if re.search('The online version of the original article can be found at', snotedata):
                for rnote in snote.getElementsByTagName('RefSource'):
                    erratumdoi = re.sub('.*dx.doi.org.', '', rnote.firstChild.data)
                    rec['tit'] += ' [doi:%s]' % erratumdoi
            elif re.search('Original.*published in', snotedata) or re.search('Translated from', snotedata):
                print '+', snotedata, '+'
                secondpubnote = re.sub('.*published in *', '', snotedata)
                secondpubnote = re.sub('.*Translated from *', '', secondpubnote)
                snotedataparts = re.split(' *, *', secondpubnote)
                for part in snotedataparts[1:]:
                    if re.search('Vol. ', part):
                        rec['vol2'] = re.sub('Vol. ', '', part)
                    elif re.search('No. ', part):
                        rec['issue2'] = re.sub('No. ', '', part)
                    elif re.search('pp\.? *', part):
                        rec['p1p22'] = re.sub('pp\.? *', '', re.sub('\.', '', part))
                    elif re.search('\d\d\d\d', part):
                        rec['year2'] = part
            else:
                if not rec.has_key('note'): 
                    rec['note'] = []
                rec['note'].append(snotedata)
    #references
    rec['refs'] = []
    for citation in artxml.getElementsByTagName('Citation'):
        reftext = ''
        doitext = ''
        for BibUnstructured in citation.getElementsByTagName('BibUnstructured'):
            reftext = getAllText(BibUnstructured)
        if len(reftext) < 20:
            reftext = getAllText(citation)
        if not re.search('10\.\d+\/', reftext):            
            for doi in citation.getElementsByTagName('Occurrence'):
                if doi.hasAttribute('Type') and doi.getAttribute('Type') == 'DOI':
                    reftext = reftext + ', DOI: ' + getAllText(doi)
        rec['refs'].append([('x', reftext)])
    
    #for citation in artxml.getElementsByTagName('BibUnstructured'):

    #special case JHEP
    if jnr in ['13130']:
        rec['vol'] = '%s%02i' % (rec['year'][2:],int(rec['issue']))
        del rec['issue']
    return rec

def xmlExtractBook(): # (FS) extract book information. Just slightly different to artcile
    """ extracts dok record of a whole Book from xml file"""
    
#    artxml = xml.dom.minidom.parse(file)
    rec = {}
    rec['editordoesexist'] = False
    ti = ''
    ti = getAllTextplusTeX(artxml.getElementsByTagName('BookTitle')[0]) # (FS)
    rec["tit"] = ti
    rec['tc'] = 'B'
    #proceedings: 
    if jnr in ['7395','0361']: rec['tc'] = 'K'
    rec['jnl'] = jc[jnr][1]
    try:
        rec['vol'] = getAllText(artxml.getElementsByTagName('BookVolumeNumber')[0]) # get Volumbenumber from XML-file for books(FS)
    except:
        rec['vol'] = ''
        rec['vol'] = re.sub('\-','',getAllText(artxml.getElementsByTagName('BookElectronicISBN')[0])) # get Volumbenumber from XML-file for books(FS)
    for node in artxml.getElementsByTagName('AuthorGroup'):
        auths = node.getElementsByTagName('Author')
        authors = []
        aff = ''
        nachname = []
        for au in auths:
            affo = aff
            try:
                aff = au.attributes["AffiliationIDS"].value
                aff = aff.replace(' ', '; =')
            except:
                aff = ''
            if (aff != affo) and affo:
                authors.append('=' + affo)
            fnames = []
            for fnnode in au.getElementsByTagName('GivenName'):
                fnames.append(fnnode.firstChild.data)
            fname = ' '.join(fnames)
            fname = fname.replace('. ', '.')
            lname = au.getElementsByTagName('FamilyName')[0].firstChild.data
            aut = (lname + ', ' + fname)
            authors.append(aut)
    try:
        if aff:
            authors.append('=' + aff)
    except:
        pass
    try:
        rec["auts"] = authors
    except:
        rec["auts"] = ''
    rec['aff'] = affil = []
    for node in artxml.getElementsByTagName('Affiliation'):
        affid = node.attributes["ID"].value
        orgname = ''
        try:
            orgname = node.getElementsByTagName('OrgDivision')[0].firstChild.data + ' - '
        except:
            pass
#                continue #(FS) I commented this because there there are OrgName's without OrgDivision's
        try:
            orgname += node.getElementsByTagName('OrgName')[0].firstChild.data
        except:
            continue
        if orgname.find('University of ') > -1:
            orgname = orgname.replace('University of ', '')
            if orgname.find(' and ') > -1:
                orgname = orgname.replace(' and ', ' U. and ')
            else:
                orgname += ' U.'
        orgname = orgname.replace('University', 'U.')
        orgname = orgname.replace(',', ' -')
        affil.append(affid + "= " + orgname)
    rec['aff'] = affil
    if (artxml.getElementsByTagName('EditorGroup').length > 0):
        rec['editordoesexist'] = True
	for node in artxml.getElementsByTagName('EditorGroup'): # try to find editor information
            auths = node.getElementsByTagName('Editor')
            authors = []
            aff = ''
            nachname = []
            for au in auths:
                affo = aff
                try:
                    aff = au.attributes["AffiliationIDS"].value
                    aff = aff.replace(' ', '; =')
                except:
                    aff = ''
                if (aff != affo) and affo:
                    authors.append('=' + affo)
                fnames = []
                for fnnode in au.getElementsByTagName('GivenName'):
                    fnames.append(fnnode.firstChild.data)
                fname = ' '.join(fnames)
                fname = fname.replace('. ', '.')
                lname = au.getElementsByTagName('FamilyName')[0].firstChild.data
                aut = (lname + ', ' + fname + ' (ed.)')
                authors.append(aut)
        try:
            if aff:
                authors.append('=' + aff)
        except:
            pass
        try:
            rec["auts"] = authors
        except:
            rec["auts"] = ''
        rec['aff'] = affil = []
        for node in artxml.getElementsByTagName('Affiliation'):
            affid = node.attributes["ID"].value
	    print '----> ' + affid
	    if ("ID" not in affid):
	        continue # (FS) Editor has AffIDxx but 'real' author has Affxx
	        print '      skipped'
            orgname = ''
            try:
                orgname = node.getElementsByTagName('OrgDivision')[0].firstChild.data + ' - '
            except:
                pass
#            continue #(FS) I commented this because there there are OrgName's without OrgDivision's
            try:
                orgname += node.getElementsByTagName('OrgName')[0].firstChild.data
            except:
                continue
            if orgname.find('University of ') > -1:
                orgname = orgname.replace('University of ', '')
                if orgname.find(' and ') > -1:
                    orgname = orgname.replace(' and ', ' U. and ')
                else:
                    orgname += ' U.'
            orgname = orgname.replace('University', 'U.')
            orgname = orgname.replace(',', ' -')
            affil.append(affid + "= " + orgname)
        rec['aff'] = affil
	
	
    rec["year"] = str(artxml.getElementsByTagName('CopyrightYear')[0].firstChild.data)
    try:
        odatenode = artxml.getElementsByTagName('OnlineDate')[0]
        oyear = odatenode.getElementsByTagName('Year')[0].firstChild.data
        omonth = odatenode.getElementsByTagName('Month')[0].firstChild.data.zfill(2)
        oday = odatenode.getElementsByTagName('Day')[0].firstChild.data.zfill(2)
        rec["onlinedate"] = oyear + '/' + omonth + '/' + oday
    except: pass
    rec['p1'] = 'pp.'
    rec['p2'] = ''
    try:
    	rec["doi"] = artxml.getElementsByTagName('BookDOI')[0].firstChild.data
    except: 
    	rec["doi"] = ''
    rec["typ"] = ''
    abst = artxml.getElementsByTagName('Abstract')
    try:
        abst = artxml.getElementsByTagName('Abstract')
        abstxt = getAllTextplusTeX(abst[0].getElementsByTagName('Para')[0])
        abstxt = abstxt.encode('utf8')
        rec["abs"] = abstxt.replace(';', ',').replace('"', '\'')
    except:
        rec["abs"] = ''
    for kwg in artxml.getElementsByTagName('KeywordGroup'):
        try:
            hd = kwg.getElementsByTagName('Heading')[0].firstChild.data
        except: continue
        k = []
        if hd[0:4] == 'PACS':
            for kw in kwg.getElementsByTagName('Keyword'):
                pacs = kw.firstChild.data.split(' ')[0][0:8]
                k.append(pacs)
            rec["pacs"] = ', '.join(k)
        if hd == 'Keywords':
            for kw in kwg.getElementsByTagName('Keyword'):
                k.append(getAllTextplusTeX(kw))
            rec["keyw"] = k
    
    for anote in artxml.getElementsByTagName('ArticleNote'):
        try:
            if anote.getElementsByTagName('Heading')[0].firstChild.data == 'PACS':
                ap = anote.getElementsByTagName('SimplePara')[0].firstChild.data
                rec["pacs"] = str(ap).replace(';', ',')
        except:
            pass

        
    return rec





for d1 in os.listdir(sprdir):
        df2 = os.path.join(sprdir, d1)
	print df2
        if not os.path.isdir(df2):
            continue
    #if df.find('PUB') == -1: continue
        if ((df2.find('BSE') == -1) and (df2.find('JOU') == -1)): continue
#	if (df2.find('BSE') == 1): continue
    #for d1 in os.listdir(df):                                 # journal
        jnr = d1[4:]
        if jnr in jw:
            print jnr + ' uninteresting'
            continue
        if not jc.has_key(jnr):
            print 'journal skipped: ' + jnr
            os.system('echo "check www.springer.com/journal/%s" | mail -s "[SPRINGER] unknown journal" %s' % (jnr, 'florian.schwennsen@desy.de'))
            continue
   #     df2 = os.path.join(df, d1)
        for d2 in os.listdir(df2):                                   # volume
            d2s = d2.replace('VOL=', '').split('.')
            try:
                vol = d2s[1]
                yr1 = int(d2s[0])
            except:
                vol = d2s[0]
                yr1 = cyear + 1
            try:
                if yr1 < cyear:                             # old journal
                    print 'old journal skipped: ', jnr, vol, yr1, '\n'
                    #continue
            except:
                pass
            df3 = os.path.join(df2, d2)

# OnlineFirst has no issue directory -> create fake dir # (FS) the same for books

            dfOF = os.path.join(df3, str(cday))
            for d3 in os.listdir(df3):
                if ('ART' in d3) or ('CHP' in d3):
		    print ' fake ' + d3
                    os.renames(os.path.join(df3,d3), os.path.join(dfOF, d3))
            editordoesexist = True # (FS)
	    isbook = False # (FS) 
            if "BOK" in d2: # entry for the whole book
                print 'book!'
#folgende Zeile unbeding loeschen
#		if not "978" in d2: continue
		isbook = True
                for d3 in os.listdir(df3):
                    df4 = os.path.join(df3, d3)
                    if "BookFrontmatter" in d3:
                        artfile = os.path.join(df4, os.listdir(df4)[0])
                        #(FS): workaround to only work on xml-files
                        if not re.search('xml$',artfile): artfile = os.path.join(df4, os.listdir(df4)[1])
                        if not re.search('xml$',artfile): artfile = os.path.join(d4, os.listdir(d4)[2])
                        artxml = xml.dom.minidom.parse(artfile)
                        rec = xmlExtractBook()
                        vol = rec['vol']
                        editordoesexist = rec['editordoesexist']
                        jrnl = jc[jnr][0] + vol
                        #jrnl = 'TEST-FS-'+jrnl
                        xmlf = os.path.join(xmldir,jrnl+ '.'+str(cday)+'.xml')
                        #xmlfile = open(xmlf,'w')
                        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
			print "tit=", rec['tit']
                        ejlmod2.writeXML([rec],xmlfile,'Springer')
                        xmlfile.close()
                        #retrival
                        retfiles_text = open(retfiles_path,"r").read()
                        line = jrnl+ '.'+str(cday)+'.xml'+ "\n"
                        if not line in retfiles_text: 
                            retfiles = open(retfiles_path,"a")
                            retfiles.write(line)
                            retfiles.close()
                        if isbook: pass
			pacs = []
                        kw = []
            #if editordoesexist: # (FS) for books: take chapters only if they are not all by the same author(s)
            if editordoesexist or not editordoesexist: # (FS) for books: take chapters only if they are not all by the same author(s)
	        for d3 in os.listdir(df3):                               # issue
		    if "matter" in d3: continue #(FS) for books: there are no chapters in Front- and Backmatter
                    iss = d3.replace('ISU=', '')
                    iss = iss.replace('PRT=', '') #(FS) for books: part~issue 
		    jrnl = jc[jnr][0] + vol + '.' + iss
		    if isbook: jrnl = jc[jnr][0] + vol #(FS) write a book completely in one file
                    jrnl = jrnl.replace("JournalOnlineFirst", "OF")
                    print jrnl
                    #if "OF" in jrnl and jnr not in ('10714', '10052', '13130'):
                    if "OF" in jrnl:
                        print "wait until print version for this journal."
                    else:
                        str(cday)
                        #jrnl = 'TEST-FS-'+jrnl
                        xmlf = os.path.join(xmldir,jrnl+ '.'+str(cday)+'.xml')
                        if isbook:
                            xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='ab'),'utf8')
                            xmlfile = open(xmlf,'a')
                        else:
                            xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
                            xmlfile = open(xmlf,'w')
                        recs = {}
    
                        df4 = os.path.join(df3, d3)
                        nr = 1
                        for d4 in os.listdir(df4):                   # article xml file
		            if "matter" in d4: continue #(FS) for books: there are no chapters in Front- and Backmatter
                            d5 = os.path.join(df4, d4)
                            print 'd4=', d4
                            artfile = False
                            for d6 in os.listdir(d5):
                                if re.search('.xml$', d6):
                                    artfile = os.path.join(d5, d6)
                                    break
                            if not artfile:
                                for d6 in os.listdir(d5):
                                    if re.search('.xml.meta$', d6):
                                        artfile = os.path.join(d5, d6)
                                        break
                            rec = {}
                            #try:
                            if True:    
                                print artfile 
                                artxml = xml.dom.minidom.parse(artfile)
                                rec = xmlExtract()
                                if isbook: 
                                    rec['tc'] = 'S'
                                    #proceedings:
                                    if jnr in ['7395','0361', '10533']: 
                                        rec['tc'] = 'C'
                                    elif jnr in ['5304', '0304']:
                                        rec['tc'] = 'PS'
                                if not editordoesexist:
                                    rec['note'] = [ 'NUR HAUPTAUFNAHME - KEINE EINZELAUFNAHMEN' ]
                                #known conference?
                                knownconferences = {'23rd European Conference on Few' : 'C16-08-08.2',
                                                    'Light Cone 2016' : 'C16-09-05.9',
                                                    'New Observables in Quarkonium' : 'C16-02-28'}
                                if rec.has_key('note'):
                                    for kc in knownconferences.keys():
                                        for note in rec['note']:
                                            if re.search(kc, note):
                                                rec['cnum'] = knownconferences[kc]
                                                rec['tc'] = 'C'
			        #JHEP does provide page numbers which could act as keys
                                #if jnr in ['13130', '10052', '10050', '10053', '13360', '00159', '10053']:
                                recs[rec['doi']] = rec
                                #else:
                                #    recs[rec['p1']] = rec
                                if d2 == 'JournalOnlineFirst':
                                    if rec.has_key('p2'):
                                        rec['pages'] = rec['p2']
                                        del rec['p2']
                                    if rec.has_key('p1'):
                                        del rec['p1']
                                    nr += 1
                            #except xml.parsers.expat.ExpatError:
                            #    print 'artfile:'+artfile
#                           #     print rec
                            #    continue

                            print ' doi: '+rec['doi']
                        keys =  recs.keys()
                        keys.sort()
                        recssorted = []
                        for  key in keys:
                            print nr
                            recssorted.append(recs[key])
                            nr += 1
                        ejlmod2.writeXML(recssorted,xmlfile,'Springer')

                        xmlfile.close()
                        #retrival
                        retfiles_text = open(retfiles_path,"r").read()
                        line = jrnl+ '.'+str(cday)+'.xml'+ "\n"
                        if not line in retfiles_text: 
                            retfiles = open(retfiles_path,"a")
                            retfiles.write(line)
                            retfiles.close()
                        if isbook: pass
                        pacs = ''
                        kw = ''










