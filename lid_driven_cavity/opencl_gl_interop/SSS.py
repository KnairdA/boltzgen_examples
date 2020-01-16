import pyopencl as cl

from common import MomentsTextureBase

from lattice.SSS import Lattice

class MomentsTexture(MomentsTextureBase):
    pass

    def collect(self):
        cl.enqueue_acquire_gl_objects(self.lattice.queue, [self.cl_gl_moments])

        self.lattice.program.collect_moments_to_texture(
            self.lattice.queue,
            self.lattice.geometry.size(),
            self.lattice.layout,
            self.lattice.memory.cl_control,
            self.cl_gl_moments)
