# -*- coding: utf-8 -*-
#harvest theses from Figshare
#FS: 2022-02-15

import sys
import datetime
import requests
import time
import urllib3
import json
import re
import ejlmod2
import codecs
import os

urllib3.disable_warnings()

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = '/afs/desy.de/user/l/library/proc/retinspire/retfiles'#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
startdate = '%4d-%02d-%02d' % (now.year-1, now.month, now.day)

srv = sys.argv[1]

rpp = 200
pages = 2
bunchsize = 100
sleepingtime = 3
skipnonlistedcategories = True
apiurl = "https://api.figshare.com/v2/articles/search"
my_secret_token = "df88e4ebd43b823b945a7e6cd4809a579ba7dee9e60ac2e5a1c18874b36d67a128d8b8b447d01fcd521d44e2a8d7128a3bf3b1fb860fb6c1f4aaf77c43dfd0d7"
auth = "Bearer %s" % (my_secret_token)

#categories with fieldcodes
cattofc = {'Computing and Processing' : 'c',
           'Components, Circuits, Devices and Systems' : 'i',
           'Components Circuits Devices and Systems' : 'i',
           'Electronic and Magnetic Properties of Condensed Matter; Superconductivity' : 'f',
           'Software Engineering' : 'c',
           'Stellar Astronomy' : 'a',
           'Galactic Astronomy' : 'a',
           'Cosmology' : 'a',
           'Astrophysics' : 'a',
           'Crystallography' : 'f',
           'Molecular Physics' : 'q',
           'Theoretical Computer Science' : 'c',
           'Applied Computer Science' : 'c',
           'Geophysics' : 'q',
           'Nuclear Engineering' : 'i',
           'Algebra' : 'm',
           'Geometry' : 'm',
           'Probability' : 'm',
           'Statistics' : 'm',
           'Applied Physics' : 'q',
           'Atomic Physics' : 'q',
           'Computational Physics' : 'c',
           'Condensed Matter Physics' : 'f',
           'Mechanics' : 'q',
           'Particle Physics' : '',
           'Plasma Physics' : 'q',
           'Quantum Mechanics' : 'k',
           'Solid Mechanics' : 'q',
           'Thermodynamics' : 'q',
           'Entropy' : 'q',
           'General Relativity' : 'g',
           'M-Theory' : 't',
           'Special Relativity' : 'g',
           'Solar System, Solar Physics, Planets and Exoplanets' : 'a',
           'Space Science' : 'a',
           'Stars, Variable Stars' : 'a',
           'Instrumentation, Techniques, and Astronomical Observations' : 'ai',
           'Interstellar and Intergalactic Matter' : 'a',
           'Extragalactic Astronomy' : 'a',
           'Artificial Intelligence and Image Processing' : 'c',
           'Computation Theory and Mathematics' : 'cm',
           'Computer Software' : 'c',
           'Distributed Computing' : 'c',
           'Classical and Physical Optics' : 'q',
           'Nonlinear Optics and Spectroscopy' : 'q',
           'Photonics, Optoelectronics and Optical Communications' : 'q',
           'Optical Physics not elsewhere classified' : 'q',
           'Degenerate Quantum Gases and Atom Optics' : 'q',
           'Quantum Optics' : 'k',
           'Gravimetrics' : 'g',
           'Astronomical and Space Instrumentation' : 'ai',
           'Cosmology and Extragalactic Astronomy' : 'a',
           'General Relativity and Gravitational Waves' : 'g',
           'High Energy Astrophysics; Cosmic Rays' : 'a',
           'Space and Solar Physics' : 'a',
           'Stellar Astronomy and Planetary Systems' : 'a',
           'Astronomical and Space Sciences not elsewhere classified' : 'a',
           'Photodetectors, Optical Sensors and Solar Cells' : 'i',
           'Signal Processing' : 'i',
           'Signal Processing and Analysis' : 'i',
           'Algebra and Number Theory' : 'm',
           'Algebraic and Differential Geometry' : 'm',
           'Category Theory, K Theory, Homological Algebra' : 'm',
           'Combinatorics and Discrete Mathematics (excl. Physical Combinatorics)' : 'm',
           'Group Theory and Generalisations' : 'm',
           'Lie Groups, Harmonic and Fourier Analysis' : 'm',
           'Mathematical Logic, Set Theory, Lattices and Universal Algebra' : 'm',
           'Operator Algebras and Functional Analysis' : 'm',
           'Ordinary Differential Equations, Difference Equations and Dynamical Systems' : 'm',
           'Partial Differential Equations' : 'm',
           'Real and Complex Functions (incl. Several Variables)' : 'm',
           'Topology' : 'm',
           'Pure Mathematics not elsewhere classified' : 'm',
           'Approximation Theory and Asymptotic Methods' : 'm',
           'Calculus of Variations, Systems Theory and Control Theory' : 'm',
           'Dynamical Systems in Applications' : 'm',
           'Theoretical and Applied Mechanics' : 'q',
           'Applied Mathematics not elsewhere classified' : 'm',
           'Numerical Solution of Differential and Integral Equations' : 'm',
           'Optimisation' : 'm',
           'Numerical and Computational Mathematics not elsewhere classified' : 'm',
           'Applied Statistics' : 'm',
           'Probability Theory' : 'm',
           'Statistical Theory' : 'm',
           'Stochastic Analysis and Modelling' : 'm',
           'Statistics not elsewhere classified' : 'm',
           'Algebraic Structures in Mathematical Physics' : 'm',
           'Integrable Systems (Classical and Quantum)' : 'm',
           'Mathematical Aspects of Classical Mechanics, Quantum Mechanics and Quantum Information Theory' : 'm',
           'Mathematical Aspects of General Relativity' : 'gm',
           'Mathematical Aspects of Quantum and Conformal Field Theory, Quantum Gravity and String Theory' : 'mt',
           'Statistical Mechanics, Physical Combinatorics and Mathematical Aspects of Condensed Matter' : 'mf',
           'Mathematical Physics not elsewhere classified' : 'm',
           'Mathematical Sciences not elsewhere classified' : 'm',
           'Atomic and Molecular Physics' : 'q',
           'Nuclear Physics' : '',
           'Plasma Physics; Fusion Plasmas; Electrical Discharges' : 'q',
           'Atomic, Molecular, Nuclear, Particle and Plasma Physics not elsewhere classified' : 'q',
           'Electrostatics and Electrodynamics' : 'q',
           'Fluid Physics' : 'q',
           'Thermodynamics and Statistical Physics' : 's',
           'Classical Physics not elsewhere classified' : 'q',
           'Condensed Matter Characterisation Technique Development' : 'f',
           'Condensed Matter Imaging' : 'f',
           'Condensed Matter Modelling and Density Functional Theory' : 'f',
           'Electronic and Magnetic Properties of Condensed Matter; Superconductivity' : 'f',
           'Soft Condensed Matter' : 'f',
           'Surfaces and Structural Properties of Condensed Matter' : 'f',
           'Condensed Matter Physics not elsewhere classified' : 'f',
           'Lasers and Quantum Electronics' : 'k',
           'Field Theory and String Theory' : 't',
           'Quantum Information, Computation and Communication' : 'kc',
           'Quantum Physics not elsewhere classified' : 'k',
           'Complex Physical Systems' : 'q',
           'Synchrotrons; Accelerators; Instruments and Techniques' : 'bi',
           'Physical Sciences not elsewhere classified' : 'q',
           'Mathematical Software' : 'mc',
           'Numerical Computation' : 'mc',
           'Computation Theory and Mathematics not elsewhere classified' : 'mc',
           'Distributed and Grid Systems' : 'c',
           'Quantum Chemistry' : 'o'}
cattofc['Fields, Waves and Electromagnetics'] = 'q'

thesesstandardservers = {'kilthub' : 'Carnegie Mellon U. (main)',
                         'melbourne' : 'U. Melbourne (main)', #2
                         'brunel' : 'Brunel U.', #no theses 
                         'auckland' : 'Auckland U.', #6
                         'leicester' : 'Leicester U.',#no theses 
                         'monash' : 'Monash U.',
                         'ryerson' : 'Ryerson U.', 
                         'wgtn' : 'Victoria U., Wellington',#no theses 
                         'lboro' : 'Loughborough U.'} 

###formulate the search statements
payloads = []
#Preprint server TechRxiv
if srv == 'techrxiv':
    publisher = 'IEEE'
    jnl = 'BOOK'
    for cat in ['Computing and Processing', 'Nuclear Engineering',
                'Signal Processing and Analysis', 'Components, Circuits, Devices and Systems']:
        payloads.append(('', {"search": ":institution: %s AND :category: %s" % (srv, cat)}))     
    alloweditems = ['preprint']   
#Stockholm #0
elif srv == 'su':
    publisher = 'Stockholm U. (main)'
    jnl = 'BOOK'
    for cat in cattofc.keys():
        if cattofc[cat] == 'm':
            payloads.append(('Stockholm U., Math. Dept.', {"search": ":institution: %s AND :category: %s AND :item_type: thesis" % (srv, cat)}))
        if cattofc[cat] in ['q', 't', 'k']:
            payloads.append(('Stockholm U.', {"search": ":institution: %s AND :category: %s AND :item_type: thesis" % (srv, cat)}))
        else:
            payloads.append(('Stockholm U. (main)', {"search": ":institution: %s AND :category: %s AND :item_type: thesis" % (srv, cat)}))
    alloweditems = ['thesis']
#standard server for theses
elif srv in thesesstandardservers.keys():
    publisher = thesesstandardservers[srv]
    jnl = 'BOOK'
    for cat in cattofc.keys():
        payloads.append((thesesstandardservers[srv], {"search": ":institution: %s AND :category: %s AND :item_type: thesis" % (srv, cat)}))
    alloweditems = ['thesis']        
    
###search and get indiviual article links
prerecs = []
articleurls = []
for (aff, payload) in payloads:
    payload['page_size'] = rpp
    for page in range(pages):
        payload['page'] = page+1
        print payload
        response = requests.post(apiurl, json=payload, headers={"authorization": auth}, timeout=120, verify=False)
        response.raise_for_status()  # will raise an exception if there's an error
        r = response.json()
        for article in r:
            rec = {'url_public_api' : article['url_public_api'], 'autaff' : [], 'note' : [payload['search']], 'jnl' : jnl}
            if aff:
                rec['affiliation'] = aff
            if article['timeline']['firstOnline'][:10] > startdate:
                if not article['url_public_api'] in articleurls:
                    prerecs.append(rec)
                    articleurls.append(article['url_public_api'] )
        time.sleep(sleepingtime)
        if len(r) < rpp:
            break
    print '-[ %i records so far ]-' % (len(prerecs))

###harvest individual articles
i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    artjson = requests.get(rec['url_public_api']).json()
    #submitter, degree, supervisor, department/
    submitter = ''
    for cf in artjson['custom_fields']:
        if cf['name'] == 'Email Address of Submitting Author':
            submitter = 'submitter: ' + cf['value']
        elif cf['name'] == 'ORCID of Submitting Author':
            submitter += ', ORCID: ' + cf['value']
        elif cf['name'] == 'Degree Name':
            for dn in cf['value']:
                rec['note'].append(cf['name'])
        elif cf['name'] == 'Advisor(s)':
            for sv in re.split(' *\n *', cf['name']):
                if 'supervisor' in rec.keys():
                    rec['supervisor'].append([sv])
                else:
                    rec['supervisor'] = [[sv]]
        elif cf['name'] == 'Department':
            for dep in cf['value']:
                rec['note'].append('department: '+dep)
    if submitter:
        rec['note'].append(submitter)
    #doctype
    if 'defined_type_name' in artjson.keys():
        if artjson['defined_type_name'] == 'preprint':
            rec['tc'] = ''
        elif artjson['defined_type_name'] == 'thesis':
            rec['tc'] = 'T'
        elif artjson['defined_type_name'] == 'monograph':
            rec['tc'] = 'B'
        elif artjson['defined_type_name'] == 'journal contribution':
            rec['tc'] = 'P'
        elif artjson['defined_type_name'] == 'conference contribution':
            rec['tc'] = 'C'
        elif artjson['defined_type_name'] == 'chapter':
            rec['tc'] = 'S'
        else:
            rec['tc'] = ''
        if not artjson['defined_type_name'] in alloweditems:
            keepit = False
            print '  skip "%s"' % (artjson['defined_type_name'])
    #categories
    if 'categories' in artjson.keys():
        for cat in artjson['categories']:
            if cat['title'] in cattofc.keys():
                rec['note'].append('category: ' + cat['title'])
                if cattofc[cat['title']]:
                    if 'fc' in rec.keys():
                        if not cattofc[cat['title']] in rec['fc']:
                            rec['fc'] += cattofc[cat['title']]
                    else:
                        rec['fc'] = cattofc[cat['title']]
            else:
                rec['note'].append('category: ' + cat['title'] + '???')
                if skipnonlistedcategories:
                    keepit = False
                    print '  skip "%s"' % (cat['title'])
    #authos
    if 'authors' in artjson.keys():
        for author in artjson['authors']:
            rec['autaff'].append([author['full_name']])
            if 'orcid_id' in author.keys() and author['orcid_id'] :
                rec['autaff'][-1].append('ORCID:'+author['orcid_id'])
            if 'affiliation' in rec.keys():
                rec['autaff'][-1].append(rec['affiliation'])
    #title
    if 'title' in artjson.keys():
        rec['tit'] = artjson['title']
    #abstract
    if 'description' in artjson.keys():
        rec['abs'] = artjson['description']
    #license
    if 'license' in artjson.keys():
        if re.search('creativecommons', artjson['license']['url']):
            rec['license'] = {'url' : artjson['license']['url']}
    #keywords
    if 'tags' in artjson.keys():
        rec['keyw'] = artjson['tags']
    #PID
    if 'doi' in artjson.keys() and artjson['doi']:
        rec['doi'] = artjson['doi']
    if 'handle' in artjson.keys() and artjson['handle']:
        rec['hdl'] = artjson['handle']
    #date
    if 'published_date' in artjson.keys():
        rec['date'] = artjson['published_date']
    #FFT
    if 'files' in artjson.keys():
        if len(artjson['files']) > 1:
            rec['note'].append('%i files attached' % (len(artjson['files'])))
        for file in artjson['files']:
            if 'license' in rec.keys():
                rec['FFT'] = file['download_url']
            else:
                rec['hidden'] = file['download_url']
    #link
    if not 'doi' in rec.keys() and not 'hdl' in rec.keys():
        rec['link'] = artjson['url_public_html']
    if keepit:
        recs.append(rec)
        print '%4i/%i' % (i, len(prerecs)), rec.keys()
    time.sleep(sleepingtime)

numfbunches = (len(recs)-1) / bunchsize + 1
for i in range(numfbunches):
    jnlfilename = 'figshare.%s.%s.%i_of_%i' % (srv, stampoftoday, i+1, numfbunches)
    bunchrecs = recs[bunchsize*i:bunchsize*(i+1)]
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(bunchrecs, xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, 'r').read()
    line = jnlfilename+'.xml'+ '\n'
    if not line in retfiles_text: 
        retfiles = open(retfiles_path, 'a')
        retfiles.write(line)
        retfiles.close()
   
