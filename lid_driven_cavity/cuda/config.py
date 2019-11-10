from boltzgen.lbm.lattice import *
from boltzgen import Geometry

descriptor = D2Q9
geometry   = Geometry(512, 512)
tau        = 0.52
precision  = 'single'
streaming  = 'SSS'

## 3D LDC
#descriptor = D3Q19
#geometry   = Geometry(64, 64, 64)
#tau        = 0.6
#precision  = 'single'
#streaming  = 'SSS'
