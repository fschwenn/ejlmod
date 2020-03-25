# -*- coding: utf-8 -*-
#harvest theses from Granada U.
#FS: 2019-11-26

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
import mechanize
import unicodedata

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Granada (main)'


numberofpages = 4
recordsperpage = 100

boringdivisions = ['Psicologia', 'Ingenieria', 'Biologia', 'Educacion', 'Quimica', 'Medicina', 'Administrativo', 'Anatomia', 'Andalucia', 'Antigua', 'Arquitectonicas', 'Atomica', 'Biotecnologia', 'Botanica', 'Bromatologia', 'Celular', 'clinica', 'Comercializacion', 'Comercio', 'Comportamiento', 'Construccion', 'Construcciones', 'Contabilidad', 'Criminologia', 'Democracia', 'Deportes', 'Deportiva', 'Dermatologia', 'Dibujo', 'Ecologia', 'Economica', 'Eduacion', 'Electronica', 'Embriologia', 'Empresa', 'Empresas', 'Enfermeria', 'Escolar]', 'Escolares', 'Escultura', 'Esenanza-Aprendizaje', 'Especialidades', 'Estadistica', 'Estomatologia', 'Estratigrafia', 'Estructuras', 'Evolutiva', 'Farmacologia', 'Filologias', 'Financiera', 'financiero', 'Fisioterapia', 'Genetica', 'Genomica', 'Geodinamica', 'Geografico', 'Ginecologia', 'Hidraulica', 'Histologia', 'Historiograficas', 'Humanidades', 'Informaticos', 'Inglesa', 'Inmunologia', 'Inteligencia', 'Internacionales', 'Interpretacion', 'Interuniversitario', 'Juridica', 'Legal', 'Linguistica', 'Mecanica', 'Medicna', 'Medieval', 'Mente', 'Mercados', 'Microbiologia', 'Migraciones', 'Mineralogia', 'Obstetricia', 'Oncologica', 'Operativa', 'Optica', 'Organizaciones', 'Otorrinolaringologia', 'Paleontologia', 'Parasitologia', 'Pedagogia', 'Pediatria', 'Penal', 'Petrologia', 'Pfizer', 'Pintura', 'Poeticas', 'Prehistoria', 'Preventiva', 'Proyectos', 'Publico', 'Radiologia', 'Recursos', 'Regional', 'Relaciones', 'Seguridad', 'Semiticos', 'Sistema', 'Sociologia', 'Tecnicas', 'Toxicologia', 'Trabajo', 'Traduccion', 'tributario', 'Vegetal', 'Zoologia', 'Historia', 'Agua', 'America', 'Analisis', 'Antropologia', 'Aplicaciones', 'Aplicada', 'Arqueologia', 'Arquitectonica', 'artes', 'Avances', 'Biogeoquimicos', 'Comunicacion', 'Dinamica', 'Educativa', 'Ensenanza-Aprendizaje', 'Eslava', 'Espanola', 'Evaluacion', 'Farmaceutica', 'Fisiologia', 'Flujos', 'Geografia', 'Grafica', 'Inorganica', 'Internacional', 'Lenguajes', 'Metodos', 'Musica', 'Ordenacion', 'Organica', 'Personalidad', 'Psicologico', 'Tecnologias', 'Tratamiento', 'Urbanistica', 'Arquitectura', 'Conflictos', 'contextos', 'Corporal', 'Curriculum', 'Diagnostico', 'Economia', 'Espacio', 'Griega', 'Humana', 'Informacion', 'Literatura', 'Musical', 'Organizacion', 'Plastica', 'Profesorado', 'Social', 'Territorio', 'Alimentos', 'Arte', 'Desarrollo', 'Lengua', 'Modelos', 'Tecnologia', 'Bioquimica', 'Discursos', 'Expresion', 'Filologia', 'Filosofia', 'Genero', 'Migratorios', 'Practicas', 'Sociales', 'Contextos', 'Economicas', 'Educativas', 'Empresariales', 'Instituciones', 'Molecular', 'Mujeres', 'Nutricion', 'Textos', 'Tierra', 'Biomedicina', 'Derecho', 'Didactica', 'Juridicas', 'Sistemas', 'Artes', 'Civil', 'Clinica', 'Farmacia', 'Lenguas']                   




###remove accents from a string
def akzenteabstreifen(string):
    if not type(string) == type(u'unicode'):
        string = unicode(string,'utf-8', errors='ignore')
        if not type(string) == type(u'unicode'):
            return string
        else:
            return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')
    else:
        return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')


prerecs = []
recs = []
jnlfilename = 'THESES-GRANADA-%s' % (stampoftoday)
for pn in range(numberofpages):
    tocurl = 'https://digibug.ugr.es/handle/10481/191/browse?rpp=' + str(recordsperpage) + '&sort_by=2&type=dateissued&offset=' + str(pn * recordsperpage) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }===' % (pn+1, numberofpages, tocurl)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)) 
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
        for a in div.find_all('a'):
            if re.search('handle\/\d', a['href']):
                rec['artlink'] = 'https://digibug.ugr.es' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/(.*\d).*', r'\1', a['href'])
                prerecs.append(rec)
    time.sleep(10)

i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue


        
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'DC.creator':
                author = meta['content']
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #supervisor
            elif meta['name'] == 'DC.contributor':
                if meta.has_attr('xml:lang'):
                    rec['division'] = akzenteabstreifen(meta['content'])
                    rec['note'].append(rec['division'])
                else:
                    rec['supervisor'].append([meta['content']])
            #isbn
            elif meta['name'] == 'DC.identifier':
                if re.search('^978', meta['content']):
                    rec['isbn'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] in ['spa', 'es']:
                    rec['language'] = 'spanish'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdflink'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
    if 'pdflink' in rec.keys():
        if 'licence' in rec.keys():
            rec['FFT'] = rec['pdflink']
        else:
            rec['hidden'] = rec['pdflink']
    keepit = True
    if 'division' in rec.keys():
        for bd in boringdivisions:
            if bd in rec['division']:
                print '  skip "%s" because of "%s"' % (rec['division'], bd)
                keepit = False
                break
    if keepit:
        print rec.keys()
        recs.append(rec)
        
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
