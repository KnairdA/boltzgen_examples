import numpy
import time

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt

from boltzgen import Generator, Geometry
from boltzgen.lbm.lattice import D2Q9
from boltzgen.lbm.model   import BGK

from simulation import Lattice, CellList

def MLUPS(cells, steps, time):
    return cells * steps / time * 1e-6

def generate_moment_plots(lattice, moments):
    for i, m in enumerate(moments):
        print("Generating plot %d of %d." % (i+1, len(moments)))

        gid = lattice.memory.gid
        velocity = numpy.reshape(
            [ numpy.sqrt(m[gid(x,y)*3+1]**2 + m[gid(x,y)*3+2]**2) for x, y in lattice.geometry.inner_cells() ],
            lattice.geometry.inner_size())

        plt.figure(figsize=(10, 10))
        plt.imshow(velocity, origin='lower', cmap=plt.get_cmap('seismic'))
        plt.savefig("result/ldc_2d_%02d.png" % i, bbox_inches='tight', pad_inches=0)

nUpdates = 100000
nStat    = 10000

geometry = Geometry(256, 256)

print("Generating kernel using boltzgen...\n")

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']
extras    = ['cell_list_dispatch']

precision = 'single'

generator = Generator(
    model     = BGK(D2Q9, tau = 0.6),
    target    = 'cl',
    precision = precision,
    index     = 'ZYX',
    layout    = 'SOA')

kernel_src  = generator.kernel(geometry, functions, extras)
kernel_src += generator.custom(geometry, """
__kernel void equilibrilize_all(__global ${float_type}* f_next,
                                __global ${float_type}* f_prev)
{
    const unsigned int gid = ${index.gid('get_global_id(0)', 'get_global_id(1)')};
    equilibrilize(f_next, f_prev, gid);
    equilibrilize(f_prev, f_next, gid);
}

__kernel void collect_moments_all(__global ${float_type}* f,
                                  __global ${float_type}* moments)
{
    const unsigned int gid = ${index.gid('get_global_id(0)', 'get_global_id(1)')};
    collect_moments(f, gid, moments);
}
""")

print("Initializing simulation...\n")

lattice = Lattice(geometry, kernel_src, D2Q9, precision = precision)
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
