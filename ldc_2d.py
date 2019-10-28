import numpy
import time
from string import Template

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt

from boltzgen import LBM, Generator, Geometry
from boltzgen.lbm.model import D2Q9

from simulation import Lattice, CellList

def MLUPS(cells, steps, time):
    return cells * steps / time * 1e-6

def generate_moment_plots(lattice, moments):
    for i, m in enumerate(moments):
        print("Generating plot %d of %d." % (i+1, len(moments)))

        velocity = numpy.ndarray(shape=tuple(reversed(lattice.geometry.inner_size())))
        for x, y in lattice.geometry.inner_cells():
            velocity[y-1,x-1] = numpy.sqrt(m[1,lattice.memory.gid(x,y)]**2 + m[2,lattice.memory.gid(x,y)]**2)

        plt.figure(figsize=(10, 10))
        plt.imshow(velocity, origin='lower', cmap=plt.get_cmap('seismic'))
        plt.savefig("result/ldc_2d_%02d.png" % i, bbox_inches='tight', pad_inches=0)

nUpdates = 100000
nStat    = 5000

geometry = Geometry(512, 512)

print("Generating kernel using boltzgen...\n")

lbm = LBM(D2Q9)
generator = Generator(
    descriptor = D2Q9,
    moments    = lbm.moments(),
    collision  = lbm.bgk(f_eq = lbm.equilibrium(), tau = 0.6))

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']
extras    = ['cell_list_dispatch']

kernel_src = generator.kernel('cl', 'single', 'SOA', geometry, functions, extras) + Template("""
__kernel void equilibrilize(__global $float_type* f_next,
                            __global $float_type* f_prev)
{
    const unsigned int gid = get_global_id(1)*$size_x + get_global_id(0);
    equilibrilize_gid(f_next, f_prev, gid);
}

__kernel void collect_moments(__global $float_type* f,
                              __global $float_type* moments)
{
    const unsigned int gid = get_global_id(1)*$size_x + get_global_id(0);
    collect_moments_gid(f, moments, gid);
}
""").substitute(float_type = 'float', size_x = geometry.size_x)

print("Initializing simulation...\n")

lattice = Lattice(geometry, kernel_src)
gid = lattice.memory.gid

bulk_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if x > 1 and x < geometry.size_x-2 and y > 1 and y < geometry.size_y-2 ])
wall_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if x == 1 or y == 1 or x == geometry.size_x-2 ])
lid_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if y == geometry.size_y-2 ])

lattice.schedule('collide_and_stream_cells', bulk_cells)
lattice.schedule('velocity_momenta_boundary_cells', wall_cells, numpy.array([0.0, 0.0], dtype=lattice.float_type[0]))
lattice.schedule('velocity_momenta_boundary_cells', lid_cells,  numpy.array([0.1, 0.0], dtype=lattice.float_type[0]))

print("Starting simulation using %d cells...\n" % lattice.geometry.volume)

moments = []

lastStat = time.time()

for i in range(1,nUpdates+1):
    lattice.evolve()

    if i % nStat == 0:
        lattice.sync()
        print("i = %4d; %3.0f MLUPS" % (i, MLUPS(lattice.geometry.volume, nStat, time.time() - lastStat)))
        moments.append(lattice.get_moments())
        lastStat = time.time()

print("\nConcluded simulation.\n")

generate_moment_plots(lattice, moments)
