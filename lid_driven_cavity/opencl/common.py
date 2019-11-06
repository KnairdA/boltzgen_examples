import pyopencl as cl
mf = cl.mem_flags

import numpy

import matplotlib
matplotlib.use('AGG')
import matplotlib.pyplot as plt


class CellList:
    def __init__(self, context, queue, float_type, cells):
        self.cl_cells = cl.Buffer(context, mf.READ_ONLY, size=len(cells) * numpy.uint32(0).nbytes)
        self.np_cells = numpy.ndarray(shape=(len(cells), 1), dtype=numpy.uint32)
        self.np_cells[:,0] = cells[:]

        cl.enqueue_copy(queue, self.cl_cells, self.np_cells).wait();

    def get(self):
        return self.cl_cells

    def size(self):
        return (len(self.np_cells), 1, 1)

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
