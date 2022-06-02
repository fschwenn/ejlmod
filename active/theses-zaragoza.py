# -*- coding: utf-8 -*-
#harvest theses from U. Zaragoza
#JH: 2022-05-01

from time import sleep
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from base64 import b16encode
import ejlmod2
import os
import codecs
import datetime
import re

publisher = 'U. Zaragoza (main)'
rpp = 50
pages = 2
boring = [u'Medicina y especialidades médicas', u'Programa de Doctorado en Producción Animal',
          'Programa de Doctorado en Historia del Arte',
          u'Programa de Doctorado en Bioquímica y Biología Molecular',
          u'Programa de Doctorado en Ciencia Analítica en Química',
          u'Programa de Doctorado en Ciencias Agrarias y del Medio Natural',
          u'Programa de Doctorado en Ciencias Biomédicas y Biotecnológicas',
          u'Programa de Doctorado en Ciencias de la Antigüedad',
          u'Programa de Doctorado en Ciencias de la Salud y del Deporte',
          u'Lingüística aplicada a la traducción e interpretación',
          u'Programa de Doctorado en Contabilidad y Finanzas',
          u'Programa de Doctorado en Derechos Humanos y Libertades Fundamentales',
          u'Programa de Doctorado en Derecho', u'Programa de Doctorado en Economía',
          u'Programa de Doctorado en Economía y Gestión de las Organizaciones',
          u'Programa de Doctorado en Educación', u'Programa de Doctorado en Geología',
          u'Programa de Doctorado en Energías Renovables y Eficiencia Energética',          
          u'Programa de Doctorado en Historia, Sociedad y Cultura: Épocas Medieval y Moderna',
          u'Programa de Doctorado en Ingeniería Biomédica',
          u'Teoría de la literatura y literatura comparada',
          u'Programa de Doctorado en Ingeniería de Sistemas e Informática',
          u'Programa de Doctorado en Ingeniería Electrónica', u'Programa de Doctorado en Ingeniería Mecánica',
          u'Programa de Doctorado en Ingeniería Química y del Medio Ambiente',
          u'Programa de Doctorado en Lingüística Hispánica',
          u'Programa de Doctorado en Logística y Gestión de la Cadena de Suministro',
          u'Programa de Doctorado en Mecánica de Fluidos', u'Programa de Doctorado en Medicina',
          u'Programa de Doctorado en Medicina y Sanidad Animal',
          u'Programa de Doctorado en Nuevos Territorios en la Arquitectura',
          u'Programa de Doctorado en Ordenación del Territorio y Medio Ambiente',
          u'Programa de Doctorado en Patrimonio, Sociedades y Espacios de Frontera',
          u'Programa de Doctorado en Química Inorgánica', u'Programa de Doctorado en Química Orgánica',
          u'Programa de Doctorado en Sociología de las Políticas Públicas y Sociales',
          u'Programa de Doctorado en Calidad, Seguridad y Tecnología de los Alimentos',
          u'Programa de Doctorado en Energías renovables y Eficiencia energética',
          u'Programa de Doctorado en Estudios Ingleses', u'Programa de Doctorado en Filosofía',
          u'Programa de Doctorado en Historia Contemporánea',
          u'Programa de Doctorado en Ingeniería de Diseño y Fabricación',
          u'Programa de Doctorado en Ingeniería Química y del Medio ambiente',
          u'Programa de Doctorado en Literaturas Hispánicas',
          u'Programa de Doctorado en Nuevos territorios en Arquitectura',
          u'Programa de Doctorado en Relaciones de Género y Estudios Feministas',
          u'Programa de Doctorado en Tecnologías de la Información y Comunicaciones en Redes Móviles',
          u'Ciencias de la Documentación e Historia de la Ciencia',
          u'Filología Inglesa y Alemana', u'Filosofía', u'Fisiatría y Enfermería',
          u'Historia', u'Ingeniería de Diseño y Fabricación',
          u'Ingeniería Electrónica y Comunicaciones', u'Ingeniería Mecánica',
          u'Ingeniería Química y Tecnologías del Medio Ambiente',
          u'Producción Animal y Ciencia de los Alimentos',
          u'Unidad Predepartamental de Arquitectura', u'Historia contemporánea',
          u'Bioquímica y Biología Molecular y Celular', u'Anatomía patológica',
          u'Cirugía, Ginecología y Obstetricia', u'Anatomía',
          u'Filología Española', u'Cirugía', u'Derecho constitucional',
          u'Historia Medieval, Ciencias y Técnicas Historiográficas y Estudios Árabes e Islámicos',
          u'Historia Moderna y Contemporánea', u'Economía financiera y contabilidad',
          u'Instituto de Ciencia de Materiales de Aragón (ICMA)', u'Farmacología',
          u'Medicina, Psiquiatría y Dermatología', u'Obstetricia y ginecología',
          u'Psicología y Sociología', u'Análisis geográfico regional', u'Arqueología',
          u'Arquitectura y tecn. Computadoras', u'Bioquímica y biología molecular', u'Cerámicas',
          u'Comercialización e Invest. Mercados', u'Derecho internacional público',
          u'Didáctica de la expresión corporal', u'Didáctica de las ciencias experimentales',
          u'Didáctica de las ciencias sociales', u'Economía aplicada',
          u'Epidemiología y Salud Pública', u'Estratigrafía', u'Filología latina', u'Filosofía del derecho',
          u'Geodinámica externa', u'Geografía humana', u'Geometría y topología',
          u'Historia e instituciones económicas',
          u'Historia moderna', u'Ingeniería de sistemas y automática',
          u'Lenguajes y sistemas informáticos', u'Métodos de invest. Y diagnóstico en educación',
          u'Microbiología', u'Microbiología y parasitología',
          u'Organización de empresas', u'Paleontología', u'Pediatría', u'Petrología y Geoquímica',
          u'Pintura', u'Prehistoria', u'Prospectiva e investigación minera',
          u'Química analítica', u'Química Analítica', u'Química orgánica', u'Radiología y medicina física',
          u'Servicios de Salud', u'Sociología', u'Tecnología electrónica', u'Zoología',
          u'Ciencias de la Antigüedad', u'Ciencias de la Educación',
          u'Derecho Penal, Filosofía del Derecho e Historia del Derecho',
          u'Didáctica de las Ciencias Experimentales',
          u'Didáctica de las Lenguas y de las Ciencias Humanas y Sociales',
          u'Dirección de Márketing e Investigación de Mercados', u'Dirección y Organización de Empresas',
          u'Estructura e Historia Económica y Economía Pública', u'Expresión Musical, Plástica y Corporal',
          u'Geografía y Ordenación del Territorio', u'Historia del Arte',
          u'Microbiología, Medicina Preventiva y Salud Pública', u'Patología Animal',
          u'Pediatría, Radiología y Medicina Física', u'Química Analítica', u'Química Orgánica',
          u'Derecho administrativo', u'Derecho civil', u'Derecho mercantil',
          u'Economía, sociología y política agraria', u'Estadística e investigación operativa',
          u'Fisiología', u'Fundamentos del análisis económico', u'Geodinámica interna',
          u'Historia antigua', u'Ingeniería agroforestal', u'Ingeniería mecánica', u'Ingeniería metalúrgica',
          u'Ing. Procesos de fabricación', u'Producción animal', u'Producción vegetal',
          u'Química inorgánica', u'Tecnología del medio ambiente', u'Agricultura y Economia Agraria',
          u'Análisis Económico', u'Ciencias Agrarias y del Medio Natural', u'Derecho de la Empresa',
          u'Derecho Privado', u'Derecho Público', u'Farmacología y Fisiología',
          u'Informática e Ingeniería de Sistemas',
          u'Instituto de Investigación en Ingeniería de Aragón (I3A)', u'Literatura Española',
          u'Métodos Estadísticos', u'Química Inorgánica', u'Zaragoza Logistics Center (ZLC)']





          

recs = []

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

jnlfilename = 'THESES-ZARAGOZA-%s' % (stampoftoday)

# Initialize Webdriver
driver = webdriver.PhantomJS()

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

def get_sub_site(url):
    global uninterestingDOIS
    keepit = True
    print("  [%s] --> Harversting data" % url)

    rec = {'tc': 'T', 'jnl': 'BOOK', 'note' : []}
    rec['link'] = re.sub('\/export.*', '', url)

    can_be_downloaded = False

    driver.get(url)
    my_record = BeautifulSoup(driver.page_source, 'lxml').find_all('record')

    if len(my_record) != 1:
        return

    for datafield in my_record[0].find_all('datafield'):
        tag = datafield.get('tag')
        data = datafield.find_all('subfield')

        # Get the language
        if tag == '041':
            language = data[0].text.upper()
            if language == 'SPA':
                rec['language'] = 'spanish'
            elif language != 'ITA':
                rec['language'] = 'italian'
            elif language != 'ENG':
                rec['language'] = language

        # Get the author
        elif tag == '100':
            rec['autaff'] = []
            for author in data:
                rec['autaff'].append([author.text, publisher])

        # Get the title
        elif tag == '245':
            for sf in datafield.find_all('subfield', attrs = {'code' : 'a'}):
                rec['tit'] = sf.text
            for sf in datafield.find_all('subfield', attrs = {'code' : 'b'}):
                rec['tit'] += ': ' + sf.text

        # Get the date
        elif tag == '260':
            date = datafield.find_all('subfield', attrs={'code': 'c'})
            rec['date'] = date[0].text

        # Get the pages
        elif tag == '300':
            rec['pages'] = data[0].text

        # Get the abstract
        elif tag == '520':
            if len(data[0].text) > 10:
                rec['abs'] = data[0].text

        # Get the license
        elif tag == '506':
            if len(data) != 1:
                can_be_downloaded = True
                rec['license'] = {}
                for sf in data:
                    if sf['code'] == 'u':
                        rec['license']['url'] = sf.text

        # Get the keywords
        elif tag == '653':
            rec['keyw'] = []
            for keyword in data:
                rec['keyw'].append(keyword.text)

        # Get the supervisors
        elif tag == '700':
            rec['supervisor'] = []
            for supervisor in datafield.find_all('subfield', attrs={'code': 'a'}):
                rec['supervisor'].append([re.sub('^Dra?\. ', '', supervisor.text)])

        # Get the pdf link
        elif tag == '856':
            pdf_link = datafield.find_all('subfield', attrs={'code': 'u'})
            if len(pdf_link) != 0:
                if can_be_downloaded:
                    rec['FFT'] = pdf_link[0].text
                else:
                    rec['hidden'] = pdf_link[0].text

        #department
        elif tag == '910':
            for sf in data:
                if sf['code'] == 'a':
                    dep = sf.text.strip()
                    if dep in boring:
                        keepit = False
                    else:
                        rec['note'].append('dep=%s' % (dep))
                elif sf['code'] == 'b':
                    subdep = sf.text.strip()
                    if subdep in boring:
                        keepit = False
                    else:
                        rec['note'].append('subdep=%s' % (subdep))
        #program
        elif tag == '521':
            for sf in data:
                if sf['code'] == 'a':
                    prg = sf.text.strip()
                    if prg in boring:
                        keepit = False
                    else:
                        rec['note'].append('prg=%s' % (prg))
    
            

        # Write the fake DOI
        rec['doi'] = '20.2000/Zargoza/' + b16encode(url.encode('utf-8')).decode('utf-8')
    if keepit:
        recs.append(rec)
    else:
        newuninterestingDOIS.append(url)
    return


for page in range(pages):
    to_curl = 'https://zaguan.unizar.es/search?cc=tesis&ln=en&rg=' + str(rpp) + '&jrec=' + str(page * rpp + 1)
    driver.get(to_curl)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, to_curl)
    # Get the index links
    for article in BeautifulSoup(driver.page_source, 'lxml').find_all('a', attrs={'class': 'tituloenlazable'}):
        nothing, record, number_and_params = article.get('href').split('/')
        final = '/%s/%s' % (record, number_and_params.split('?')[0])
        finalurl = 'https://zaguan.unizar.es%s/export/xm?ln=en' % final
        if not finalurl in uninterestingDOIS:
            get_sub_site(finalurl)
            sleep(4)
    sleep(10)


#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()


ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()
