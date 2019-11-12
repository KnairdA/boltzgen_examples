import pyopencl as cl

from common import MomentsTextureBase

from lattice.AA import Lattice

class MomentsTexture(MomentsTextureBase):
    pass

    def collect(self):
        cl.enqueue_acquire_gl_objects(self.lattice.queue, [self.cl_gl_moments])

        if self.lattice.tick:
            self.lattice.program.collect_moments_to_texture_tick(
                self.lattice.queue,
                self.lattice.geometry.size(),
                self.lattice.layout,
                self.lattice.memory.cl_pop,
                self.cl_gl_moments)
        else:
            self.lattice.program.collect_moments_to_texture_tock(
                self.lattice.queue,
                self.lattice.geometry.size(),
                self.lattice.layout,
                self.lattice.memory.cl_pop,
                self.cl_gl_moments)
