#!/usr/bin/env python

from boltzgen import LBM, Generator, Geometry
from boltzgen.lbm.model import D2Q9

geometry = Geometry(256, 256)

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary', 'example']
extras    = ['omp_parallel_for', 'moments_vtk']

precision = 'double'

lbm = LBM(D2Q9)
generator = Generator(
    descriptor = D2Q9,
    moments    = lbm.moments(),
    collision  = lbm.bgk(f_eq = lbm.equilibrium(), tau = 0.52),
    target     = 'cpp',
    precision  = precision,
    index      = 'XYZ',
    layout     = 'AOS')

with open("kernel.h", "w") as kernel:
    kernel.write(generator.kernel(geometry, functions, extras))
