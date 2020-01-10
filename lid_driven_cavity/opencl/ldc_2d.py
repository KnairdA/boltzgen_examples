import numpy
import time

import pyopencl as cl

from boltzgen import Generator, Geometry
from boltzgen.lbm.lattice import D2Q9
from boltzgen.lbm.model   import BGK

from common import CellList, generate_moment_plots

nUpdates = 20000
nStat    = 1000

geometry = Geometry(512, 512)

print("Generating kernel using boltzgen...\n")

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']
extras    = ['cell_list_dispatch']

precision = 'single'
streaming = 'SSS'

if streaming == 'SSS':
    functions = functions + ['update_sss_control_structure']

import AB
import AA
import SSS

Lattice = eval('%s.Lattice' % streaming)

def MLUPS(cells, steps, time):
    return cells * steps / time * 1e-6

generator = Generator(
    model     = BGK(D2Q9, tau = 0.54),
    target    = 'cl',
    precision = precision,
    streaming = streaming,
    index     = 'ZYX',
    layout    = 'SOA')

kernel_src = generator.kernel(geometry, functions, extras)

print("Constructing OpenCL context...\n")

cl_platform = cl.get_platforms()[0]
cl_context  = cl.Context(properties=[(cl.context_properties.PLATFORM, cl_platform)])
cl_queue    = cl.CommandQueue(cl_context)

print("Initializing simulation...\n")

lattice = Lattice(geometry, kernel_src, D2Q9, cl_context, cl_queue, precision = precision)
gid = lattice.memory.gid

ghost_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.cells() if x == 0 or y == 0 or x == geometry.size_x-1 or y == geometry.size_y-1 ])
bulk_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if x > 1 and x < geometry.size_x-2 and y > 1 and y < geometry.size_y-2 ])
wall_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if x == 1 or y == 1 or x == geometry.size_x-2 ])
lid_cells = CellList(lattice.context, lattice.queue, lattice.float_type,
    [ gid(x,y) for x, y in geometry.inner_cells() if y == geometry.size_y-2 ])

if streaming == 'SSS':
    lattice.schedule('equilibrilize', ghost_cells)

if streaming in ['AB', 'SSS']:
    lattice.schedule('collide_and_stream', bulk_cells)
    lattice.schedule('velocity_momenta_boundary', wall_cells, numpy.array([0.0, 0.0], dtype=lattice.float_type[0]))
    lattice.schedule('velocity_momenta_boundary', lid_cells,  numpy.array([0.1, 0.0], dtype=lattice.float_type[0]))

elif streaming == 'AA':
    lattice.schedule_tick('collide_and_stream_tick', bulk_cells)
    lattice.schedule_tick('velocity_momenta_boundary_tick', wall_cells, numpy.array([0.0, 0.0], dtype=lattice.float_type[0]))
    lattice.schedule_tick('velocity_momenta_boundary_tick', lid_cells,  numpy.array([0.1, 0.0], dtype=lattice.float_type[0]))

    lattice.schedule_tock('equilibrilize_tick', ghost_cells)
    lattice.schedule_tock('collide_and_stream_tock', bulk_cells)
    lattice.schedule_tock('velocity_momenta_boundary_tock', wall_cells, numpy.array([0.0, 0.0], dtype=lattice.float_type[0]))
    lattice.schedule_tock('velocity_momenta_boundary_tock', lid_cells,  numpy.array([0.1, 0.0], dtype=lattice.float_type[0]))


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
