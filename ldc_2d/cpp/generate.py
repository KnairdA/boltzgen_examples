#!/usr/bin/env python

import argparse

from boltzgen import LBM, Generator, Geometry
from boltzgen.lbm.model import D2Q9

argparser = argparse.ArgumentParser(
    description = 'Generate a C++ implementation of a lid driven cavity simulation using LBM')
argparser.add_argument(
    '--output', required = False, help = 'Target directory for the generated sources')

args = argparser.parse_args()

geometry = Geometry(128, 128)

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']

lbm = LBM(D2Q9)
generator = Generator(
    descriptor = D2Q9,
    moments    = lbm.moments(),
    collision  = lbm.bgk(f_eq = lbm.equilibrium(), tau = 0.52),
    target     = 'cpp',
    precision  = 'double',
    index      = 'XYZ',
    layout     = 'AOS')

if args.output is None:
    args.output = '.'

with open('%s/kernel.h' % args.output, 'w') as kernel:
    kernel.write(generator.kernel(geometry, functions))

ldc_src = ''
with open('ldc.cpp.mako', 'r') as template:
    ldc_src = template.read()

with open('%s/ldc.cpp' % args.output, 'w') as app:
    app.write(generator.custom(geometry, ldc_src))
