import numpy
import time
from string import Template

import pyopencl as cl
from pyopencl.tools import get_gl_sharing_context_properties

from boltzgen import Generator, Geometry
from boltzgen.lbm.lattice import D2Q9
from boltzgen.lbm.model   import BGK

from common import CellList

from OpenGL.GL   import *
from OpenGL.GLUT import *
from OpenGL.GL import shaders
from pyrr import matrix44

geometry = Geometry(512, 512)

functions = ['collide_and_stream', 'equilibrilize', 'collect_moments', 'momenta_boundary']
extras    = ['cell_list_dispatch', 'opencl_gl_interop']

precision = 'single'
streaming = 'AA'

import AA
import AB

def glut_window(fullscreen = False):
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)

    if fullscreen:
        window = glutEnterGameMode()
    else:
        glutInitWindowSize(800, 500)
        glutInitWindowPosition(0, 0)
        window = glutCreateWindow("LDC 2D")

    return window

window = glut_window(fullscreen = False)

Lattice = eval('%s.Lattice' % streaming)
MomentsTexture = eval('%s.MomentsTexture' % streaming)

generator = Generator(
    model     = BGK(D2Q9, tau = 0.53),
    target    = 'cl',
    precision = precision,
    streaming = streaming,
    index     = 'ZYX',
    layout    = 'SOA')

kernel_src = generator.kernel(geometry, functions, extras)

cl_platform = cl.get_platforms()[0]
cl_context  = cl.Context(properties=[(cl.context_properties.PLATFORM, cl_platform)] + get_gl_sharing_context_properties())
cl_queue    = cl.CommandQueue(cl_context)

lattice = Lattice(geometry, kernel_src, D2Q9, cl_context, cl_queue, precision = precision)
moments = MomentsTexture(lattice)

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


def get_projection(width, height):
    world_height = geometry.size_y
    world_width  = world_height / height * width

    projection  = matrix44.create_orthogonal_projection(-world_width/2, world_width/2, -world_height/2, world_height/2, -1, 1)
    translation = matrix44.create_from_translation([-geometry.size_x/2, -geometry.size_y/2, 0])

    point_size = width / world_width

    return numpy.matmul(translation, projection), point_size

vertex_shader = shaders.compileShader("""
#version 430

layout (location=0) in vec4 vertex;
                   out vec2 frag_pos;

uniform mat4 projection;

void main() {
    gl_Position = projection * vertex;
    frag_pos    = vertex.xy;
}""", GL_VERTEX_SHADER)

fragment_shader = shaders.compileShader(Template("""
#version 430

in vec2 frag_pos;

uniform sampler2D moments;

out vec4 result;

vec2 unit(vec2 v) {
    return vec2(v[0] / $size_x, v[1] / $size_y);
}

vec3 blueRedPalette(float x) {
    return mix(
        vec3(0.0, 0.0, 1.0),
        vec3(1.0, 0.0, 0.0),
        x
    );
}

void main(){
    const vec2 sample_pos = unit(frag_pos);
    const vec4 data = texture(moments, sample_pos);
    result.a = 1.0;
    result.rgb = blueRedPalette(data[3] / 0.1);
}
""").substitute({
    "size_x": geometry.size_x,
    "size_y": geometry.size_y,
}), GL_FRAGMENT_SHADER)

shader_program = shaders.compileProgram(vertex_shader, fragment_shader)
projection_id = shaders.glGetUniformLocation(shader_program, 'projection')

def on_display():
    for i in range(0,100):
        lattice.evolve()

    moments.collect()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    shaders.glUseProgram(shader_program)
    glUniformMatrix4fv(projection_id, 1, False, numpy.asfortranarray(projection))
    moments.bind()

    glBegin(GL_POLYGON)
    glVertex(0,0,0)
    glVertex(lattice.geometry.size_x,0,0)
    glVertex(lattice.geometry.size_x,lattice.geometry.size_y,0)
    glVertex(0,lattice.geometry.size_y,0)
    glEnd()

    glutSwapBuffers()

def on_reshape(width, height):
    global projection, point_size
    glViewport(0,0,width,height)
    projection, point_size = get_projection(width, height)

def on_timer(t):
    glutTimerFunc(t, on_timer, t)
    glutPostRedisplay()

glutDisplayFunc(on_display)
glutReshapeFunc(on_reshape)
glutTimerFunc(10, on_timer, 10)

glutMainLoop()
