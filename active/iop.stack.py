# -*- coding: UTF-8 -*-
# checks for new ftp-feeds from IOP and converts them
# FS 2020-05-04

import os
import sys
import re
import time
import datetime
import codecs
from bs4 import BeautifulSoup
import urllib2
import urlparse
import ejlmod2
import tarfile
import shutil

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
iopdirtmp = '/afs/desy.de/group/library/publisherdata/iop/tmp'
iopdirraw = '/afs/desy.de/group/library/publisherdata/iop/raw'
iopdirdone = '/afs/desy.de/group/library/publisherdata/iop/done'
pdfdir = '/afs/desy.de/group/library/publisherdata/pdf'
publisher = 'IOP'
ftpdir = "/afs/desy.de/group/library/preprints/incoming/IOP"

#ISSN to journal name
jnl = {'1538-3881': 'Astron.J.',
       '0004-637X': 'Astrophys.J.',
       '1538-4357': 'Astrophys.J.Lett.',
       '2041-8205': 'Astrophys.J.Lett.',
       '0067-0049': 'Astrophys.J.Supp.',
       '0264-9381': 'Class.Quant.Grav.',
       '1009-9271': 'Chin.J.Astron.Astrophys.',
       '1009-1963': 'Chin.Phys.',
       '1674-1056': 'Chin.Phys.',
       '1674-1137': 'Chin.Phys.',
       '0256-307X': 'Chin.Phys.Lett.',
       '0253-6102': 'Commun.Theor.Phys.',
       '0143-0807': 'Eur.J.Phys.',
       '0295-5075': 'EPL',
       '1757-899X': 'IOP Conf.Ser.Mater.Sci.Eng.',
       '1751-8121': 'J.Phys.',
       '0953-4075': 'J.Phys.',
       '2399-6528': 'J.Phys.Comm.',
       '0953-8984': 'J.Phys.Condens.Matter',
       '1742-6596': 'J.Phys.Conf.Ser.',
       '0954-3899': 'J.Phys.',
       '1475-7516': 'JCAP',
       '1126-6708': 'JHEP',
       '1748-0221': 'JINST',
       '1742-5468': 'JSTAT',
       '0957-0233': 'Measur.Sci.Tech.',
       '0026-1394': 'Metrologia',
       '1367-2630': 'New J.Phys.',
       '0951-7715': 'Nonlinearity',
       '0031-9120': 'Phys.Educ.',
       '0031-9155': 'Phys.Med.Biol.',
       '1402-4896': 'Phys.Scripta',
       '1063-7869': 'Phys.Usp.',
       '0741-3335': 'Plasma Phys.Control.Fusion',
       '1538-3873': 'Publ.Astron.Soc.Pac.',
       '0034-4885': 'Rep.Prog.Phys.',
       '1674-4527': 'Res.Astron.Astrophys.',
       '0036-0279': 'Russ.Math.Surveys',
       '0953-2048': 'Supercond.Sci.Technol.'}
jnl['2516-1067'] = 'Plasma Res.Express'

#uninteresting journals in feed
jnlskip = {'2058-8585' : 'Flexible and Printed Electronics'}

#CNUMs for conferences in JINST
cnumdict = {'12th Workshop on Resistive Plate Chambers and Related Detectors (RPC2014)': 'C14-02-23.2',
            '12th Workshop on Resistive Plate Chambers and Related Detectors': 'C14-02-23.2',
            'International Conference on Instrumentation for Colliding Beam Physics (INSTR14)': 'C14-02-24',
            'Topical Workshop on Electronics for Particle Physics 2013 (TWEPP-13)': 'C13-09-23',
            '13th Topical Seminar on Innovative Particle and Radiation Detectors (IPRD13)': 'C13-10-07',
            'Precision Astronomy with Fully Depleted CCDS (PACCD2013)': 'C13-11-18.1',
            '10th International Conference on Position Sensitive Detectors (PSD10)': 'C14-09-07',
            '10th International Conference on Position Sensitive Detectors': 'C14-09-07',
            'Workshop on Intelligent Trackers (WIT2014)': 'C14-05-14',
            'TWEPP2014': 'C14-09-22.7',
            '7th International Workshop on Semiconductor Pixel Detectors for Particles and Imaging': 'C14-09-01.3',
            '16th International Workshop on Radiation Imaging Detectors': 'C14-06-22.3',
            'Precision Astronomy with Fully Depleted CCDS(2014)': 'C14-12-04.1',
            '2nd International Summer School on Intelligent Signal Processing for Frontier Research and Industry': 'C14-07-15',
            '17th International Workshop on Radiation Imaging Detectors': 'C15-06-28.1',
            'Light Detection in Noble Elements (LIDINE 2015)': 'C15-08-28',
            '13th Workshop on Resistive Plate Chambers and Related Detectors (RPC2016)': 'C16-02-22.3',
            '17th International Symposium on Laser-Aided Plasma Diagnostics (LAPD17)' : 'C15-09-27.1',
            'TWEPP2015': 'C15-09-28',
            'International Workshop on Fast Cherenkov Detectors - Photon detection, DIRC design and DAQ (DIRC2015)' : 'C15-11-11.2',
            '4th International Conference Frontiers in Diagnostics Fix Technologies (ICFDT4)': 'C16-03-30.5',
            '18th International Workshop on Radiation Imaging Detectors (IWORID2016)' : 'C16-07-03.1',
            '14th Topical Seminar on Innovative Particle and Radiation Detectors' : 'C16-10-03',
            'International Workshop on Semiconductor Pixel Detectors for Particles and Imaging (Pixel 2016)' : 'C16-09-05.3',
            '14th Topical Seminar on Innovative Particle and Radiation Detectors (IPRD16)' : 'C16-10-03',
            'Topical Workshop on Electronics for Particle Physics (TWEPP2016)' : 'C16-09-26.4',
            'International Conference on Instrumentation for Colliding Beam Physics (INSTR17)' : 'C17-02-27',
            'Precision Astronomy with Fully Depleted CCDS (PACCD2016)' : 'C16-12-01.1',
            '19th International Workshop on Radiation Imaging Detectors (IWORID2017)' : 'C17-07-02.5',
            '11th International Conference on Position Sensitive Detectors (PSD11)' : 'C17-09-03.2',
            'Calorimetry for the High Energy Frontier (CHEF2017)' : 'C17-10-02.3',
            'XII International Symposium on Radiation from Relativistic Electrons in Periodic Structures (RREPS-17)' : 'C17-09-18.6',
            'International Workshop on Fast Cherenkov Detectors - Photon detection, DIRC design and DAQ (DIRC2017)' : 'C17-08-07.6',
            'Light Detection in Noble Elements (LIDINE2017)' : 'C17-09-22',
            'XII International Symposium on Radiation from Relativistic Electrons in Periodic Structures (RREPS-17)' : 'C17-09-18.6',
            '24th International congress on x-ray optics and microanalysis (ICXOM24)' : 'C17-09-25.6',
            '20th International Workshop On Radiation Imaging Detectors' : 'C18-06-24.2',
            '5th International Conference Frontiers in Diagnostcs Technologies (ICFDT)' : 'C18-10-03.1',
            'The 9th International Workshop on Semiconductor Pixel Detectors for Particles and Imaging' : 'C18-12-10',
            '14th Workshop on Resistive Plate Chambers and Related Detectors (RPC2018)' : 'C18-02-19.3',
            'RPC2018' : 'C18-02-19.3',
            'PIXEL2018' : 'C18-12-10',
            '3rd European Conference on Plasma Diagnostics (ECPD2019)' : 'C19-05-06.5',
            'ECPD2019' : 'C19-05-06.5',
            '20th International Workshop On Radiation Imaging Detectors' : 'C18-06-24.2',
            'LAPD19' : 'C19-09-22.5',
            'IWORID2019' : 'C19-07-07.2',
            'RREPS-19' : 'C19-09-16.8',
            'IPRD19' : 'C19-10-14.1',
            'DIRC2019' : 'C19-09-11.1',
            'INFIERI 2019' : 'C19-05-12.3',
            'LIDINE2019' : 'C19-08-28',
            'RPC2018' : 'C18-02-19.3',
            'CHEF2019' : 'C19-11-25.3',
            'The International Conference Instrumentation for Colliding Beam Physics (INSTR2020)' : 'C20-02-24',
            'RREPS-19' : 'C19-09-16.8',
            'XV Workshop on Resistive Plate Chambers and Related Detectors (RPC2020)' : 'C20-02-10.1'}


bisac = {'SCI000000' : 'SCIENCE / General',
         'SCI001000' : 'SCIENCE / Acoustics & Sound',
         'SCI003000' : 'SCIENCE / Applied Sciences',
         'SCI004000' : 'SCIENCE / Astronomy',
         'SCI005000' : 'SCIENCE / Astrophysics & Space Science',
         'SCI010000' : 'SCIENCE / Biotechnology',
         'SCI012000' : 'SCIENCE / Chaotic Behavior in Systems',
         'SCI013000' : 'SCIENCE / Chemistry / General',
         'SCI013010' : 'SCIENCE / Chemistry / Analytic',
         'SCI013020' : 'SCIENCE / Chemistry / Clinical',
         'SCI013060' : 'SCIENCE / Chemistry / Industrial & Technical',
         'SCI013030' : 'SCIENCE / Chemistry / Inorganic',
         'SCI013040' : 'SCIENCE / Chemistry / Organic',
         'SCI013050' : 'SCIENCE / Chemistry / Physical & Theoretical',
         'SCI015000' : 'SCIENCE / Cosmology',
         'SCI016000' : 'SCIENCE / Crystallography',
         'SCI019000' : 'SCIENCE / Earth Sciences / General',
         'SCI030000' : 'SCIENCE / Earth Sciences / Geography',
         'SCI031000' : 'SCIENCE / Earth Sciences / Geology',
         'SCI081000' : 'SCIENCE / Earth Sciences / Hydrology',
         'SCI042000' : 'SCIENCE / Earth Sciences / Meteorology & Climatology',
         'SCI048000' : 'SCIENCE / Earth Sciences / Mineralogy',
         'SCI052000' : 'SCIENCE / Earth Sciences / Oceanography',
         'SCI082000' : 'SCIENCE / Earth Sciences / Seismology & Volcanism',
         'SCI021000' : 'SCIENCE / Electricity',
         'SCI022000' : 'SCIENCE / Electromagnetism',
         'SCI023000' : 'SCIENCE / Electron Microscopes & Microscopy',
         'SCI024000' : 'SCIENCE / Energy',
         'SCI026000' : 'SCIENCE / Environmental Science',
         'SCI080000' : 'SCIENCE / Essays',
         'SCI028000' : 'SCIENCE / Experiments & Projects',
         'SCI032000' : 'SCIENCE / Geophysics',
         'SCI033000' : 'SCIENCE / Gravity',
         'SCI034000' : 'SCIENCE / History',
         'SCI086000' : 'SCIENCE / Life Sciences / General',
         'SCI056000' : 'SCIENCE / Life Sciences / Anatomy & Physiology (see also Life Sciences / Human Anatomy & Physiology)',
         'SCI006000' : 'SCIENCE / Life Sciences / Bacteriology',
         'SCI007000' : 'SCIENCE / Life Sciences / Biochemistry',
         'SCI008000' : 'SCIENCE / Life Sciences / Biology / General',
         'SCI072000' : 'SCIENCE / Life Sciences / Biology / Developmental Biology',
         'SCI039000' : 'SCIENCE / Life Sciences / Biology / Marine Biology',
         'SCI045000' : 'SCIENCE / Life Sciences / Biology / Microbiology',
         'SCI049000' : 'SCIENCE / Life Sciences / Biology / Molecular Biology',
         'SCI009000' : 'SCIENCE / Life Sciences / Biophysics',
         'SCI011000' : 'SCIENCE / Life Sciences / Botany',
         'SCI017000' : 'SCIENCE / Life Sciences / Cytology',
         'SCI020000' : 'SCIENCE / Life Sciences / Ecology',
         'SCI027000' : 'SCIENCE / Life Sciences / Evolution',
         'SCI029000' : 'SCIENCE / Life Sciences / Genetics & Genomics',
         'SCI073000' : 'SCIENCE / Life Sciences / Horticulture',
         'SCI036000' : 'SCIENCE / Life Sciences / Human Anatomy & Physiology',
         'SCI087000' : 'SCIENCE / Life Sciences / Taxonomy',
         'SCI070000' : 'SCIENCE / Life Sciences / Zoology / General',
         'SCI025000' : 'SCIENCE / Life Sciences / Zoology / Entomology',
         'SCI070010' : 'SCIENCE / Life Sciences / Zoology / Ichthyology',
         'SCI070020' : 'SCIENCE / Life Sciences / Zoology / Invertebrates',
         'SCI070030' : 'SCIENCE / Life Sciences / Zoology / Mammals',
         'SCI070040' : 'SCIENCE / Life Sciences / Zoology / Ornithology',
         'SCI070050' : 'SCIENCE / Life Sciences / Zoology / Primatology',
         'SCI037000' : 'SCIENCE / Light',
         'SCI083000' : 'SCIENCE / Limnology',
         'SCI038000' : 'SCIENCE / Magnetism',
         'SCI040000' : 'SCIENCE / Mathematical Physics',
         'SCI041000' : 'SCIENCE / Mechanics / General',
         'SCI018000' : 'SCIENCE / Mechanics / Dynamics / General',
         'SCI084000' : 'SCIENCE / Mechanics / Dynamics / Aerodynamics',
         'SCI085000' : 'SCIENCE / Mechanics / Dynamics / Fluid Dynamics',
         'SCI065000' : 'SCIENCE / Mechanics / Dynamics / Thermodynamics',
         'SCI079000' : 'SCIENCE / Mechanics / Statics',
         'SCI044000' : 'SCIENCE / Metric System',
         'SCI047000' : 'SCIENCE / Microscopes & Microscopy',
         'SCI074000' : 'SCIENCE / Molecular Physics',
         'SCI050000' : 'SCIENCE / Nanostructures',
         'SCI051000' : 'SCIENCE / Nuclear Physics',
         'SCI053000' : 'SCIENCE / Optics',
         'SCI054000' : 'SCIENCE / Paleontology',
         'SCI075000' : 'SCIENCE / Philosophy & Social Aspects',
         'SCI055000' : 'SCIENCE / Physics',
         'SCI057000' : 'SCIENCE / Quantum Theory',
         'SCI058000' : 'SCIENCE / Radiation',
         'SCI059000' : 'SCIENCE / Radiology',
         'SCI060000' : 'SCIENCE / Reference',
         'SCI061000' : 'SCIENCE / Relativity',
         'SCI043000' : 'SCIENCE / Research & Methodology',
         'SCI076000' : 'SCIENCE / Scientific Instruments',
         'SCI077000' : 'SCIENCE / Solid State Physics',
         'SCI078000' : 'SCIENCE / Spectroscopy & Spectrum Analysis',
         'SCI063000' : 'SCIENCE / Study & Teaching',
         'SCI064000' : 'SCIENCE / System Theory',
         'SCI066000' : 'SCIENCE / Time',
         'SCI067000' : 'SCIENCE / Waves & Wave Mechanics',
         'SCI068000' : 'SCIENCE / Weights & Measures',
         'MAT000000' : 'MATHEMATICS / General',
         'MAT001000' : 'MATHEMATICS / Advanced',
         'MAT002000' : 'MATHEMATICS / Algebra / General',
         'MAT002010' : 'MATHEMATICS / Algebra / Abstract',
         'MAT002030' : 'MATHEMATICS / Algebra / Elementary',
         'MAT002040' : 'MATHEMATICS / Algebra / Intermediate',
         'MAT002050' : 'MATHEMATICS / Algebra / Linear',
         'MAT003000' : 'MATHEMATICS / Applied',
         'MAT004000' : 'MATHEMATICS / Arithmetic',
         'MAT005000' : 'MATHEMATICS / Calculus',
         'MAT036000' : 'MATHEMATICS / Combinatorics',
         'MAT006000' : 'MATHEMATICS / Counting & Numeration',
         'MAT007000' : 'MATHEMATICS / Differential Equations',
         'MAT008000' : 'MATHEMATICS / Discrete Mathematics',
         'MAT039000' : 'MATHEMATICS / Essays',
         'MAT009000' : 'MATHEMATICS / Finite Mathematics',
         'MAT037000' : 'MATHEMATICS / Functional Analysis',
         'MAT011000' : 'MATHEMATICS / Game Theory',
         'MAT012000' : 'MATHEMATICS / Geometry / General',
         'MAT012010' : 'MATHEMATICS / Geometry / Algebraic',
         'MAT012020' : 'MATHEMATICS / Geometry / Analytic',
         'MAT012030' : 'MATHEMATICS / Geometry / Differential',
         'MAT012040' : 'MATHEMATICS / Geometry / Non-Euclidean',
         'MAT013000' : 'MATHEMATICS / Graphic Methods',
         'MAT014000' : 'MATHEMATICS / Group Theory',
         'MAT015000' : 'MATHEMATICS / History & Philosophy',
         'MAT016000' : 'MATHEMATICS / Infinity',
         'MAT017000' : 'MATHEMATICS / Linear Programming',
         'MAT018000' : 'MATHEMATICS / Logic',
         'MAT034000' : 'MATHEMATICS / Mathematical Analysis',
         'MAT019000' : 'MATHEMATICS / Matrices',
         'MAT020000' : 'MATHEMATICS / Mensuration',
         'MAT021000' : 'MATHEMATICS / Number Systems',
         'MAT022000' : 'MATHEMATICS / Number Theory',
         'MAT023000' : 'MATHEMATICS / Pre-Calculus',
         'MAT029000' : 'MATHEMATICS / Probability & Statistics / General',
         'MAT029010' : 'MATHEMATICS / Probability & Statistics / Bayesian Analysis',
         'MAT029020' : 'MATHEMATICS / Probability & Statistics / Multivariate Analysis',
         'MAT029030' : 'MATHEMATICS / Probability & Statistics / Regression Analysis',
         'MAT025000' : 'MATHEMATICS / Recreations & Games',
         'MAT026000' : 'MATHEMATICS / Reference',
         'MAT027000' : 'MATHEMATICS / Research',
         'MAT028000' : 'MATHEMATICS / Set Theory',
         'MAT030000' : 'MATHEMATICS / Study & Teaching',
         'MAT038000' : 'MATHEMATICS / Topology',
         'MAT031000' : 'MATHEMATICS / Transformations',
         'MAT032000' : 'MATHEMATICS / Trigonometry',
         'MAT033000' : 'MATHEMATICS / Vector Analysis',
         'TEC000000' : 'TECHNOLOGY / General',
         'TEC001000' : 'TECHNOLOGY / Acoustics & Sound',
         'TEC002000' : 'TECHNOLOGY / Aeronautics & Astronautics',
         'TEC003000' : 'TECHNOLOGY / Agriculture / General',
         'TEC003020' : 'TECHNOLOGY / Agriculture / Animal Husbandry',
         'TEC003030' : 'TECHNOLOGY / Agriculture / Crop Science',
         'TEC003040' : 'TECHNOLOGY / Agriculture / Forestry',
         'TEC003050' : 'TECHNOLOGY / Agriculture / Irrigation',
         'TEC003060' : 'TECHNOLOGY / Agriculture / Soil Science',
         'TEC003070' : 'TECHNOLOGY / Agriculture / Sustainable Agriculture',
         'TEC003010' : 'TECHNOLOGY / Agriculture / Tropical Agriculture',
         'TEC004000' : 'TECHNOLOGY / Automation',
         'TEC048000' : 'TECHNOLOGY / Cartography',
         'TEC005000' : 'TECHNOLOGY / Construction / General',
         'TEC005010' : 'TECHNOLOGY / Construction / Carpentry',
         'TEC005020' : 'TECHNOLOGY / Construction / Contracting',
         'TEC005030' : 'TECHNOLOGY / Construction / Electrical',
         'TEC005040' : 'TECHNOLOGY / Construction / Estimating',
         'TEC005050' : 'TECHNOLOGY / Construction / Heating, Ventilation & Air Conditioning',
         'TEC005060' : 'TECHNOLOGY / Construction / Masonry',
         'TEC005070' : 'TECHNOLOGY / Construction / Plumbing',
         'TEC005080' : 'TECHNOLOGY / Construction / Roofing',
         'TEC006000' : 'TECHNOLOGY / Drafting & Mechanical Drawing',
         'TEC007000' : 'TECHNOLOGY / Electricity',
         'TEC008000' : 'TECHNOLOGY / Electronics / General',
         'TEC008010' : 'TECHNOLOGY / Electronics / Circuits / General',
         'TEC008020' : 'TECHNOLOGY / Electronics / Circuits / Integrated',
         'TEC008030' : 'TECHNOLOGY / Electronics / Circuits / Logic',
         'TEC008040' : 'TECHNOLOGY / Electronics / Circuits / Printed',
         'TEC008050' : 'TECHNOLOGY / Electronics / Circuits / VLSI',
         'TEC008060' : 'TECHNOLOGY / Electronics / Digital',
         'TEC008070' : 'TECHNOLOGY / Electronics / Microelectronics',
         'TEC008080' : 'TECHNOLOGY / Electronics / Optoelectronics',
         'TEC008090' : 'TECHNOLOGY / Electronics / Semiconductors',
         'TEC008100' : 'TECHNOLOGY / Electronics / Solid State',
         'TEC008110' : 'TECHNOLOGY / Electronics / Transistors',
         'TEC009000' : 'TECHNOLOGY / Engineering / General',
         'TEC009090' : 'TECHNOLOGY / Engineering / Automotive',
         'TEC009010' : 'TECHNOLOGY / Engineering / Chemical & Biochemical',
         'TEC009020' : 'TECHNOLOGY / Engineering / Civil',
         'TEC009030' : 'TECHNOLOGY / Engineering / Electrical',
         'TEC009050' : 'TECHNOLOGY / Engineering / Hydraulic',
         'TEC009060' : 'TECHNOLOGY / Engineering / Industrial',
         'TEC009070' : 'TECHNOLOGY / Engineering / Mechanical',
         'TEC009080' : 'TECHNOLOGY / Engineering / Nuclear',
         'TEC010000' : 'TECHNOLOGY / Environmental Engineering & Technology',
         'TEC011000' : 'TECHNOLOGY / Fiber Optics',
         'TEC045000' : 'TECHNOLOGY / Fire Science',
         'TEC049000' : 'TECHNOLOGY / Fisheries & Aquaculture',
         'TEC012000' : 'TECHNOLOGY / Food Science',
         'TEC013000' : 'TECHNOLOGY / Fracture Mechanics',
         'TEC056000' : 'TECHNOLOGY / History',
         'TEC050000' : 'TECHNOLOGY / Holography',
         'TEC014000' : 'TECHNOLOGY / Hydraulics',
         'TEC015000' : 'TECHNOLOGY / Imaging Systems',
         'TEC016000' : 'TECHNOLOGY / Industrial Design / General',
         'TEC016010' : 'TECHNOLOGY / Industrial Design / Packaging',
         'TEC016020' : 'TECHNOLOGY / Industrial Design / Product',
         'TEC017000' : 'TECHNOLOGY / Industrial Health & Safety',
         'TEC018000' : 'TECHNOLOGY / Industrial Technology',
         'TEC057000' : 'TECHNOLOGY / Inventions',
         'TEC019000' : 'TECHNOLOGY / Lasers',
         'TEC046000' : 'TECHNOLOGY / Machinery',
         'TEC020000' : 'TECHNOLOGY / Manufacturing',
         'TEC021000' : 'TECHNOLOGY / Material Science',
         'TEC022000' : 'TECHNOLOGY / Mensuration',
         'TEC023000' : 'TECHNOLOGY / Metallurgy',
         'TEC024000' : 'TECHNOLOGY / Microwaves',
         'TEC025000' : 'TECHNOLOGY / Military Science',
         'TEC026000' : 'TECHNOLOGY / Mining',
         'TEC027000' : 'TECHNOLOGY / Nanotechnology',
         'TEC028000' : 'TECHNOLOGY / Nuclear Energy',
         'TEC029000' : 'TECHNOLOGY / Operations Research',
         'TEC030000' : 'TECHNOLOGY / Optics',
         'TEC058000' : 'TECHNOLOGY / Pest Control',
         'TEC047000' : 'TECHNOLOGY / Petroleum',
         'TEC031000' : 'TECHNOLOGY / Power Resources',
         'TEC032000' : 'TECHNOLOGY / Quality Control',
         'TEC033000' : 'TECHNOLOGY / Radar',
         'TEC034000' : 'TECHNOLOGY / Radio',
         'TEC035000' : 'TECHNOLOGY / Reference',
         'TEC036000' : 'TECHNOLOGY / Remote Sensing',
         'TEC037000' : 'TECHNOLOGY / Robotics',
         'TEC038000' : 'TECHNOLOGY / Scanning Systems',
         'TEC052000' : 'TECHNOLOGY / Social Aspects',
         'TEC039000' : 'TECHNOLOGY / Superconductors & Superconductivity',
         'TEC054000' : 'TECHNOLOGY / Surveying',
         'TEC040000' : 'TECHNOLOGY / Technical & Manufacturing Industries & Trades',
         'TEC044000' : 'TECHNOLOGY / Technical Writing',
         'TEC041000' : 'TECHNOLOGY / Telecommunications',
         'TEC043000' : 'TECHNOLOGY / Television & Video',
         'TEC055000' : 'TECHNOLOGY / Textiles & Polymers'}


bic = {'P' : 'Mathematics & science',
       'PB' : 'Mathematics',
       'PBB' : 'Philosophy of mathematics',
       'PBC' : 'Mathematical foundations',
       'PBCD' : 'Mathematical logic',
       'PBCH' : 'Set theory',
       'PBCN' : 'Number systems',
       'PBD' : 'Discrete mathematics',
       'PBF' : 'Algebra',
       'PBG' : 'Groups & group theory',
       'PBH' : 'Number theory',
       'PBJ' : 'Pre-calculus',
       'PBK' : 'Calculus & mathematical analysis',
       'PBKA' : 'Calculus',
       'PBKB' : 'Real analysis, real variables',
       'PBKD' : 'Complex analysis, complex variables',
       'PBKF' : 'Functional analysis & transforms',
       'PBKJ' : 'Differential calculus & equations',
       'PBKL' : 'Integral calculus & equations',
       'PBKQ' : 'Calculus of variations',
       'PBKS' : 'Numerical analysis',
       'PBM' : 'Geometry',
       'PBMB' : 'Trigonometry',
       'PBMH' : 'Euclidean geometry',
       'PBML' : 'Non-Euclidean geometry',
       'PBMP' : 'Differential & Riemannian geometry',
       'PBMS' : 'Analytic geometry',
       'PBMW' : 'Algebraic geometry',
       'PBMX' : 'Fractal geometry',
       'PBP' : 'Topology',
       'PBPD' : 'Algebraic topology',
       'PBPH' : 'Analytic topology',
       'PBT' : 'Probability & statistics',
       'PBTB' : 'Bayesian inference',
       'PBU' : 'Optimization',
       'PBUD' : 'Game theory',
       'PBUH' : 'Linear programming',
       'PBV' : 'Combinatorics & graph theory',
       'PBW' : 'Applied mathematics',
       'PBWH' : 'Mathematical modelling',
       'PBWL' : 'Stochastics',
       'PBWR' : 'Nonlinear science',
       'PBWS' : 'Chaos theory',
       'PBWX' : 'Fuzzy set theory',
       'PBX' : 'History of mathematics',
       'PD' : 'Science: general issues',
       'PDA' : 'Philosophy of science',
       'PDC' : 'Scientific nomenclature & classification',
       'PDD' : 'Scientific standards',
       'PDDM' : 'Mensuration & systems of measurement',
       'PDE' : 'Maths for scientists',
       'PDG' : 'Industrial applications of scientific research & technological innovation',
       'PDK' : 'Science funding & policy',
       'PDN' : 'Scientific equipment, experiments & techniques',
       'PDND' : 'Microscopy',
       'PDR' : 'Impact of science & technology on society',
       'PDX' : 'History of science',
       'PDZ' : 'Popular science',
       'PDZM' : 'Popular mathematics',
       'PG' : 'Astronomy, space & time',
       'PGC' : 'Theoretical & mathematical astronomy',
       'PGG' : 'Astronomical observation: observatories, equipment & methods',
       'PGK' : 'Cosmology & the universe',
       'PGM' : 'Galaxies & stars',
       'PGS' : 'Solar system: the Sun & planets',
       'PGT' : 'Astronomical charts & atlases',
       'PGZ' : 'Time (chronology), time systems & standards',
       'PH' : 'Physics',
       'PHD' : 'Classical mechanics',
       'PHDB' : 'Elementary mechanics',
       'PHDD' : 'Analytical mechanics',
       'PHDF' : 'Fluid mechanics',
       'PHDS' : 'Wave mechanics (vibration & acoustics)',
       'PHDT' : 'Dynamics & statics',
       'PHDV' : 'Gravity',
       'PHDY' : 'Energy',
       'PHF' : 'Materials / States of matter',
       'PHFB' : 'Low temperature physics',
       'PHFC' : 'Condensed matter physics (liquid state & solid state physics)',
       'PHFC1' : 'Soft matter physics',
       'PHFC2' : 'Mesoscopic physics',
       'PHFG' : 'Physics of gases',
       'PHFP' : 'Plasma physics',
       'PHH' : 'Thermodynamics & heat',
       'PHJ' : 'Optical physics',
       'PHJL' : 'Laser physics',
       'PHK' : 'Electricity, electromagnetism & magnetism',
       'PHM' : 'Atomic & molecular physics',
       'PHN' : 'Nuclear physics',
       'PHP' : 'Particle & high-energy physics',
       'PHQ' : 'Quantum physics (quantum mechanics & quantum field theory)',
       'PHR' : 'Relativity physics',
       'PHS' : 'Statistical physics',
       'PHU' : 'Mathematical physics',
       'PHV' : 'Applied physics',
       'PHVB' : 'Astrophysics',
       'PHVD' : 'Medical physics',
       'PHVG' : 'Geophysics',
       'PHVJ' : 'Atmospheric physics',
       'PHVN' : 'Biophysics',
       'PHVQ' : 'Chemical physics',
       'PHVS' : 'Cryogenics',
       'PN' : 'Chemistry',
       'PNF' : 'Analytical chemistry',
       'PNFC' : 'Chromatography',
       'PNFR' : 'Magnetic resonance',
       'PNFS' : 'Spectrum analysis, spectrochemistry, mass spectrometry',
       'PNK' : 'Inorganic chemistry',
       'PNN' : 'Organic chemistry',
       'PNND' : 'Organometallic chemistry',
       'PNNP' : 'Polymer chemistry',
       'PNR' : 'Physical chemistry',
       'PNRC' : 'Colloid chemistry',
       'PNRD' : 'Catalysis',
       'PNRH' : 'Electrochemistry & magnetochemistry',
       'PNRL' : 'Nuclear chemistry, photochemistry & radiation',
       'PNRP' : 'Quantum & theoretical chemistry',
       'PNRS' : 'Solid state chemistry',
       'PNRW' : 'Thermochemistry & chemical thermodynamics',
       'PNRX' : 'Surface chemistry & adsorption',
       'PNT' : 'Crystallography',
       'PNV' : 'Mineralogy & gems',
       'PS' : 'Biology, life sciences',
       'PSA' : 'Life sciences: general issues',
       'PSAB' : 'Taxonomy & systematics',
       'PSAD' : 'Bio-ethics',
       'PSAF' : 'Ecological science, the Biosphere',
       'PSAG' : 'Xenobiotics',
       'PSAJ' : 'Evolution',
       'PSAK' : 'Genetics (non-medical)',
       'PSAK1' : 'DNA & Genome',
       'PSAN' : 'Neurosciences',
       'PSB' : 'Biochemistry',
       'PSBC' : 'Proteins',
       'PSBF' : 'Carbohydrates',
       'PSBH' : 'Lipids',
       'PSBM' : 'Biochemical immunology',
       'PSBT' : 'Toxicology (non-medical)',
       'PSBZ' : 'Enzymology',
       'PSC' : 'Developmental biology',
       'PSD' : 'Molecular biology',
       'PSF' : 'Cellular biology (cytology)',
       'PSG' : 'Microbiology (non-medical)',
       'PSGD' : 'Bacteriology (non-medical)',
       'PSGH' : 'Parasitology (non-medical)',
       'PSGL' : 'Virology (non-medical)',
       'PSGN' : 'Protozoa',
       'PSP' : 'Hydrobiology',
       'PSPF' : 'Freshwater biology',
       'PSPM' : 'Marine biology',
       'PSQ' : 'Mycology, fungi (non-medical)',
       'PST' : 'Botany & plant sciences',
       'PSTD' : 'Plant physiology',
       'PSTL' : 'Plant reproduction & propagation',
       'PSTP' : 'Plant pathology & diseases',
       'PSTS' : 'Plant ecology',
       'PSTV' : 'Phycology, algae & lichens',
       'PSV' : 'Zoology & animal sciences',
       'PSVD' : 'Animal physiology',
       'PSVH' : 'Animal reproduction',
       'PSVL' : 'Animal pathology & diseases',
       'PSVP' : 'Animal behaviour',
       'PSVS' : 'Animal ecology',
       'PSVT' : 'Zoology: Invertebrates',
       'PSVT3' : 'Molluscs',
       'PSVT5' : 'Crustaceans',
       'PSVT6' : 'Arachnids',
       'PSVT7' : 'Insects (entomology)',
       'PSVW' : 'Zoology: Vertebrates',
       'PSVW1' : 'Fishes (ichthyology)',
       'PSVW3' : 'Amphibians',
       'PSVW5' : 'Reptiles',
       'PSVW6' : 'Birds (ornithology)',
       'PSVW7' : 'Zoology: Mammals',
       'PSVW71' : 'Marsupials & monotremes',
       'PSVW73' : 'Marine & freshwater mammals',
       'PSVW79' : 'Primates',
       'PSX' : 'Human biology',
       'PSXE' : 'Early man',
       'PSXM' : 'Medical anthropology',
       'T' : 'Technology, engineering, agriculture',
       'TB' : 'Technology: general issues',
       'TBC' : 'Engineering: general',
       'TBD' : 'Technical design',
       'TBDG' : 'Ergonomics',
       'TBG' : 'Engineering graphics & technical drawing',
       'TBJ' : 'Maths for engineers',
       'TBM' : 'Instruments & instrumentation engineering',
       'TBMM' : 'Engineering measurement & calibration',
       'TBN' : 'Nanotechnology',
       'TBR' : 'Intermediate technology',
       'TBX' : 'History of engineering & technology',
       'TBY' : 'Inventions & inventors',
       'TC' : 'Biochemical engineering',
       'TCB' : 'Biotechnology',
       'TCBG' : 'Genetic engineering',
       'TCBS' : 'Biosensors',
       'TD' : 'Industrial chemistry & manufacturing technologies',
       'TDC' : 'Industrial chemistry',
       'TDCB' : 'Chemical engineering',
       'TDCC' : 'Heavy chemicals',
       'TDCD' : 'Detergents technology',
       'TDCG' : 'Powder technology',
       'TDCH' : 'Insecticide & herbicide technology',
       'TDCJ' : 'Pigments, dyestuffs & paint technology',
       'TDCJ1' : 'Cosmetics technology',
       'TDCK' : 'Surface-coating technology',
       'TDCP' : 'Plastics & polymers technology',
       'TDCQ' : 'Ceramics & glass technology',
       'TDCR' : 'Rubber technology',
       'TDCT' : 'Food & beverage technology',
       'TDCT1' : 'Brewing technology',
       'TDCT2' : 'Winemaking technology',
       'TDCW' : 'Pharmaceutical technology',
       'TDG' : 'Leather & fur technology',
       'TDH' : 'Textile & fibre technology',
       'TDJ' : 'Timber & wood processing',
       'TDJP' : 'Pulp & paper technology',
       'TDM' : 'Metals technology / metallurgy',
       'TDP' : 'Other manufacturing technologies',
       'TDPB' : 'Precision instruments manufacture',
       'TDPB1' : 'Clocks, chronometers & watches (horology)',
       'TDPD' : 'Household appliances manufacture',
       'TDPF' : 'Furniture & furnishings manufacture',
       'TDPH' : 'Clothing & footware manufacture',
       'TDPP' : 'Printing & reprographic technology',
       'TG' : 'Mechanical engineering & materials',
       'TGB' : 'Mechanical engineering',
       'TGBF' : 'Tribology (friction & lubrication)',
       'TGBN' : 'Engines & power transmission',
       'TGBN1' : 'Steam engines',
       'TGM' : 'Materials science',
       'TGMB' : 'Engineering thermodynamics',
       'TGMD' : 'Mechanics of solids',
       'TGMD4' : 'Dynamics & vibration',
       'TGMD5' : 'Stress & fracture',
       'TGMF' : 'Mechanics of fluids',
       'TGMF1' : 'Aerodynamics',
       'TGMF2' : 'Hydraulics & pneumatics',
       'TGMF3' : 'Flow, turbulence, rheology',
       'TGMT' : 'Testing of materials',
       'TGMT1' : 'Non-destructive testing',
       'TGP' : 'Production engineering',
       'TGPC' : 'Computer aided manufacture (CAM)',
       'TGPQ' : 'Industrial quality control',
       'TGPR' : 'Reliability engineering',
       'TGX' : 'Engineering skills & trades',
       'TGXT' : 'Tool making',
       'TGXW' : 'Welding',
       'TH' : 'Energy technology & engineering',
       'THF' : 'Fossil fuel technologies',
       'THFG' : 'Gas technology',
       'THFP' : 'Petroleum technology',
       'THFS' : 'Solid fuel technology',
       'THK' : 'Nuclear power & engineering',
       'THN' : 'Heat transfer processes',
       'THR' : 'Electrical engineering',
       'THRB' : 'Power generation & distribution',
       'THRD' : 'Power networks, systems, stations & plants',
       'THRF' : 'Power utilization & applications',
       'THRH' : 'Energy conversion & storage',
       'THRM' : 'Electric motors',
       'THRS' : 'Electrician skills',
       'THT' : 'Energy efficiency',
       'THX' : 'Alternative & renewable energy sources & technology',
       'TJ' : 'Electronics & communications engineering',
       'TJF' : 'Electronics engineering',
       'TJFC' : 'Circuits & components',
       'TJFD' : 'Electronic devices & materials',
       'TJFD1' : 'Microprocessors',
       'TJFD3' : 'Transistors',
       'TJFD5' : 'Semi-conductors & super-conductors',
       'TJFM' : 'Automatic control engineering',
       'TJFM1' : 'Robotics',
       'TJFN' : 'Microwave technology',
       'TJK' : 'Communications engineering / telecommunications',
       'TJKD' : 'Radar',
       'TJKR' : 'Radio technology',
       'TJKS' : 'Satellite communication',
       'TJKT' : 'Telephone technology',
       'TJKT1' : 'Mobile phone technology',
       'TJKV' : 'Television technology',
       'TJKW' : 'WAP (wireless) technology',
       'TN' : 'Civil engineering, surveying & building',
       'TNC' : 'Structural engineering',
       'TNCB' : 'Surveying',
       'TNCB1' : 'Quantity surveying',
       'TNCC' : 'Soil & rock mechanics',
       'TNCE' : 'Earthquake engineering',
       'TNCJ' : 'Bridges',
       'TNF' : 'Hydraulic engineering',
       'TNFD' : 'Dams & reservoirs',
       'TNFH' : 'Harbours & ports',
       'TNFL' : 'Flood control',
       'TNFR' : 'Land reclamation & drainage',
       'TNH' : 'Highway & traffic engineering',
       'TNK' : 'Building construction & materials',
       'TNKF' : 'Fire protection & safety',
       'TNKH' : 'Heating, lighting, ventilation',
       'TNKS' : 'Security & fire alarm systems',
       'TNKX' : 'Conservation of buildings & building materials',
       'TNT' : 'Building skills & trades',
       'TNTB' : 'Bricklaying & plastering',
       'TNTC' : 'Carpentry',
       'TNTP' : 'Plumbing',
       'TNTR' : 'Roofing',
       'TQ' : 'Environmental science, engineering & technology',
       'TQD' : 'Environmental monitoring',
       'TQK' : 'Pollution control',
       'TQS' : 'Sanitary & municipal engineering',
       'TQSR' : 'Waste treatment & disposal',
       'TQSR1' : 'Sewage treatment & disposal',
       'TQSR3' : 'Hazardous waste treatment & disposal',
       'TQSW' : 'Water supply & treatment',
       'TQSW1' : 'Water purification & desalinization',
       'TR' : 'Transport technology & trades',
       'TRC' : 'Automotive technology & trades',
       'TRCS' : 'Automotive (motor mechanic) skills',
       'TRCT' : 'Road transport & haulage trades',
       'TRF' : 'Railway technology, engineering & trades',
       'TRFT' : 'Railway trades',
       'TRL' : 'Shipbuilding technology, engineering & trades',
       'TRLD' : 'Ship design & naval architecture',
       'TRLN' : 'Navigation & seamanship',
       'TRLT' : 'Maritime / nautical trades',
       'TRP' : 'Aerospace & aviation technology',
       'TRPS' : 'Aviation skills / piloting',
       'TRT' : 'Intelligent & automated transport system technology',
       'TT' : 'Other technologies & applied sciences',
       'TTA' : 'Acoustic & sound engineering',
       'TTB' : 'Applied optics',
       'TTBF' : 'Fibre optics',
       'TTBL' : 'Laser technology & holography',
       'TTBM' : 'Imaging systems & technology',
       'TTBS' : 'Scanning systems & technology',
       'TTD' : 'Space science',
       'TTDS' : 'Astronautics',
       'TTM' : 'Military engineering',
       'TTMW' : 'Ordnance, weapons technology',
       'TTP' : 'Explosives technology & pyrotechnics',
       'TTS' : 'Marine engineering',
       'TTSH' : 'Offshore engineering',
       'TTSX' : 'Sonar',
       'TTU' : 'Mining technology & engineering',
       'TTV' : 'Other vocational technologies & trades',
       'TTVC' : 'Hotel & catering trades',
       'TTVH' : 'Hairdressing & salon skills',
       'TTVR' : 'Traditional trades & skills',
       'TTX' : 'Taxidermy',
       'TV' : 'Agriculture & farming',
       'TVB' : 'Agricultural science',
       'TVD' : 'Agricultural engineering & machinery',
       'TVDR' : 'Irrigation',
       'TVF' : 'Sustainable agriculture',
       'TVG' : 'Organic farming',
       'TVH' : 'Animal husbandry',
       'TVHB' : 'Animal breeding',
       'TVHF' : 'Dairy farming',
       'TVHH' : 'Apiculture (beekeeping)',
       'TVHP' : 'Poultry farming',
       'TVK' : 'Agronomy & crop production',
       'TVKC' : 'Cereal crops',
       'TVKF' : 'Fertilizers & manures',
       'TVM' : 'Smallholdings',
       'TVP' : 'Pest control',
       'TVQ' : 'Tropical agriculture: practice & techniques',
       'TVR' : 'Forestry & silviculture: practice & techniques',
       'TVS' : 'Horticulture',
       'TVSW' : 'Viticulture',
       'TVT' : 'Aquaculture & fish-farming: practice & techniques',
       'U' : 'Computing & information technology',
       'UB' : 'Information technology: general issues',
       'UBH' : 'Health & safety aspects of IT',
       'UBJ' : 'Ethical & social aspects of IT',
       'UBL' : 'Legal aspects of IT',
       'UBW' : 'Internet: general works ',
       'UD' : 'Digital lifestyle',
       'UDA' : 'Personal organisation software & apps',
       'UDB' : 'Internet guides & online services',
       'UDBA' : 'Online shopping & auctions',
       'UDBD' : 'Internet searching',
       'UDBG' : 'Internet gambling',
       'UDBM' : 'Online finance & investing',
       'UDBR' : 'Internet browsers',
       'UDBS' : 'Social networking',
       'UDBV' : 'Virtual worlds ',
       'UDF' : 'Email: consumer/user guides',
       'UDH' : 'Portable & handheld devices: consumer/user guides',
       'UDM' : 'Digital music: consumer/user guides',
       'UDP' : 'Digital photography: consumer/user guides',
       'UDQ' : 'Digital video: consumer/user guides',
       'UDT' : 'Mobile phones: consumer/user guides',
       'UDV' : 'Digital TV & media centres: consumer/user guides',
       'UDX' : 'Computer games / online games: strategy guides',
       'UF' : 'Business applications',
       'UFB' : 'Integrated software packages',
       'UFBC' : 'Microsoft Office',
       'UFBF' : 'Microsoft Works',
       'UFBL' : 'Lotus Smartsuite',
       'UFBP' : 'OpenOffice',
       'UFBS' : 'StarOffice',
       'UFBW' : 'iWork',
       'UFC' : 'Spreadsheet software',
       'UFCE' : 'Excel',
       'UFCL' : 'Lotus 1-2-3',
       'UFD' : 'Word processing software',
       'UFDM' : 'Microsoft Word',
       'UFG' : 'Presentation graphics software',
       'UFGP' : 'PowerPoint',
       'UFK' : 'Accounting software',
       'UFL' : 'Enterprise software',
       'UFLS' : 'SAP (Systems, applications & products in databases)',
       'UFM' : 'Mathematical & statistical software',
       'UFP' : 'Project management software',
       'UFS' : 'Collaboration & group software',
       'UG' : 'Graphical & digital media applications',
       'UGB' : 'Web graphics & design',
       'UGC' : 'Computer-aided design (CAD)',
       'UGD' : 'Desktop publishing',
       'UGG ' : 'Computer games design',
       'UGK' : '3D graphics & modelling',
       'UGL' : 'Illustration & drawing software',
       'UGM' : 'Digital music: professional',
       'UGN' : 'Digital animation',
       'UGP' : 'Photo & image editing',
       'UGV' : 'Digital video: professional',
       'UK' : 'Computer hardware',
       'UKC' : 'Supercomputers',
       'UKD' : 'Mainframes & minicomputers',
       'UKF' : 'Servers',
       'UKG' : 'Grid & parallel computing',
       'UKM' : 'Embedded systems',
       'UKN' : 'Network hardware',
       'UKP' : 'Personal computers',
       'UKPC' : 'PCs (IBM-compatible personal computers)',
       'UKPM' : 'Macintosh',
       'UKR' : 'Maintenance & repairs',
       'UKS' : 'Storage media & peripherals',
       'UKX' : 'Utilities & tools',
       'UL' : 'Operating systems',
       'ULD' : 'Windows & variants',
       'ULDF' : 'Windows 7',
       'ULDG' : 'Windows Vista',
       'ULDL' : 'Windows 2003',
       'ULDP' : 'Windows XP',
       'ULDT' : 'Windows 2000',
       'ULDX' : 'Windows NT',
       'ULH' : 'Macintosh OS',
       'ULL' : 'Linux',
       'ULLD' : 'Debian',
       'ULLR' : 'Red Hat',
       'ULLS' : 'SUSE',
       'ULLU' : 'UBUNTU',
       'ULN' : 'UNIX',
       'ULNB' : 'BSD / FreeBSD',
       'ULNH' : 'HP-UX',
       'ULNM' : 'IBM AIX',
       'ULNS' : 'Sun Solaris',
       'ULP' : 'Handheld operating systems',
       'ULQ' : 'IBM mainframe operating systems',
       'ULR' : 'Real time operating systems',
       'UM' : 'Computer programming / software development',
       'UMA' : 'Program concepts / learning to program',
       'UMB' : 'Algorithms & data structures',
       'UMC' : 'Compilers',
       'UMF' : 'Agile programming',
       'UMG' : 'Aspect programming / AOP',
       'UMH' : 'Extreme programming',
       'UMJ' : 'Functional programming',
       'UMK' : 'Games development & programming',
       'UMKB' : '2D graphics: games programming',
       'UMKC' : '3D graphics: games programming',
       'UMKL' : 'Level design: games programming',
       'UML' : 'Graphics programming',
       'UMN' : 'Object-oriented programming (OOP)',
       'UMP' : 'Microsoft programming',
       'UMPN' : '.Net programming',
       'UMPW' : 'Windows programming',
       'UMQ' : 'Macintosh programming',
       'UMR' : 'Network programming',
       'UMS' : 'Mobile & handheld device programming / Apps programming',
       'UMT' : 'Database programming',
       'UMW' : 'Web programming',
       'UMWS' : 'Web services',
       'UMX' : 'Programming & scripting languages: general',
       'UMZ' : 'Software Engineering',
       'UMZL' : 'Unified Modeling Language (UML)',
       'UMZT' : 'Software testing & verification',
       'UMZW' : 'Object oriented software engineering',
       'UN' : 'Databases',
       'UNA' : 'Database design & theory',
       'UNAR' : 'Relational databases',
       'UNC' : 'Data capture & analysis',
       'UND' : 'Data warehousing',
       'UNF' : 'Data mining',
       'UNH' : 'Information retrieval',
       'UNJ' : 'Object-oriented databases',
       'UNK' : 'Distributed databases',
       'UNN' : 'Databases & the Web',
       'UNS' : 'Database software',
       'UNSB' : 'Oracle',
       'UNSC' : 'Access',
       'UNSF' : 'FileMaker',
       'UNSJ' : 'SQL Server / MS SQL',
       'UNSK' : 'SQLite',
       'UNSM' : 'MySQL',
       'UNSP' : 'PostgreSQL',
       'UNSX' : 'IBM DB2',
       'UNSY' : 'Sybase',
       'UQ' : 'Computer certification',
       'UQF' : 'Computer certification: Microsoft',
       'UQJ' : 'Computer certification: Cisco',
       'UQL' : 'Computer certification: ECDL',
       'UQR' : 'Computer certification: CompTia',
       'UQT' : 'Computer certification: CLAiT',
       'UR' : 'Computer security',
       'URD' : 'Privacy & data protection',
       'URH' : 'Computer fraud & hacking',
       'URJ' : 'Computer viruses, Trojans & worms',
       'URQ' : 'Firewalls',
       'URS' : 'Spam',
       'URW' : 'Spyware',
       'URY' : 'Data encryption',
       'UT' : 'Computer networking & communications',
       'UTC' : 'Cloud computing',
       'UTD' : 'Client-Server networking',
       'UTF' : 'Network management',
       'UTFB' : 'Computer systems back-up & data recovery',
       'UTG' : 'Grid computing',
       'UTM' : 'Electronic mail (email): professional',
       'UTN' : 'Network security',
       'UTP' : 'Networking standards & protocols',
       'UTR' : 'Distributed systems',
       'UTS' : 'Networking packages',
       'UTV' : 'Virtualisation',
       'UTW' : 'WAP networking & applications',
       'UTX' : 'EDI (electronic data interchange)',
       'UY' : 'Computer science',
       'UYA' : 'Mathematical theory of computation',
       'UYAM' : 'Maths for computer scientists',
       'UYD' : 'Systems analysis & design',
       'UYF' : 'Computer architecture & logic design',
       'UYFL' : 'Assembly languages',
       'UYFP' : 'Parallel processing',
       'UYM' : 'Computer modelling & simulation',
       'UYQ' : 'Artificial intelligence',
       'UYQE' : 'Expert systems / knowledge-based systems',
       'UYQL' : 'Natural language & machine translation',
       'UYQM' : 'Machine learning',
       'UYQN' : 'Neural networks & fuzzy systems',
       'UYQP' : 'Pattern recognition',
       'UYQS' : 'Speech recognition',
       'UYQV' : 'Computer vision',
       'UYS' : 'Signal processing',
       'UYT' : 'Image processing',
       'UYU' : 'Audio processing',
       'UYV' : 'Virtual reality',
       'UYZ' : 'Human-computer interaction',
       'UYZF' : 'Information visualization',
       'UYZG' : 'User interface design & usability',
       'UYZM' : 'Information architecture'}

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d-%02d-%02d' % (now.year, now.month, now.day, now.hour, now.minute)

#get data from IOP stacks
os.system('wget --no-check-certificate -O %s/%s.tar.gz https://J9774:gIe^F83S@stacks.iop.org/Member/lload.tar.gz' % (iopdirraw, stampoftoday))




#check for new ftp-feeds
todo = []
bookfeeds = []
done = os.listdir(iopdirdone)
for datei in os.listdir(iopdirraw):
    if datei in done:
        print '%s already in done' % (datei)
        os.system('rm %s/%s' % (iopdirraw, datei))
    elif re.search('tar.gz$', datei):
        todo.append(datei)

for datei in os.listdir(ftpdir):
    if datei in done:
        print '%s already in done' % (datei)
    elif re.search('xml$', datei):
        bookfeeds.append(datei)
    


print '%i packages to do: %s' % (len(todo), ', '.join(todo))
if not todo and not bookfeeds:
    sys.exit(0)
if not os.path.isdir(iopdirtmp):
    os.system('mkdir %s' % (iopdirtmp))


#extract the feeds:
for datei in todo:
    print 'extracting %s' % (os.path.join(iopdirraw, datei))
    journalfeed = tarfile.open(os.path.join(iopdirraw, datei), 'r:gz')
    journalfeed.extractall(path=iopdirtmp)
    journalfeed.close()

#create base name
iopftrunc = stampoftoday


collapseWs = re.compile('[\n \t]+')
#initialBlank = re.compile('([A-Z]) ')
initialEnd = re.compile(r'([A-Z])\b')
#convert xml-tags to LaTex-style        
def fsunwrap(tag):
    try: 
        for sup in tag.find_all('SUP'):
            cont = sup.string
            sup.replace_with('^'+cont)
    except:
        print 'fsunwrap-sup-problem'
    try: 
        for sub in tag.find_all('SUB'):
            cont = sub.string
            sub.replace_with('_'+cont)
    except:
        print 'fsunwrap-sub-problem'
    return tag

#convert individual article        
def convertarticle(issn, vol, isu, artid):
    if issn in jnl.keys():
        rec = {'jnl' : jnl[issn], 'note' : [], 'keyw' : [], 'aff' : [], 'refs' : []}
        if  jnl[issn] == 'Astrophys.J.Lett.':
            rec['alternatejnl'] = 'Astrophys.J.'
        if issn in ['1742-6596']:
            tc = ['C']
        elif issn in ['0034-4885']:
            tc = ['PR']
        else:
            tc = ['P']
    elif issn in jnlskip.keys():
        print 'skip journal "%s"' % (jnlskip[issn])
        return []
    else:
        print 'do not know journal with ISSN:%s' % (issn)
        sys.exit(0)
        rec = {'jnl' : issn, 'note' : [], 'keyw' : [], 'aff' : [], 'refs' : []}
    ###read metadata
    if os.path.isfile(os.path.join(iopdirtmp, issn, vol, isu, artid, '.article')):
        inf = open(os.path.join(iopdirtmp, issn, vol, isu, artid, '.article'))
        article = BeautifulSoup(''.join(inf.readlines()))
        inf.close()
        #article type
        for attrnode in article.find_all('attributes'):        
            if attrnode.has_attr('art_type'):
                if attrnode['art_type'] == 'rev':
                    tc = ['R']
                elif attrnode['art_type'] == 'misc': 
                    tc = ['']
        #conference
        for focusnode in article.find_all('art_focus'):
            if focusnode.has_attr('alt'):
                if focusnode['alt'] == 'Proceeding Article':
                    tc = ['C']
                rec['note'].append(focusnode['alt'])
                if focusnode['alt'] in cnumdict.keys():
                    rec['cnum'] = cnumdict[focusnode['alt']]
                    tc = ['C']
            elif focusnode.has_attr('group'):
                comm = focusnode['group']
                rec['note'].append(comm)
                if comm in cnumdict.keys():
                    rec['cnum'] = cnumdict[comm]
        #volume
        for volumenode in article.find_all('volume'):
            rec['vol'] = volumenode.text.strip()
            if issn in ['1674-1056', '0953-4075']:
                rec['vol'] = 'B'+rec['vol']
            elif issn == '1674-1137':
                rec['vol'] = 'C'+rec['vol']
            elif issn == '1751-8121':
                rec['vol'] = 'A'+rec['vol']
            elif issn == '0954-3899':
                rec['vol'] = 'G'+rec['vol']
        #issue
        for issuenode in article.find_all('issue'):
            issue = issuenode.text.strip()
            if issn == '1402-4896' and issue[0] == 'T':
                rec['vol'] = issue
            else:
                rec['issue'] = issue
                if issue.startswith("S"): #we have a supplememnt 
                    rec['jnl'] += " Suppl."                     
        #year
        for datenode in article.find_all('date_cover'):
            datecover = datenode.text.strip()
            rec['year'] = datecover[0:4]
            if rec['jnl'] in ['JCAP', 'JHEP', 'JSTAT']:
                rec['vol'] = datecover[2:4] + datecover[5:7]
                if 'issue' in rec.keys():
                    del rec['issue']
        #article number
        for artnumnode in article.find_all('artnum'):
            rec['artnum'] = artnumnode.text.strip()
        #DOI
        for doinode in article.find_all('doi'):
            rec['doi'] = doinode.text.strip()
        #pages
        for pagenode in article.find_all('pages'):
            if pagenode.has_attr('extent'):
                rec['pages'] = pagenode['extent']
            if pagenode.has_attr('start'):
                rec['p1'] = pagenode['start']
            if pagenode.has_attr('end'):
                rec['p2'] = pagenode['end']
        #arXiv number
        for idnode in article.find_all('external_id'):
            if idnode.has_attr('type') and idnode['type'] == 'arxive':
                rec['arxiv'] = re.sub('v.*', '', idnode.text.strip())
        #date
        for datenode in article.find_all('date_online'):
            if datenode.has_attr('fulltext'):
                rec['date'] = datenode['fulltext']
            elif datenode.has_attr('header'):
                rec['date'] = datenode['header']
            else:
                print 'no date for %s' % (rec['doi'])
        #title
        for titnode in article.find_all('title_full'):
            for footnode in titnode.find_all('footnote'):
                rec['note'].append(footnode.text.strip())
                footnode.replace_with('')
            fsunwrap(titnode)
            rec['tit'] = titnode.text.strip()
            rec['tit']  = collapseWs.sub(' ', rec['tit'])
        #keywords
        for kwnode in article.find_all('kwd_main'):
            rec['keyw'].append(kwnode.text.strip())
        #authors
        authors = []
        afid = ''
        for aunode in article.find_all('author_granular'):
            #name
            (fname, nlfname, nllname, lname) = ('', '', '', '')
            for group in aunode.find_all('group'):
                rec['col'] = group.text
            for fnamenode in aunode.find_all('given'):
                fname = re.sub('\.\.', '.', initialEnd.sub(r'\1.', fnamenode.text))
                if fnamenode.has_attr('non_latin'):
                    nlfname = fnamenode['non_latin']
            for lnamenode in aunode.find_all('surname'):
                lname = lnamenode.text
                if lnamenode.has_attr('non_latin'):
                    nllname = lnamenode['non_latin']
            #affiliation
            afido = afid
            afi = ''
            if aunode.has_attr('affil'):
                afid = aunode['affil'].replace(',','; =')
            if (afid != afido) and afido:
                authors.append('=' + afido)         
            #ORCID and combine
            if aunode.has_attr('orcid'):
                orcid = 'ORCID:' + aunode['orcid']
                finalauthor = lname + ', ' + fname +  ', ' + orcid
            else:
                finalauthor = lname + ', ' + fname
            if nllname + nlfname != '':
                finalauthor += ', CHINESENAME: ' + nllname + ' ' +  nlfname
            if re.search('[a-zA-Z]', finalauthor):
                authors.append(finalauthor)
        if afid:
            authors.append('=' + afid)
        rec['auts'] = authors
        (afid, afido) = ('', '')
        if not authors:
            for aunode in article.find_all('author'):
                aut = aunode.text.strip()
                if 'Collaboration' in aut:
                    rec['col'] = aut
                    continue
                authors.append(aut)
                if aunode.has_attr('affil'):
                    afid = aunode['affil'].replace(',','; =')
                    authors.append('=' + afid)
            rec['auts'] = authors
        #affiliations
        (affid, orgname) = ('', '')
        for afnode in article.find_all('affil'):
            if afnode.has_attr('id'):
                affid = afnode['id']
            rec['aff'].append('%s= %s' % (affid, collapseWs.sub(' ', afnode.text.strip())))
        #Open Access
        for oanode in article.find_all('open_access'):
            rec['licence'] = {'url' : oanode['url']}
            rec['FFT'] = 'http://iopscience.iop.org/article/%s/pdf' % (rec['doi'])
        #typecode
        rec['tc'] = tc
        try:
            if issn == '1748-0221' and rec['p1'][0] == 'C':
                rec['tc'] = ['C']
        except:
            pass
        #abstract
        for absnode in article.find_all('header_text', attrs = {'heading' : 'Abstract'}):
            fsunwrap(absnode)
            rec['abs'] = collapseWs.sub(' ', absnode.text.strip())    
        ###read references
        if os.path.isfile(os.path.join(iopdirtmp, issn, vol, isu, artid, '.refs')):
            inf = open(os.path.join(iopdirtmp, issn, vol, isu, artid, '.refs'))
            references = BeautifulSoup(''.join(inf.readlines()))
            inf.close()
            for reference in references.find_all('reference'):
                for x in reference.find_all('ref_citation'):
                    ref = [('x', x.text.strip())]
                #detailed only if there is a DOI to 'ensure' that it is matched
                for refdoi in reference.find_all('ref_doi'):
                    ref.append(('a', 'doi:' + refdoi.text.strip()))
                    for ref_year in reference.find_all('refyear'):
                        ref.append(('y', refyear.text.strip()))
                    for ref_authors in reference.find_all('refauthors'):
                        ref.append(('h', refauthors.text.strip()))
                    #for refjournal in reference.find_all('ref_journal'):
                    #   pbn = refjournal.text.strip()
                    #   for refvolume in reference.find_all('ref_volume'):
                    #       pbn += ',' + refvolume.text.strip()
                    #   for refstartpage in reference.find_all('ref_start_page'):
                    #       pbn += ',' + refstartpage.text.strip()
                    #   ref.append(('s', pbn))
                rec['refs'].append(ref)
        else:
            print '   no references for ', rec['doi']
        ###check for fulltext
        for datei in os.listdir(os.path.join(iopdirtmp, issn, vol, isu, artid)):
            if re.search('\.pdf$', datei):
                pdfsrc = os.path.join(iopdirtmp, issn, vol, isu, artid, datei)
                pdfdst = os.path.join(pdfdir, re.sub('[\/\(\)]', '_', rec['doi']) + '.pdf')
                if os.path.isfile(pdfdst):
                    print '   fulltext found but no need to copy'
                else:
                   try:
                        shutil.copy(pdfsrc, pdfdst)
                        print '   fulltext found and copied'
                   except:
                       print '   fulltext found but not copied!'
                       print pdfsrc
                       print pdfdst
        ###
        print '.', rec['doi'], rec.keys()        
        return rec
    else:
        return {}













        
#scan extracted directories
for issn in os.listdir(iopdirtmp):
    if re.search('\d\d\d\d\-\d\d\d[\dX]', issn):
        for vol in os.listdir(os.path.join(iopdirtmp, issn)):
            if re.search('\d', vol):
                recs = []
                issues = []
                for isu in os.listdir(os.path.join(iopdirtmp, issn, vol)):
                    if re.search('\d', isu):
                        print '------{ ISSN:%s VOL:%s ISU:%s}------' % (issn, vol, isu)
                        issues.append(isu)
                        for artid in os.listdir(os.path.join(iopdirtmp, issn, vol, isu)):
                            if re.search('\d', artid):
                                rec = convertarticle(issn, vol, isu, artid)
                                if rec: recs.append(rec)
                if recs:
                    if issn in jnl.keys():
                        if 'vol' in recs[0].keys():
                            iopf = 'iop-%s-%s%s_%s' % (iopftrunc, re.sub(' ', '', jnl[issn]), recs[0]['vol'], '.'.join(issues))
                        else:
                            iopf = 'iop-%s-%s%s_%s' % (iopftrunc, re.sub(' ', '', jnl[issn]), vol, '.'.join(issues))                 
                    else:
                        iopf = 'iop-%s-%s%s_%s' % (iopftrunc, re.sub(' ', '', issn), vol, '.'.join(issues))
                    if not issn in jnlskip.keys():
                        xmlf = os.path.join(xmldir,iopf+'.xml')
                        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
                        ejlmod2.writeXML(recs ,xmlfile,'IOP')
                        xmlfile.close()
                  
                        #retrival
                        retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
                        retfiles_text = open(retfiles_path,"r").read()
                        line = iopf+'.xml'+ "\n"
                        if not line in retfiles_text: 
                            retfiles = open(retfiles_path,"a")
                            retfiles.write(line)
                            retfiles.close()
                print '   %s with %i records\n' % (iopf, len(recs))

#scan books
for bookfeed in bookfeeds:    
    os.system('cp %s/%s %s/%s' % (ftpdir, bookfeed, iopdirraw, bookfeed))
    products = []
    prerecs = {}
    print bookfeed
    iopf = re.sub('.*_(.*).xml', r'iopbooks_\1', bookfeed)
    inf = open('%s/%s' % (iopdirraw, bookfeed), 'r')
    product = False
    for line in inf.readlines():
        if '<Product>' in line:
            product = line
        elif product:
            product += line
        if '</Product>' in line:
            products.append(product)
            product = False
    inf.close()
    print '%i products found' % (len(products))
    i = 0
    for product in products:
        bproduct = BeautifulSoup(product)
        i += 1
        print '---{ %i/%i }---' % (i, len(products))
        rec = {'autaff' : [], 'keyw' : [], 'note' : [], 'jnl' : 'BOOK', 'tc' : 'B'}
        #get rid of Related Material
        for rema in bproduct.find_all('relatedmaterial'):
            rema.replace_with('')
        #DOI
        for wi in bproduct.find_all('workidentifier'):
            for wit in wi.find_all('workidtype'):
                if wit.text == '06':
                    for idv in wi.find_all('idvalue'):
                        rec['doi'] = idv.text
                        print ' ', rec['doi']
        #productform
        for pf in bproduct.find_all('productform'):
            if pf.text[0] == 'B':
                rec['productform'] = 'print'
            elif pf.text[0] in ['D', 'E']:
                rec['productform'] = 'online'
        #isbn
        isbnadded = False
        for pi in bproduct.find_all('productidentifier'):
            if not 'isbns' in rec.keys():
                for pit in pi.find_all('productidtype'):
                    if pit.text == '15':
                        for idv in pi.find_all('idvalue'):
                            isbn = idv.text
                            print ' ', isbn
                            if not 'doi' in rec.keys():
                                rec['doi'] = '20.2000/' + isbn
                            if 'productform' in rec.keys():
                                rec['isbns'] = [[('a', isbn), ('b', rec['productform'])]]
                            else:
                                rec['isbns'] = [[('a', isbn)]]
                            if rec['doi'] in prerecs.keys():
                                prerecs[rec['doi']]['isbns'].append(rec['isbns'][0])
                                isbnadded = True
    
        if isbnadded:
            print 'added ISBN to existing record of %s' % (rec['doi'])
            continue
        #series
        for tos in bproduct.find_all('titleofseries'):
            rec['series'] = tos.text
        #title
        for tit in bproduct.find_all('title'):
            for titt in tit.find_all('titletext'):
                rec['tit'] = titt.text
        if not 'tit' in rec.keys():
            for td in bproduct.find_all('titledetail'):
                for tel in td.find_all('titleelementlevel'):
                    if tel.text == '01':
                        for twp in td.find_all('titlewithoutprefix'):
                            rec['tit'] = twp.text
        #authors
        for contributor in bproduct.find_all('contributor'):
            for cr in contributor.find_all('contributorrole'):
                role = cr.text
            for pni in contributor.find_all('personnameinverted'):
                if role[0] == 'A':
                    rec['autaff'].append([ pni.text ])
                elif role[0] == 'B':
                    rec['autaff'].append([ pni.text + ' (Ed.)'])
            for pa in contributor.find_all('professionalaffiliation'):
                for paa in pa.find_all('affiliation'):
                    rec['autaff'][-1].append(paa.text)
        #pages
        for nop in bproduct.find_all('numberofpages'):
            rec['pages'] = nop.text
        #abstract
        for ot in bproduct.find_all(['othertext', 'textcontent']):        
            if not 'abs' in rec.keys():
                for ttc in ot.find_all(['texttype', 'texttypecode']):
                    if ttc.text in ['02', '03']:
                        for ott in ot.find_all('text'):
                            rec['abs'] = ott.text
        #date
        for pd in bproduct.find_all('publicationdate'):
            rec['date'] = re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3', pd.text)
        if not 'date' in rec.keys():
            for pd in bproduct.find_all('publishingdate'):
                for pdd in pd.find_all('date'):
                    rec['date'] = re.sub('(\d\d\d\d)(\d\d)(\d\d)', r'\1-\2-\3', pdd.text)
        #keywords
        for subject in bproduct.find_all('subject'):
            for ssi in subject.find_all('subjectschemeidentifier'):
                if ssi.text in ['23', '93']:
                    for sht in subject.find_all('subjectheadingtext'):
                        rec['keyw'].append(sht.text)
                elif ssi.text == '10':
                    for sc in subject.find_all('subjectcode'):
                        if sc.text in bisac.keys():
                            rec['keyw'].append(bisac[sc.text])
                            rec['note'].append('BISAC: ' + bisac[sc.text])
                elif ssi.text == '12':
                    for sc in subject.find_all('subjectcode'):
                        if sc.text in bic.keys():
                            rec['keyw'].append(bic[sc.text])
                            rec['note'].append('BIC: ' + bic[sc.text])
        #combine different ISBNs into one
        quasiuniquekey = re.sub('\W', '', rec['autaff'][0][0]+rec['tit'])
        if not quasiuniquekey in prerecs.keys():
            print ' - new book with key:', quasiuniquekey
            prerecs[quasiuniquekey] = rec
        else:
            print ' - addition to book with key:', quasiuniquekey
            for isbn in rec['isbns']:                
                if not isbn in prerecs[quasiuniquekey]['isbns']:
                    print '   - add isbn:', isbn
                    prerecs[quasiuniquekey]['isbns'].append(isbn)
                else:
                    print '   - do not add isbn:', isbn
            if rec['doi'][:2] == '10':
                prerecs[quasiuniquekey]['doi'] = rec['doi']
    recs = prerecs.values()
    #retrival
    if recs:
        xmlf = os.path.join(xmldir,iopf+'.xml')
        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
        ejlmod2.writeXML(recs ,xmlfile,'IOP')
        xmlfile.close()
        retfiles_text = open(retfiles_path,"r").read()
        line = iopf+'.xml'+ "\n"
        if not line in retfiles_text: 
            retfiles = open(retfiles_path,"a")
            retfiles.write(line)
            retfiles.close()
    
#if everything went fine, move the files to done
for datei in todo:
    os.system('mv %s/%s %s/%s' % (iopdirraw, datei, iopdirdone, datei))
for bookfeed in bookfeeds:
    os.system('mv %s/%s %s/%s' % (iopdirraw, bookfeed, iopdirdone, bookfeed))

shutil.rmtree(iopdirtmp)
print 'done :-)'
    
