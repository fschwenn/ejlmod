# -*- coding: utf-8 -*-
#harvest theses from University of U. Autonoma, Madrid (main) 
#FS: 2019-09-26

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

rpp = 50
pages = 5
boring = ['UAM. Departamento de Medicina', 'Hospital Universitario de La Princesa',
          u'UAM. Departamento de Biología', u'Centro de Biología Molecular Severo Ochoa (CBM)',
          u'Centro Nacional de Investigaciones Cardiovasculares Carlos III (CNIC)',
          u'Centro Nacional de Investigaciones Oncológicas (CNIO)',
          u'CSIC. Instituto de Catálisis y Petroleoquímica (ICP)',
          u'Hospital General Universitario Gregorio Marañon',
          u'Instituto de Investigación en Ciencias de la Alimentación (CIAL)',
          u'Instituto de Investigaciones Biomédicas &quot;Alberto Sols&quot; (IIBM)',
          u'UAM. Departamento de Biología Molecular', u'UAM. Departamento de Bioquímica',
          u'UAM. Departamento de Ciencia Política y Relaciones Internacionales',
          u'UAM. Departamento de Cirugía', u'UAM. Departamento de Estructura Económica y Economía del Desarrollo',
          u'UAM. Departamento de Estudios Árabes e Islámicos y Estudios Orientales',
          u'UAM. Departamento de Filología Española', u'UAM. Departamento de Filosofía',
          u'UAM. Departamento de Geografía', u'UAM. Departamento de Historia Contemporánea',
          u'UAM. Departamento de Música', u'UAM. Departamento de Pedagogía',
          u'UAM. Departamento de Psicología Social y Metodología', u'UAM. Departamento de Psiquiatría',
          u'UAM. Departamento de Química Física Aplicada', u'UAM. Departamento de Química Inorgánica',
          u'UAM. Departamento de Química Orgánica', u'Centro de Investigación Biomédica en Red en Enfermedades Raras (CIBERER)'
          u'Centro de Investigaciones Energéticas Medioambientales y Tecnológicas (CIEMAT)',
          u'Instituto de Investigación del Hospital de La Princesa (IP)', u'UAM. Departamento de Filologías y su Didáctica',
          u'Instituto de Investigaciones Biomédicas &quot;Alberto Sols&quot; (IIBM)',
          u'Instituto de Investigación Hospital Universitario LA PAZ (IdiPAZ)',
          u'Instituto de Investigación Sanitaria Fundación Jiménez Díaz (IIS-FJD)',
          u'Instituto Fundación Teófilo Hernando para la I+D del medicamento',
          u'UAM. Departamento de Antropología Social y Pensamiento Filosófico',
          u'UAM. Departamento de Educación Física, Deporte y Motricidad Humana',
          u'UAM. Departamento de Farmacología', u'UAM. Departamento de Fisiología',
          u'UAM. Departamento de Historia Antigua, Historia Medieval, Paleografía y Diplomática',
          u'UAM. Departamento de Obstetricia y Ginecología', u'UAM. Departamento de Pediatría',
          u'UAM. Departamento de Química Analítica y Análisis Instrumental',
          u'Hospital Universitario 12 de Octubre', u'UAM. Departamento de Anatomía, Histología y Neurociencia',
          u'Instituto Madrileño de Estudios Avanzados en Materiales (IMDEA-Materiales)',
          u'Instituto Madrileño de Investigación y Desarrollo Rural, Agrario y Alimentario (IMIDRA)',
          u'UAM. Departamento de Derecho Privado, Social y Económico', u'UAM. Departamento de Derecho Público y Filosofía Jurídica',
          u'UAM. Departamento de Didácticas Específicas', u'UAM. Departamento de Ecología', u'UAM. Departamento de Economía Aplicada',
          u'UAM. Departamento de Filología Francesa', u'UAM. Departamento de Filología Inglesa',          
          u'UAM. Departamento de Lingüística, Lenguas Modernas, Lógica y Fª de la Ciencia y Tª de la Literatura y Literatura Comparada',
          u'UAM. Departamento de Medicina Preventiva y Salud Pública y Microbiología',
          u'UAM. Departamento de Prehistoria y Arqueología', u'UAM. Departamento de Psicología Básica',
          u'UAM. Departamento de Psicología Biológica y de la Salud', u'UAM. Departamento de Psicología Evolutiva y de la Educación',
          u'UAM. Departamento de Química', u'UAM. Departamento de Tecnología Electrónica y de las Comunicaciones',
          u'Hospital Universitario Marqués de Valdecilla-IDIVAL (Santander)', u'Hospital Virgen de la Salud (Toledo)',
          u'Instituto de Ciencias Ambientales de la Orinoquia Colombiana (ICAOC, Colombia)',
          u'Instituto Madrileño de Estudios Avanzados en Alimentación (IMDEA-Alimentación)',
          u'Instituto Madrileño de Estudios Avanzados en Nanociencia (IMDEA-Nanociencia)',
          u'Instituto Nacional de Técnica Aeroespacial (INTA)', u'UAM. Centro de Microanálisis de Materiales (CMAM)',
          u'UAM. Departamento de Análisis Económico: Economía Cuantitativa',
          u'UAM. Departamento de Análisis Económico, Teoría Económica e Historia Económica',
          u'UAM. Departamento de Anatomía Patológica', u'UAM. Departamento de Contabilidad',
          u'UAM. Departamento de Didáctica y Teoría de la Educación',
          u'UAM. Departamento de Economía y Hacienda Pública', u'UAM. Departamento de Educación Artística, Plástica y Visual',
          u'UAM. Departamento de Enfermería', u'UAM. Departamento de Filología Clásica',
          u'UAM. Departamento de Filologías y su Didáctica', u'UAM. Departamento de Financiación e Investigación Comercial',
          u'UAM. Departamento de Geología y Geoquímica', u'UAM. Departamento de Historia Moderna',
          u'UAM. Departamento de Historia y Teoría del Arte', u'UAM. Departamento de Ingeniería Informática',
          u'UAM. Departamento de Ingeniería Química', u'UAM. Departamento de Organización de Empresas',
          u'UAM. Departamento de Química Agrícola', u'UAM. Instituto Universitario de Estudios de la M']

deptofc = {u'UAM. Departamento de Física de la Materia Condensada' : 'f',
           u'UAM. Departamento de Física Teórica de la Materia Condensada' : 'f',
           u'Instituto de Ciencias Matemáticas (ICMAT)' : 'm',
           u'UAM. Departamento de Matemáticas' : 'm'}
publisher = 'U. Autonoma, Madrid (main)'

typecode = 'T'

jnlfilename = 'THESES-UAM-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
#tocurl = 'https://repositorio.uam.es/handle/10486/129587/discover?sort_by=dc.date.issued_dt&order=desc&rpp=10'

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
for page in range(pages):
    tocurl = 'https://repositorio.uam.es/handle/10486/700636/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc&filtertype_0=type&filter_relational_operator_0=equals&filter_0=doctoralThesis'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'supervisor' : [], 'note' : []}
        for a in div.find_all('a'):
            if a.has_attr('href') and re.search('handle', a['href']):
                rec['link'] = 'https://repositorio.uam.es' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                if not rec['hdl'] in uninterestingDOIS:
                    prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]            
                rec['autaff'][-1].append('U. Autonoma, Madrid (main)')
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            #elif meta['name'] == 'DC.subject':
            #    for keyw in re.split(' *; *', meta['content']):
            #        rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['xml:lang'] == 'en_US':
                    rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d pag', meta['content']):
                    rec['pages'] = re.sub('\D', '', meta['content'])
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'spa':
                    rec['language'] = 'Spanish'
                elif meta['content'] == 'ita':
                    rec['language'] = 'Italian'
                elif meta['content'] == 'por':
                    rec['language'] = 'Portuguese'
                elif meta['content'] != 'eng':
                    rec['note'] = [ 'Language: %s' % (meta['content']) ]
            #contributor
            elif meta['name'] == 'DC.contributor':
                if re.search(' \(dir.?\)', meta['content']):
                    rec['supervisor'].append([re.sub(' \(dir.?\)', '', meta['content'])])
                else:
                    dep = meta['content']
                    if dep in boring:
                        keepit = False
                    else:
                        if dep in deptofc.keys():
                            rec['fc'] = deptofc[dep]
                        else:
                            rec['note'].append(dep)
    #license
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['license'] = {'url' : a['href']}
    if keepit:
        recs.append(rec)
        print '  ', rec.keys()
    else:
        newuninterestingDOIS.append(rec['hdl'])


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

ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()
