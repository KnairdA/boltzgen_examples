import pyopencl as cl
mf = cl.mem_flags

from OpenGL.GL import *
from OpenGL.arrays import vbo

import numpy

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


class MomentsTextureBase:
    def __init__(self, lattice):
        self.lattice = lattice
        self.gl_texture_buffer = numpy.ndarray(shape=(self.lattice.memory.volume, 4), dtype=self.lattice.memory.float_type)
        self.gl_texture_buffer[:,:] = 0.0

        self.gl_moments = glGenTextures(1)
        self.gl_texture_type = {2: GL_TEXTURE_2D, 3: GL_TEXTURE_3D}.get(self.lattice.descriptor.d)
        glBindTexture(self.gl_texture_type, self.gl_moments)

        if self.gl_texture_type == GL_TEXTURE_3D:
            glTexImage3D(self.gl_texture_type, 0, GL_RGBA32F, self.lattice.memory.size_x, self.lattice.memory.size_y, self.lattice.memory.size_z, 0, GL_RGBA, GL_FLOAT, self.gl_texture_buffer)
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_WRAP_T,     GL_CLAMP_TO_EDGE)
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_WRAP_S,     GL_CLAMP_TO_EDGE)
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_WRAP_R,     GL_CLAMP_TO_EDGE)
            self.cl_gl_moments  = cl.GLTexture(self.lattice.context, mf.READ_WRITE, self.gl_texture_type, 0, self.gl_moments, 3)
        elif self.gl_texture_type == GL_TEXTURE_2D:
            glTexImage2D(self.gl_texture_type, 0, GL_RGBA32F, self.lattice.memory.size_x, self.lattice.memory.size_y, 0, GL_RGBA, GL_FLOAT, self.gl_texture_buffer)
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_MIN_FILTER, GL_NEAREST);
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_WRAP_T,     GL_CLAMP_TO_EDGE)
            glTexParameteri(self.gl_texture_type, GL_TEXTURE_WRAP_S,     GL_CLAMP_TO_EDGE)
            self.cl_gl_moments  = cl.GLTexture(self.lattice.context, mf.READ_WRITE, self.gl_texture_type, 0, self.gl_moments, 2)

    def bind(self, location = GL_TEXTURE0):
        glEnable(self.gl_texture_type)
        glActiveTexture(location);
        glBindTexture(self.gl_texture_type, self.gl_moments)
