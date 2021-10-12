#!/usr/bin/env python

'''
Generate BAL catalogs from DESI healpix data for a specific data release. One 
catalog is generated per healpix. The catalogs are put in a directory 
structure that matches the structure of the data release. 
Use the separate script buildbalcat.py to create a BAL catalog for a 
corresponding QSO catalog. 
'''

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
from glob import glob

import argparse

import fitsio
from collections import defaultdict
import desispec.io
from desispec.coaddition import coadd_cameras

import baltools
from baltools import balconfig as bc
from baltools import plotter, fitbal, baltable
from baltools import desibal as db

debug = True

def pmmkdir(direct): 
    if not os.path.isdir(direct):
        try:
            os.makedirs(direct)
        except PermissionError:
            print("Error: no permission to make directory ", direct)
            exit(1)

os.environ['DESI_SPECTRO_REDUX'] = '/global/cfs/cdirs/desi/spectro/redux'

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="""Run balfinder on DESI data""")

parser.add_argument('-hp','--healpix', nargs='*', default = None, required=False,
                    help='List of healpix number(s) to process - default is all')

parser.add_argument('-r', '--release', type = str, default = 'everest', required = False,
                    help = 'Data release subdirectory, default is everest')

parser.add_argument('-s', '--survey', type = str, default = 'main', required = False,
                    help = 'Survey subdirectory [sv1, sv2, sv3, main], default is main')

parser.add_argument('-m', '--moon', type = str, default = 'dark', required = False,
                    help = 'Moon brightness [bright, dark], default is dark')

parser.add_argument('-o','--outdir', type = str, default = None, required = True,
                    help = 'Root directory for output files')

parser.add_argument('-c','--clobber', type = bool, default=False, required=False,
                    help = 'Clobber (overwrite) BAL catalog if it already exists?')

parser.add_argument('-v','--verbose', type = bool, default = False, required = False,
                    help = 'Provide verbose output?')

args  = parser.parse_args()

if debug: 
    args.verbose=True
    

# Root directory for input data: 
# Example: /global/cfs/cdirs/desi/spectro/redux/everest/healpix/main/dark/100
dataroot = os.path.join(os.getenv("DESI_SPECTRO_REDUX"), args.release, "healpix", args.survey, args.moon) 
#if release == 'daily':
#    dataroot = os.path.join(dataroot, 'cumulative')
#if not os.path.isdir(dataroot): 
#    print("Error: did not find root directory ", dataroot)
#    exit(1)
    
# Root directory for output catalogs: 
outroot = os.path.join(args.outdir, args.release, "healpix", args.survey, args.moon)
pmmkdir(outroot)


# Determine which tile(s) to process

healpixdirs = glob(dataroot + "/*/*")

healpixels = []  # list of all available healpix
for healpixdir in healpixdirs:
    healpixels.append(healpixdir[healpixdir.rfind('/')+1::])

inputhealpixels = args.healpix

if inputhealpixels is not None:
    for inputhealpixel in inputhealpixels: 
        assert(inputhealpixel in healpixels), "Healpix {} not available".format(inputhealpixels)
else:
    inputhealpixels = healpixels

# Create/confirm output tile directories exist
for inputhealpix in inputhealpixels: 
    healpixdir = os.path.join(outroot, inputhealpix[:3], inputhealpix) 
    pmmkdir(healpixdir) 

# For each tile in inputtiles, get the list of dates, create output 
# directories, identify BALs, and create catalogs 

# List of healpix that caused issues for by hand rerun.
issuehealpixels = []
errortypes = []

for healpix in inputhealpixels: 
    coaddfilename = "coadd-{0}-{1}-{2}.fits".format(args.survey, args.moon, healpix) 
    balfilename = coaddfilename.replace('coadd-', 'baltable-')

    indir = os.path.join(dataroot, inputhealpix[:3], inputhealpix)
    outdir = os.path.join(outroot, inputhealpix[:3], inputhealpix)

    coaddfile = os.path.join(indir, coaddfilename) 
    balfile = os.path.join(outdir, balfilename) 

    if args.verbose:
        print("Coadd file: ", coaddfile)
        print("BAL file: ", balfile)

    if not os.path.isfile(balfile) or args.clobber:
        try:
            db.desibalfinder(coaddfile, altbaldir=outdir, overwrite=args.clobber, verbose=args.verbose, release=args.release)
        except:
            print("An error occured at healpix {}. Adding healpix to issuehealpixels list.".format(healpix))
            errortype = sys.exc_info()[0]
            issuehealpixels.append(healpix)
            errortypes.append(errortype)

print("Healpix with errors and error types: ")
for i in range(len(issuehealpixels)):
    print("{} : {}".format(issuehealpixels[i], errortypes[i]))