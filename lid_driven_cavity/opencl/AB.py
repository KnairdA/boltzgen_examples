import pyopencl as cl
mf = cl.mem_flags

import numpy

class Memory:
    def __init__(self, descriptor, geometry, context, float_type):
        self.context    = context
        self.float_type = float_type

        self.size_x = geometry.size_x
        self.size_y = geometry.size_y
        self.size_z = geometry.size_z
        self.volume = self.size_x * self.size_y * self.size_z

        self.pop_size     = descriptor.q * self.volume * self.float_type(0).nbytes
        self.moments_size = 3 * self.volume * self.float_type(0).nbytes

        self.cl_pop_a = cl.Buffer(self.context, mf.READ_WRITE, size=self.pop_size)
        self.cl_pop_b = cl.Buffer(self.context, mf.READ_WRITE, size=self.pop_size)

        self.cl_moments = cl.Buffer(self.context, mf.WRITE_ONLY, size=self.moments_size)

    def gid(self, x, y, z = 0):
        return z * (self.size_x*self.size_y) + y * self.size_x + x;

class Lattice:
    def __init__(self, geometry, kernel_src, descriptor, context, queue, precision = 'single'):
        self.geometry = geometry
        self.descriptor = descriptor

        self.float_type = {
            'single': (numpy.float32, 'float'),
            'double': (numpy.float64, 'double'),
        }.get(precision, None)

        self.layout = None

        self.context = context
        self.queue   = queue

        self.memory = Memory(descriptor, self.geometry, self.context, self.float_type[0])
        self.tick = False

        self.compiler_args = {
            'single': '-cl-single-precision-constant -cl-fast-relaxed-math',
            'double': '-cl-fast-relaxed-math'
        }.get(precision, None)

        self.build_kernel(kernel_src)

        self.program.equilibrilize_domain(
            self.queue, self.geometry.size(), self.layout, self.memory.cl_pop_a, self.memory.cl_pop_b).wait()
        self.program.equilibrilize_domain(
            self.queue, self.geometry.size(), self.layout, self.memory.cl_pop_b, self.memory.cl_pop_a).wait()

        self.tasks = []

    def build_kernel(self, src):
        self.program = cl.Program(self.context, src).build(self.compiler_args)

    def schedule(self, f, cells, *params):
        self.tasks += [ (eval("self.program.%s" % f), cells, params) ]

    def evolve(self):
        if self.tick:
            self.tick = False
            for f, cells, params in self.tasks:
                f(self.queue, cells.size(), self.layout, self.memory.cl_pop_a, self.memory.cl_pop_b, cells.get(), *params)
        else:
            self.tick = True
            for f, cells, params in self.tasks:
                f(self.queue, cells.size(), self.layout, self.memory.cl_pop_b, self.memory.cl_pop_a, cells.get(), *params)

    def sync(self):
        self.queue.finish()

    def get_moments(self):
        moments = numpy.ndarray(shape=(self.memory.volume*(self.descriptor.d+1),1), dtype=self.float_type[0])

        if self.tick:
            self.program.collect_moments_domain(
                self.queue, self.geometry.size(), self.layout, self.memory.cl_pop_b, self.memory.cl_moments)
        else:
            self.program.collect_moments_domain(
                self.queue, self.geometry.size(), self.layout, self.memory.cl_pop_a, self.memory.cl_moments)

        cl.enqueue_copy(self.queue, moments, self.memory.cl_moments).wait();

        return moments
