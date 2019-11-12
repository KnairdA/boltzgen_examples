#!/usr/bin/env python

import argparse

from boltzgen import Generator, Geometry
from boltzgen.lbm.model import BGK

import config

argparser = argparse.ArgumentParser(
    description = 'Generate a CUDA implementation of a lid driven cavity simulation using LBM')
argparser.add_argument(
    '--output', required = False, help = 'Target directory for the generated sources')

args = argparser.parse_args()

generator = Generator(
    model     = BGK(config.descriptor, tau = config.tau),
    target    = 'cuda',
    precision = config.precision,
    streaming = config.streaming,
    index     = config.index,
    layout    = 'SOA')

if args.output is None:
    args.output = '.'

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']

if config.streaming == 'SSS':
    functions += ['update_sss_control_structure']

extras = ['cell_list_dispatch']

with open('%s/kernel.h' % args.output, 'w') as kernel:
    kernel.write(generator.kernel(config.geometry, functions, extras))

ldc_src = ''
with open('ldc.cuda.%s.mako' % config.streaming, 'r') as template:
    ldc_src = template.read()

with open('%s/ldc.cu' % args.output, 'w') as app:
    app.write(generator.custom(config.geometry, ldc_src))
