#!/usr/bin/env python

import argparse

from boltzgen import LBM, Generator, Geometry
from boltzgen.lbm.model import D2Q9

import config

argparser = argparse.ArgumentParser(
    description = 'Generate a C++ implementation of a lid driven cavity simulation using LBM')
argparser.add_argument(
    '--output', required = False, help = 'Target directory for the generated sources')

args = argparser.parse_args()

lbm = LBM(config.descriptor)
generator = Generator(
    descriptor = config.descriptor,
    moments    = lbm.moments(),
    collision  = lbm.bgk(f_eq = lbm.equilibrium(), tau = config.tau),
    target     = 'cpp',
    precision  = config.precision,
    index      = 'XYZ',
    layout     = 'AOS')

if args.output is None:
    args.output = '.'

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']

with open('%s/kernel.h' % args.output, 'w') as kernel:
    kernel.write(generator.kernel(config.geometry, functions))

ldc_src = ''
with open('ldc.cpp.mako', 'r') as template:
    ldc_src = template.read()

with open('%s/ldc.cpp' % args.output, 'w') as app:
    app.write(generator.custom(config.geometry, ldc_src))
