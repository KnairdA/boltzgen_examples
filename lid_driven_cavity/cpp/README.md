# Lid driven cavity

This example models the common lid driven cavity example.
Note that the actual optimized C++ implementation is generated using the _boltzgen_ library.

See `config.py` for various configuration options. Both 2D and 3D are supported.

## Build instructions

```
mkdir build
cd build
cmake ..
make
./ldc
```

This should result in some summarizing CLI output in addition to a `test.vtk` file for visualization in Paraview.
