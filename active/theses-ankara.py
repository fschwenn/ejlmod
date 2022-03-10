# -*- coding: utf-8 -*-
#harvest theses from Ankara U.
#FS: 2022-03-05

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time
import json
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Ankara U.'

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

rpp = 50
pages = 5
boringfacs = [u'Sosyal Bilimleri Enstitüsü', u'Arkeoloji Ana Bilim Dalı', u'Bilgisayar ve Öğretim Teknolojileri Eğitimi Ana Bilim Dalı',
              u'Bilgi ve Belge Yönetimi', u'Biyoloji Ana Bilim Dalı', u'Çalışma Ekonomisi ve Endüstri İlişkileri Ana Bilim Dalı',
              u'Dil ve Tarih Coğrafya Fakültesi: Bilgi ve Belge Yönetimi Bölümü', u'Dil ve Tarih Coğrafya Fakültesi', u'Felsefe',
              u'Hukuk', u'İslam Tarihi ve Sanatları Ana Bilim Dalı', u'Jeoloji Mühendisliği', u'Kimya Mühendisliği Ana Bilim Dalı',
              u'Kimya', u'Özel Hukuk Ana Bilim Dalı', u'Siyaset Bilimi ve Kamu Yönetimi Ana Bilim Dalı',
              u'Tarım Makineleri ve Teknolojileri Mühendisliği Ana Bilim Dalı', u'Felsefe ve Din Bilimleri Ana Bilim Dalı',
              u'İletişim Fakültesi', u'Tarih', u'Türk İnkılap Tarihi Enstitüsü', u'Hukuk Fakültesi', u'Mühendislik Fakültesi',
              u'Ziraat Fakültesi', u'Dil ve Tarih-Coğrafya Fakültesi', u'Eğitim Bilimleri Enstitüsü', u'Eğitim Bilimleri Fakültesi',
              u'Siyasal Bilgiler Fakültesi', u'İlahiyat Fakültesi', u'Bilgisayar Mühendisliği Ana Bilim Dalı',
              u'Doğu Dilleri ve Edebiyatları (Sinoloji) Ana Bilim Dalı', u'Felsefe Ana Bilim Dalı', u'Gazetecilik Ana Bilim Dalı',
              u'Gazetecilik Bilim Dalı', u'İslam Mezhepleri Tarihi', u'Bilgisayar Mühendisliği Ana Bilim Dalı',
              u'Doğu Dilleri ve Edebiyatları (Sinoloji) Ana Bilim Dalı', u'Felsefe Ana Bilim Dalı', u'Gazetecilik Ana Bilim Dalı',
              u'Gazetecilik Bilim Dalı', u'İslam Mezhepleri Tarihi', u'Peyzaj Mimarlığı Ana Bilim Dalı', u'Tefsir Bilim Dalı',
              u'Yer Bilgisi: Ankara Üniversitesi / Sosyal Bilimler Enstitüsü / İslam Tarihi ve Sanatları Ana Bilim Dalı / İslam Tarihi Bilim Dalı',
              u'Fen Bilimler Enstitüsü', u'Kamu Hukuku Ana Bilim Dalı', u'Tasavvuf Bilim Dalı', u'Temel İslam Bilimleri Ana Bilim Dalı',
              u'Sosyal Bilimler Enstitüsü', u'Biyoloji', u'Çalışma Ekonomisi ve Endüstri İlişkileri', u'Elektrik-Elektronik Mühendisliği',
              u'Gayrimenkul Geliştirme ve Yönetimi', u'Hidrobiyoloji Anabilim Dalı', u'Kimya Mühendisliği', u'Peyzaj Mimarlığı',
              u'Spor Bilimleri Fakültesi', u'Tarım Makineleri ve Teknolojileri Mühendisliği', u'Tarla Bitkileri', u'Bilgisayar Mühendisliği',
              u'Gıda Mühendisliği', u'Tarımsal Yapılar ve Sulama', u'Toprak Bilimi ve Bitki Besleme', u'Bitki Koruma',
              u'Ankara Üniversitesi Fen Bilimleri Enstitüsü Gıda Mühendisliği Anabilim Dalı',
              u'Ankara Üniversitesi Sosyal Bilimler Enstitüsü Felsefe ve Din Bilimleri (İslam Felsefesi) Ana Bilim Dalı',
              u'Ankara Üniversitesi Sosyal Bilimler Enstitüsü Özel Hukuk (Medenî Usul ve İcra-İflâs Hukuku) Anabilim Dalı',
              u'Beslenme ve Diyetetik Anabilim Dalı', u'Biyokimya Bilim Dalı', u'Biyoteknoloji Anabilim Dalı', u'Biyoteknoloji Bilim Dalı',
              u'Botanik Anabilim Dalı', u'Çocuk Gelişimi Anabilim Dalı', u'Çocuk Gelişimi Ana Bilim Dalı',
              u'Elektrik-Elektronik Mühendisliği Ana Bilim Dalı', u'Fizikokimya Bilim Dalı', u'Fonksiyonel Analiz Anabilim Dalı',
              u'Gayrimenkul Geliştirme ve Yönetimi Ana Bilim Dalı', u'Jeoloji Mühendisliği Anabilim Dalı', u'Tarım Ekonomisi Anabilim Dalı',
              u'Tarım Ekonomisi', u'Tarım Makineleri ve Teknolojileri Mühendisliği Anabilim Dalı', u'Tarla Bitkileri Anabilim Dalı',
              u'Zootekni Anabilim Dalı', u'Anorganik Kimya Bilim Dalı', u'Gıda Mühendisliği Anabilim Dalı', u'İstatistik Ana Bilim Dalı',
              u'Kimya Ana Bilim Dalı', u'Kimya Anabilim Dalı', u'Sağlık Bilimleri Fakültesi', u'Biyoloji Anabilim Dalı',
              u'Ankara Üniversitesi Eğitim Bilimleri Enstitüsü Eğitimde Psikolojik Hizmetler Anabilim Dalı Rehberlik ve Psikolojik Danışma Bilim Dalı',
              u'Ankara Üniversitesi Fen Bilimleri Enstitüsü Bitki Koruma Anabilim Dalı',
              u'Ankara Üniversitesi Fen Bilimleri Enstitüsü Jeofizik Mühendisliği Anabilim Dalı',
              u'Ankara Üniversitesi Fen Bilimleri Enstitüsü Tarım Ekonomisi Anabilim Dalı',
              u'Ankara Üniversitesi Fen Bilimleri Enstitüsü Zootekni Anabilim Dalı',
              u'Ankara Üniversitesi Sağlık Bilimleri Enstitüsü Endodonti Ana Bilim Dalı',
              u'Ankara Üniversitesi Sağlık Bilimleri Enstitüsü Mikrobiyoloji Anabilim Dalı',
              u'Ankara Üniversitesi Sosyal Bilimler Enstitüsü İktisat Anabilim Dalı',
              u'Ankara Üniversitesi Sosyal Bilimler Enstitüsü Tarih Anabilim Dalı', u'Diş Hekimliği Fakültesi', u'Diş Hekimliği',
              u'Eğitim Bilimleri Enstitüs', u'Eğitim Bilimleri Enstitüsü Eğitim', u'Sağlık Bilimler Enstitüsü', u'Saglık Bilimleri Enstitüsü',
              u'SOSYAL BİLİMLER ENSTİTÜSÜ', u'Türk İnkılâp Tarihi Enstitüsü', u'Economiques', u'Ziraat Mühendisliği',          
              u'Sağlık Bilimleri Enstitüsü']


hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-ANKARA-%s' % (stampoftoday)

prerecs = []
for page in range(pages):
    tocurl = 'https://dspace.ankara.edu.tr/xmlui/handle/20.500.12575/27627/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    try:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    except:
        print "retry in 300 seconds"
        time.sleep(300)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    time.sleep(3)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'ds-artifact-item'}):
        keepit = True
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor'  : []}
        for span in div.find_all('span', attrs = {'class' : 'publisher'}):
            for fac in re.split(' : ', span.text.strip()):
                if fac in boringfacs:
                    keepit = False
                elif not fac in ['Ankara', u'Ankara Üniversitesi']:
                    rec['note'].append(fac)
        for a in div.find_all('a'):
            rec['link'] = 'https://dspace.ankara.edu.tr' + a['href']
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        if keepit:
            prerecs.append(rec)
    print '  %i prerecs so far' % (len(prerecs))

recs = []
i = 0
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'] + '?show=full', headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link'] + '?show=full'), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if re.search('\(', meta['content']):
                    if re.search('\(Yazar', meta['content']):
                        rec['autaff'] = [[ re.sub(' *\(.*', '', meta['content']), publisher ]]
                else:
                    rec['autaff'] = [[ meta['content'], publisher ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' the ', meta['content']):
                    rec['abs'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'tr':
                    rec['language'] = 'Turkish'
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d\d', meta['content']):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', meta['content'])
    #date
    if not 'date' in rec.keys():
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_date'}):
                rec['date'] = meta['content']            
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']

    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            if label == 'dc.contributor.department':
                fac = td.text.strip()
                if fac in boringfacs:
                    keepit = False
                else:
                    rec['note'].append(fac)
            #supervisor
            elif label == 'dc.contributor.advisor':
                rec['supervisor'].append([td.text.strip()])
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()

