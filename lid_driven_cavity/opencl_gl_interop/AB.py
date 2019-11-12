import pyopencl as cl

from common import MomentsTextureBase

from lattice.AB import Lattice

class MomentsTexture(MomentsTextureBase):
    pass

    def collect(self):
        cl.enqueue_acquire_gl_objects(self.lattice.queue, [self.cl_gl_moments])

        if self.lattice.tick:
            self.lattice.program.collect_moments_to_texture(
                self.lattice.queue,
                self.lattice.geometry.size(),
                self.lattice.layout,
                self.lattice.memory.cl_pop_a,
                self.cl_gl_moments)
        else:
            self.lattice.program.collect_moments_to_texture(
                self.lattice.queue,
                self.lattice.geometry.size(),
                self.lattice.layout,
                self.lattice.memory.cl_pop_b,
                self.cl_gl_moments)
