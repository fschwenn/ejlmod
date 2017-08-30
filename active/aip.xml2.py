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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
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
elif (jnl == 'aipconf') or (jnl == 'aipcp') or (jnl == 'apc'):
    jnlname = 'AIP Conf.Proc.'
    jnl = 'apc'
    iss = '1'
    typecode = 'C'

    
urltrunk = 'http://aip.scitation.org/toc/%s/%s/%s?size=all' % (jnl,vol,iss)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))


def getarticle(href, sec, subsec, p1):
    artlink = 'http://aip.scitation.org%s' % (href)
    try:
        print artlink
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (artlink)
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
    rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : iss, 'tc' : typecode, 
           'note' : [], 'auts' : [], 'aff' : [], 'p1' : p1}
    emails = {}
    if cnum:
        rec['cnum'] = cnum
    if sec:
        rec['note'].append(sec)
        if sec == 'NEW PRODUCTS':
            return {}
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
    #check whether older date exists
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta['name'] == 'dc.onlineDate':
            if not rec.has_key('date') or meta['content'] < rec['date']:
                rec['date'] = meta['content'] 
    #title
    for header in artpage.body.find_all('header', attrs = {'class' : 'publicationContentTitle'}):
        for h2 in header.find_all('h2'):
            rec['tit'] = h2.text.strip()
            rec['tit'] = re.sub('\n* *Scilight relation icon', '', rec['tit'])
    #doi
    rec['doi'] = re.sub('\/doi\/', '', re.sub('.doi.abs.', '', href))
    #emails
    for authornotes in artpage.body.find_all('author-notes'):
        for p in authornotes.find_all('p', attrs = {'class' : 'first last'}):
            affnr = 'NOAFFNR'
            for sup in p.find_all('sup'):
                affnr =  re.sub('\)', '', sup.text)
            for a in p.find_all('a', attrs = {'class' : 'email'}):
                emails[affnr] = re.sub('mailto:', '', a.text.strip())
    #affiliations
    for div in artpage.body.find_all('div', attrs = {'class' : 'affiliations-list hide'}):
        for li in div.find_all('li'):
            for sup in li.find_all('sup'):
                affnr =  re.sub('\)', '', sup.text)
                sup.replace_with('Aff%s= ' % affnr)
            rec['aff'].append(li.text)
    if not rec['aff']:
        for div in artpage.body.find_all('div', attrs = {'class' : 'affiliations-list list-unstyled hide'}):
            for li in div.find_all('li'):
                for sup in li.find_all('sup'):
                    affnr =  re.sub('\)', '', sup.text)
                    sup.replace_with('Aff%s= ' % affnr)
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
            author = re.sub('([A-Z]\.) ([A-Z]\.) ', r'\1\2 ', author)
            author = re.sub('([A-Z]\.) ([A-Z]\.) ', r'\1\2 ', author)
            author = re.sub('(.*) (.*)', r'\2, \1', author)
            for a in span.find_all('a'):
                if a.has_attr('href') and re.search('orcid.org', a['href']):
                    re.sub('http...orcid.org.', ', ORCID:', a['href'])
            for affi in range(len(affs)):
                if emails.has_key(affs[affi]):
                    author += ', EMAIL:%s' % (emails[affs[affi]])
                    affs[affi] = ''
            rec['auts'].append(author)                    
            for aff in affs:
                if aff:
                    rec['auts'].append('=Aff%s' % (aff))
    if len(rec['auts']) == 1 and not re.search('EMAIL', rec['auts'][0]) and emails.has_key('NOAFFNR'):
        rec['auts'][0] += ', EMAIL:%s' % (emails['NOAFFNR'])        
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'abstractSection abstractInFull'}):
        rec['abs'] = div.text.strip()
    if not rec.has_key('abs'):
        for div in artpage.body.find_all('div', attrs = {'class' : 'hlFld-Abstract'}):
            for div2 in div.find_all('div', attrs = {'class' : 'NLM_paragraph'}):
                rec['abs'] = div2.text.strip()
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
                            else:
                                a.replace_with('')
                    rec['refs'].append([('x', regexpref.sub(' ', li.text.strip()))])
    return rec
                
recs = []
(sec, subsec) = (False, False)
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
                                print '    div2'
                                (href, p1) = (False, False)
                                for a in article.find_all('a', attrs = {'class' : 'ref nowrap'}):
                                    href = a['href']
                                #articleID is not on indiviual article page (sic!)
                                for div3  in article.find_all('div', attrs = {'class' : 'meta-article'}):
                                    p1 = re.sub('.*, ([A-Z0-9]+) \(\d\d\d\d\);.*', r'\1', div3.text.strip())
                                if href and p1:
                                    recs.append(getarticle(href, sec, subsec, p1))
                    elif child2.name == 'article':
                        for div2 in child2.find_all('div', attrs = {'class' : 'art_title linkable'}):
                            (href, p1) = (False, False)
                            for a in child2.find_all('a', attrs = {'class' : 'ref nowrap'}):
                                href = a['href']
                            #articleID is not on indiviual article page (sic!)
                            for div3  in child2.find_all('div', attrs = {'class' : 'meta-article'}):
                                p1 = re.sub('.*, ([A-Z0-9]+) \(\d\d\d\d\);.*', r'\1', div3.text.strip())
                            if href and p1:
                                article = getarticle(href, sec, subsec, p1)
                                if article['auts']:
                                    recs.append(article)
                        




                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
