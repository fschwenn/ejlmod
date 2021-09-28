# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest AIP-journals
# FS 2015-02-11

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

publisher = 'AIP'
typecode = 'P'
jnl = sys.argv[1]
vol = sys.argv[2]
jnlfilename = jnl+vol
cnum = False
if len(sys.argv) > 3: 
    iss = sys.argv[3]
    jnlfilename = jnl + vol + '.' + iss
if len(sys.argv) > 4:
    cnum = sys.argv[4]
    jnlfilename = jnl + vol + '.' + iss + '_' + cnum
if   (jnl == 'rsi'): 
    jnlname = 'Rev.Sci.Instrum.'
elif (jnl == 'jmp'):
    jnlname = 'J.Math.Phys.'
elif (jnl == 'chaos'):
    jnlname = 'Chaos'
elif (jnl == 'ajp'):
    jnlname = 'Am.J.Phys.'
elif (jnl == 'ltp'):
    jnlname = 'Low Temp.Phys.'
    jnlname2 = 'Fiz.Nizk.Temp.'
elif (jnl == 'php'):
    jnlname = 'Phys.Plasmas'
elif (jnl == 'adva'):
    jnlname = 'AIP Adv.'
elif (jnl == 'aipconf') or (jnl == 'aipcp') or (jnl == 'apc'):
    jnlname = 'AIP Conf.Proc.'
    jnl = 'apc'
    typecode = 'C'
elif (jnl == 'apl'):
    jnlname = 'Appl.Phys.Lett.'
elif (jnl == 'jap'):
    jnlname = 'J.Appl.Phys.'
elif (jnl == 'jcp'):
    jnlname = 'J.Chem.Phys.'
elif (jnl == 'phf'):
    jnlname = 'Phys.Fluids'
elif (jnl == 'jva'):
    jnlname = 'J.Vac.Sci.Tech.'
elif (jnl == 'jvb'):
    jnlname = 'J.Vac.Sci.Tech.'
elif (jnl == 'aqs'):
    jnlname = 'AVS Quantum Sci.'
elif (jnl == 'app'):
    jnlname = 'APL Photonics?'
elif (jnl == 'sci'):
    jnlname = 'Scilight?'
elif (jnl == 'pto'): #authors messy
    jnlname = 'Phys.Today'
    typecode = ''

    
    
tocfilname = '%s/%s.toc' % (tmpdir, jnlfilename)
urltrunk = 'http://aip.scitation.org/toc/%s/%s/%s?size=all' % (jnl,vol,iss)
if jnl in ['aqs']:
    urltrunk = 'https://avs.scitation.org/toc/%s/%s/%s?size=all' % (jnl,vol,iss)
print urltrunk
if not os.path.isfile(tocfilname):
    os.system('wget -T 300 -t 3 -q  -U "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0" -O %s "%s"' % (tocfilname, urltrunk))
    time.sleep(5)
inf = open(tocfilname, 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()), features="lxml")
inf.close()
#try:
#    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
#    time.sleep(3)
#except:
#    print "retry %s in 180 seconds" % (urltrunk)
#    time.sleep(180)
#    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))


def getarticle(href, sec, subsec, p1):
    artlink = 'http://aip.scitation.org%s' % (href)
    if jnl in ['aqs']:
        artlink = 'http://avs.scitation.org%s' % (href)
    artfilname = '%s/%s.%s' % (tmpdir, jnlfilename, re.sub('\W', '', p1))
    if not os.path.isfile(artfilname):
        os.system('wget -T 300 -t 3 -q -O %s "%s"' % (artfilname, artlink))
        time.sleep(10)
        if not os.path.getsize(artfilname):
            print 'retry %s' % (artlink)            
            time.sleep(120)
            os.system('wget -T 300 -t 3 -q  -U "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:39.0) Gecko/20100101 Firefox/39.0" -O %s "%s"' % (artfilname, artlink))
            time.sleep(10)
    inf = open(artfilname, 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()), features="lxml")
    inf.close()

#    try:
#        print artlink
#        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
#        time.sleep(3)
#    except:
#        print "retry %s in 180 seconds" % (artlink)
#        time.sleep(180)
#        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
    rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : iss, 'tc' : typecode, 'keyw' : [],
           'note' : [], 'auts' : [], 'aff' : [], 'p1' : p1}
    if jnl == 'jva':
        rec['vol'] = 'A%s' % (vol)
    elif jnl == 'jvb':
        rec['vol'] = 'B%s' % (vol)
    emails = {}
    if cnum:
        rec['cnum'] = cnum
    if sec:
        rec['note'].append(sec)
        if sec == 'NEW PRODUCTS':
            return {'auts' : False}
        elif sec == 'CONTRIBUTED REVIEW ARTICLES':
            rec['tc'] = 'R'
    if subsec:
        rec['note'].append(subsec)
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #keywords
            if meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'].strip())
            #date
            elif meta['name'] == 'dc.Date':
                rec['date'] = meta['content'] 
            #title
            elif meta['name'] == 'dc.Title':
                rec['tit'] = meta['content']
    #date
    if not 'date' in rec.keys():
        for div in artpage.body.find_all('div', attrs = {'class' : 'publicationContentEpubDate'}):
            rec['date'] = re.sub('.*: *', '', div.text.strip())
    #get rid of 'related articles' 
    for div in artpage.body.find_all('div', attrs = {'class' : 'related-articles'}):
        div.replace_with('')
    #check whether older date exists
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta['name'] == 'dc.onlineDate':
            if not rec.has_key('date') or meta['content'] < rec['date']:
                rec['date'] = meta['content'] 
    #title
    for header in artpage.body.find_all('header', attrs = {'class' : 'publicationContentTitle'}):
        for h2 in header.find_all('h2'):
            rec['tit'] = h2.text.strip()
        if not 'tit' in rec.keys():
            for h3 in header.find_all('h3'):
                rec['tit'] = h3.text.strip()
        if not 'tit' in rec.keys():
            for h1 in header.find_all('h1'):
                rec['tit'] = h1.text.strip()
        rec['tit'] = re.sub('\n* *Scilight relation icon', '', rec['tit'])
    #doi
    rec['doi'] = re.sub('\/doi\/', '', re.sub('\/doi\/full\/', '', re.sub('.doi.abs.', '', href)))
    #emails
    for authornotes in artpage.body.find_all('author-notes'):
        for p in authornotes.find_all('p', attrs = {'class' : 'first last'}):
            affnr = 'NOAFFNR'
            for sup in p.find_all('sup'):
                affnr =  re.sub('\)', '', sup.text)
            for a in p.find_all('a', attrs = {'class' : 'email'}):
                ats = a.text.strip()
                if not re.search('email.protect', ats):
                    emails[affnr] = re.sub('mailto:', '', )
    #affiliations
    for div in artpage.body.find_all('div', attrs = {'class' : 'affiliations-list hide'}):
        for li in div.find_all('li'):
            for sup in li.find_all('sup'):
                affnr =  re.sub('\)', '', sup.text)
                sup.replace_with('Aff%s= ' % affnr)
            for a in li.find_all('a', attrs = {'class' : 'email'}):
                emails[affnr] = re.sub('mailto:', '', a['href'])
            if not emails.has_key(affnr):
                rec['aff'].append(li.text)
    if not rec['aff']:
        for div in artpage.body.find_all('div', attrs = {'class' : 'affiliations-list list-unstyled hide'}):
            for li in div.find_all('li'):
                affnr = False
                for sup in li.find_all('sup'):
                    affnr =  re.sub('\)', '', sup.text)
                    sup.replace_with('Aff%s= ' % affnr)
                for a in li.find_all('a', attrs = {'class' : 'email'}):
                    emails[affnr] = re.sub('mailto:', '', a['href'])
                if affnr:
                    if not emails.has_key(affnr):
                        rec['aff'].append(li.text)
                else:
                    rec['aff'].append(li.text)
    #authors
    affnr = 2 + len(rec['aff'])
    for div in artpage.body.find_all('div', attrs = {'class' : 'entryAuthor'}):
        #for li in div.find_all('li', attrs = {'class' : 'author-affiliation hide'}):
        for li in div.find_all('li'):
            aff = li.text.strip()
            rec['aff'].append('Aff%s= %s' % (affnr, aff))
            li.string = str(affnr)
            li.wrap(artpage.new_tag('sup')).wrap(artpage.new_tag('span'))
            affnr += 1
            
        for span in div.find_all('span'):            
            affs = []
            for sup in span.find_all('sup'):
                affs += re.split(',', re.sub('\)', '', sup.text))
                sup.replace_with('')
            author = re.sub(' and *$', '', span.text.strip())
            author = re.sub(',', '', author)
            author = re.sub('[\n\r\t]', '', author)
            #author = re.sub('([A-Z]\.) ([A-Z]\.) ', r'\1\2 ', author)
            #author = re.sub('([A-Z]\.) ([A-Z]\.) ', r'\1\2 ', author)
            #author = re.sub('(.*) (.*)', r'\2, \1', author)            
            for a in span.find_all('a'):
                if a.has_attr('href') and re.search('orcid.org', a['href']):
                    author += re.sub('http.*orcid.org.', ', ORCID:', a['href'])
            for affi in range(len(affs)):
                if emails.has_key(affs[affi]):
                    if not re.search('ORCID', author) and re.search('@', emails[affs[affi]]):
                        author += ', EMAIL:%s' % (emails[affs[affi]])
                    affs[affi] = ''
            #chinese name
            if re.search(' \(.+\)', author):
                author = re.sub('(.*) *\((.*)\)(.*)', r'\1\3, CHINESENAME: \2', author)
            rec['auts'].append(author)                    
            for aff in affs:
                if aff:
                    rec['auts'].append('=Aff%s' % (aff))
    if len(rec['auts']) == 1 and not re.search('EMAIL', rec['auts'][0]) and emails.has_key('NOAFFNR'):
        if re.search('@', emails['NOAFFNR']):
            rec['auts'][0] += ', EMAIL:%s' % (emails['NOAFFNR'])
    #special case Physics Today
    if jnl == 'pto':
        rec['auts'] = []
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_author'}):
            rec['auts'].append(meta['content'])
    for div in artpage.body.find_all('div', attrs = {'class' : 'topic-list'}):
        for a in div.find_all('a'):
            kw = a.text.strip()
            if not kw in rec['keyw']:
                rec['keyw'].append(kw)
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'abstractSection abstractInFull'}):
        rec['abs'] = div.text.strip()
    if not rec.has_key('abs'):
        for div in artpage.body.find_all('div', attrs = {'class' : 'hlFld-Abstract'}):
            for div2 in div.find_all('div', attrs = {'class' : 'NLM_paragraph'}):
                rec['abs'] = div2.text.strip()
    if not rec.has_key('abs'):
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'dc.Description'}):
            rec['abs'] = meta['content']
    #references
    for div in artpage.body.find_all('div', attrs = {'class' : 'article-paragraphs'}):
        for h4 in div.find_all('h4'):
            if re.search('References', h4.text, re.IGNORECASE):
                rec['refs'] = []
                for li in div.find_all('li'):
                    for span in li.find_all('span'):
                        for a in span.find_all('a'):
                            if a.has_attr('href') and re.search('doi.org', a['href']):
                                rdoi = re.sub('htt.*doi.org.', ', DOI: ', a['href'])
                                a.replace_with(rdoi)
                            elif not re.search('arxiv.org', a['href']):
                                a.replace_with('')
                    rawref = li.text.strip()
                    if not rawref in ['Published by AIP Publishing.']:
                        rec['refs'].append([('x', regexpref.sub(' ', rawref))])
    if not 'refs' in rec.keys():
        for ol in artpage.body.find_all('ol'):
            rec['possiblerefs'] = []
            indicator = False
            for li in ol.find_all('li'):
                for a in li.find_all('a'):
                    if a.has_attr('href') and re.search('doi.org', a['href']):
                        rdoi = re.sub('htt.*doi.org.', ', DOI: ', a['href'])
                        a.replace_with(rdoi)
                        indicator = True
                    elif not re.search('arxiv.org', a['href']):
                        a.replace_with('')
                rawref = li.text.strip()
                if not rawref in ['Published by AIP Publishing.']:
                    rec['possiblerefs'].append([('x', regexpref.sub(' ', rawref))])
            if indicator:
                rec['refs'] = rec['possiblerefs']
            
            
    print '  ', rec['doi'] + ': ' + ' '.join(['%s[%i]' % (k, len(rec[k])) for k in rec.keys()])
    time.sleep(2)
    return rec
                
(sec, subsec) = (False, False)
tocheck = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'sub-section'}):
    for child in div.contents:
        if child.name == 'h5': 
            sec = child.text.strip()
        elif child.name == 'section':
            for child2 in child.contents:
                if type(child2) == type(child):
                    if child2.name == 'h6':
                        subsec = child2.text.strip()
                    elif child2.name == 'section':
                        for article in child2.find_all('article'):
                            for div2 in article.find_all('div', attrs = {'class' : 'art_title linkable'}):
                                (href, p1) = (False, False)
                                for a in article.find_all('a', attrs = {'class' : 'ref nowrap'}):
                                    href = a['href']
                                #articleID is not on indiviual article page (sic!)
                                for div3  in article.find_all('div', attrs = {'class' : 'meta-article'}):
                                    p1 = re.sub('.*, ([A-Z0-9]+) \(\d\d\d\d\);.*', r'\1', div3.text.strip())
                                if href and p1:
                                    tocheck.append((href, sec, subsec, p1))
                    elif child2.name == 'article':
                        for div2 in child2.find_all('div', attrs = {'class' : 'art_title linkable'}):
                            (href, p1) = (False, False)
                            for a in child2.find_all('a', attrs = {'class' : 'ref nowrap'}):
                                href = a['href']
                            #articleID is not on indiviual article page (sic!)
                            for div3  in child2.find_all('div', attrs = {'class' : 'meta-article'}):
                                p1 = re.sub('.*, ([A-Z0-9]+) \(\d\d\d\d\);.*', r'\1', div3.text.strip())
                            if href and p1:
                                tocheck.append((href, sec, subsec, p1))
                        
recs = []
i = 0
for (href, sec, subsec, p1) in tocheck:
    i += 1
    if href in ['/doi/full/10.1063/1.5019809']:
        print 'skip %s' % (href)
    else:
        print '---{ %i/%i }---{ %s %s %s %s }---' % (i, len(tocheck), href, sec, subsec, p1)
        if sec in ['From the Editor', "Readers' Forum", 'Issues and Events', 'Books',
                   'New Products', 'Obituaries', 'Quick Study', 'Back Scatter']:
            print '     skip "%s"' % (sec)
        else:
            rec = getarticle(href, sec, subsec, p1)
            if rec['auts']:
                recs.append(rec)
print '%i records for %s' % (len(recs), jnlfilename)


                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
