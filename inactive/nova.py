# -*- coding: UTF-8 -*-
##!/usr/bin/python

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs
import urllib2
import urlparse
import time
#import cookielib
from bs4 import BeautifulSoup

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
publisher = 'Nova Science Publishers, Inc.'



jnlfilename = 'NovaScience'
toclinks = ['https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=25294&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=3119&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=6671&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=197&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=1066&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=3651&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=19497&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=4639&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=24956&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=691&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=3679&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=4056&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=4516&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=6369&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=21198&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_69&products_id=248&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=29753&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=3911&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=18046&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=2075&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=12164&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=3907&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=11625&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=6836&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=41033&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=16795&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=8356&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_75&products_id=36986&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_72&products_id=566&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_72&products_id=1099&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_72&products_id=17447&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_97&products_id=6360&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_97&products_id=18314&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_97&products_id=691&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_97&products_id=54339&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=5811&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=28927&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=31398&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=3808&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=16028&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=3854&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=42371&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=39777&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=1869&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=145&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=1867&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=699&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=1872&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=36691&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=8678&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=21109&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=3174&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=430&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=140&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=3858&osCsid=7615f1138fcb94694c8634a9939cef50',
            'https://www.novapublishers.com/catalog/product_info.php?cPath=23_48_73&products_id=1475&osCsid=7615f1138fcb94694c8634a9939cef50']


def fsunwrap(tag):
    try: 
        for i in tag.find_all('i'):
            cont = i.string
            i.replace_with(cont)
    except:
        print 'fsunwrap-i-problem'
    try: 
        for b in tag.find_all('b'):
            cont = b.string
            b.replace_with(cont)
    except:
        print 'fsunwrap-b-problem'
    try: 
        for sup in tag.find_all('sup'):
            cont = sup.string
            sup.replace_with('^'+cont)
    except:
        print 'fsunwrap-sup-problem'
    try: 
        for sub in tag.find_all('sub'):
            cont = sub.string
            sub.replace_with('_'+cont)
    except:
        print 'fsunwrap-sub-problem'
    try: 
        for form in tag.find_all('formula',attrs={'formulatype': 'inline'}):
            form.replace_with(' [FORMULA] ')
    except:
        print 'fsunwrap-form-problem'
    return tag



recs = []
for toclink in set(toclinks):
    rec = {'tc' : 'B', 'jnl' : 'BOOK', 'link' : toclink, 'auts' : []}
    toc = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
    #Ttile
    for td in toc.body.find_all('td', attrs = {'class' : 'pageHeading2'}):
        if not rec.has_key('tit'):
            rec['tit'] = td.text
    for td in toc.body.find_all('td', attrs = {'class' : 'main'}):
        tdtext = re.sub('[\n\t]', ' ', td.text.strip())
        #Editors
        if re.search('^Editors:', tdtext):
            tdtext = re.sub(' and ', ', ', tdtext)
            editors = re.sub('Editors: *', '', re.sub('\(.*?\)', '', tdtext))
            if re.search(';', editors):
                for editor in re.split(' *; ', editors):
                    rec['auts'].append(editor.strip()+' (ed.)')
            else:
                for editor in re.split(' *, ', editors):
                    rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1 (ed.)', editor.strip()))
        #Abstract
        elif re.search('^Book Description:', tdtext):
            rec['abs'] = re.sub('Book Description: *', '', tdtext)
        #Date
        elif re.search('^Pub. Date:', tdtext):
            rec['date'] = re.sub('.* (20\d\d)[, ].*', r'\1', tdtext)
            rec['date'] = re.sub('.* (20\d\d).*', r'\1', rec['date'])
        #Pages 
        elif re.search('^Pages:', tdtext):
            if re.search('\d[ \.]pp', tdtext):
                rec['pages'] = re.sub('.* (\d+)[ \.]pp.*', r'\1', tdtext)
            else:
                rec['pages'] = re.sub('.* (\d+).*', r'\1', tdtext)
        #ISBN
        elif re.search('^ISBN:', tdtext):
            rec['isbn'] = re.sub('.*?(\d+.*)', r'\1', tdtext)
            rec['isbn'] = re.sub('\-', '', rec['isbn'])
    recs.append(rec)



xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
