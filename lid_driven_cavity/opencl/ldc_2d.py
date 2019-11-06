import numpy
import time

from boltzgen import Generator, Geometry
from boltzgen.lbm.lattice import D2Q9
from boltzgen.lbm.model   import BGK

from common import CellList, generate_moment_plots

nUpdates = 100000
nStat    = 10000

geometry = Geometry(512, 512)

print("Generating kernel using boltzgen...\n")

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']
extras    = ['cell_list_dispatch']

precision = 'single'
streaming = 'AA'

import AA
import AB

Lattice = eval('%s.Lattice' % streaming)
HelperTemplate = eval('%s.HelperTemplate' % streaming)

def MLUPS(cells, steps, time):
    return cells * steps / time * 1e-6

generator = Generator(
    model     = BGK(D2Q9, tau = 0.54),
    target    = 'cl',
    precision = precision,
    streaming = streaming,
    index     = 'ZYX',
    layout    = 'SOA')

kernel_src  = generator.kernel(geometry, functions, extras)
kernel_src += generator.custom(geometry, HelperTemplate)

print("Initializing simulation...\n")

lattice = Lattice(geometry, kernel_src, D2Q9, precision = precision)
gid = lattice.memory.gid

ghost_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.cells() if x == 0 or y == 0 or x == geometry.size_x-1 or y == geometry.size_y-1 ])
bulk_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if x > 1 and x < geometry.size_x-2 and y > 1 and y < geometry.size_y-2 ])
wall_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if x == 1 or y == 1 or x == geometry.size_x-2 ])
lid_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if y == geometry.size_y-2 ])

if streaming == 'AB':
    lattice.schedule('collide_and_stream_cells', bulk_cells)
    lattice.schedule('velocity_momenta_boundary_cells', wall_cells, numpy.array([0.0, 0.0], dtype=lattice.float_type[0]))
    lattice.schedule('velocity_momenta_boundary_cells', lid_cells,  numpy.array([0.1, 0.0], dtype=lattice.float_type[0]))

elif streaming == 'AA':
    lattice.schedule_tick('collide_and_stream_tick_cells', bulk_cells)
    lattice.schedule_tick('velocity_momenta_boundary_tick_cells', wall_cells, numpy.array([0.0, 0.0], dtype=lattice.float_type[0]))
    lattice.schedule_tick('velocity_momenta_boundary_tick_cells', lid_cells,  numpy.array([0.1, 0.0], dtype=lattice.float_type[0]))

    lattice.schedule_tock('equilibrilize_tick_cells', ghost_cells)
    lattice.schedule_tock('collide_and_stream_tock_cells', bulk_cells)
    lattice.schedule_tock('velocity_momenta_boundary_tock_cells', wall_cells, numpy.array([0.0, 0.0], dtype=lattice.float_type[0]))
    lattice.schedule_tock('velocity_momenta_boundary_tock_cells', lid_cells,  numpy.array([0.1, 0.0], dtype=lattice.float_type[0]))


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
