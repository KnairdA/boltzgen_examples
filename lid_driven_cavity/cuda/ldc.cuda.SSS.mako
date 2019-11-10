#include <cstdint>
#include <memory>
#include <vector>
#include <chrono>
#include <iostream>
#include <fstream>

#include "kernel.h"

void write_moments_to_vtk(const std::string& path, ${float_type}* u) {
    std::ofstream fout;
    fout.open(path.c_str());

    fout << "# vtk DataFile Version 3.0\n";
    fout << "lbm_output\n";
    fout << "ASCII\n";
    fout << "DATASET RECTILINEAR_GRID\n";
% if descriptor.d == 2:
    fout << "DIMENSIONS " << ${geometry.size_x-2} << " " << ${geometry.size_y-2} << " 1" << "\n";
% else:
    fout << "DIMENSIONS " << ${geometry.size_x-2} << " " << ${geometry.size_y-2} << " " << ${geometry.size_z-2} << "\n";
% endif

    fout << "X_COORDINATES " << ${geometry.size_x-2} << " float\n";
    for( std::size_t x = 1; x < ${geometry.size_x-1}; ++x ) {
        fout << x << " ";
    }

    fout << "\nY_COORDINATES " << ${geometry.size_y-2} << " float\n";
    for( std::size_t y = 1; y < ${geometry.size_y-1}; ++y ) {
        fout << y << " ";
    }

% if descriptor.d == 2:
    fout << "\nZ_COORDINATES " << 1 << " float\n";
    fout << 0 << "\n";
    fout << "POINT_DATA " << ${(geometry.size_x-2) * (geometry.size_y-2)} << "\n";
% else:
    fout << "\nZ_COORDINATES " << ${geometry.size_z-2} << " float\n";
    for( std::size_t z = 1; z < ${geometry.size_z-1}; ++z ) {
        fout << z << " ";
    }
    fout << "\nPOINT_DATA " << ${(geometry.size_x-2) * (geometry.size_y-2) * (geometry.size_z-2)} << "\n";
% endif

    fout << "VECTORS velocity float\n";
% if descriptor.d == 2:
    for ( std::size_t y = 1; y < ${geometry.size_y-1}; ++y ) {
        for ( std::size_t x = 1; x < ${geometry.size_x-1}; ++x ) {
            const std::size_t gid = x*${geometry.size_y}+y;
            fout << u[gid*${descriptor.d}+0] << " " << u[gid*${descriptor.d}+1] << " 0\n";
        }
    }
% else:
    for ( std::size_t z = 1; z < ${geometry.size_z-1}; ++z ) {
        for ( std::size_t y = 1; y < ${geometry.size_y-1}; ++y ) {
            for ( std::size_t x = 1; x < ${geometry.size_x-1}; ++x ) {
                const std::size_t gid = x*${geometry.size_y*geometry.size_z}+y*${geometry.size_z}+z;
                fout << u[gid*${descriptor.d}+0] << " " << u[gid*${descriptor.d}+1] << " " << u[gid*${descriptor.d}+2] << "\n";
            }
        }
    }
% endif

    fout.close();
}

void simulate(std::size_t nStep)
{
<%
    padding = (max(geometry.size_x,geometry.size_y,geometry.size_z)+1)**(descriptor.d-1)
%>
    ${float_type}* f_aa;
    cudaMalloc(&f_aa, ${(geometry.volume+2*padding)*descriptor.q}*sizeof(${float_type}));

    ${float_type}** f;
    cudaMalloc(&f, ${descriptor.q}*sizeof(${float_type}*));

    ${float_type}* device_moments_rho;
    cudaMalloc(&device_moments_rho, ${geometry.volume} * sizeof(${float_type}));
    ${float_type}* device_moments_u;
    cudaMalloc(&device_moments_u, ${geometry.volume*descriptor.d} * sizeof(${float_type}));
    std::vector<${float_type}> moments_u(${geometry.volume*descriptor.d});

    init_sss_control_structure<<<1,1>>>(f_aa, f);
    cudaDeviceSynchronize();

    std::vector<std::size_t> ghost;
    std::vector<std::size_t> bulk;
    std::vector<std::size_t> lid_bc;
    std::vector<std::size_t> box_bc;

    for (int iX = 0; iX < ${geometry.size_x}; ++iX) {
        for (int iY = 0; iY < ${geometry.size_y}; ++iY) {
% if descriptor.d == 2:
            const std::size_t iCell = iX*${geometry.size_y} + iY;
            if (iX == 0 || iY == 0 || iX == ${geometry.size_x-1} || iY == ${geometry.size_y-1}) {
                ghost.emplace_back(iCell);
            } else if (iY == ${geometry.size_y-2}) {
                lid_bc.emplace_back(iCell);
            } else if (iX == 1 || iX == ${geometry.size_x-2} || iY == 1) {
                box_bc.emplace_back(iCell);
            } else {
                bulk.emplace_back(iCell);
            }
% elif descriptor.d == 3:
            for (int iZ = 0; iZ < ${geometry.size_z}; ++iZ) {
                const std::size_t iCell = iX*${geometry.size_y*geometry.size_z} + iY*${geometry.size_z} + iZ;
                if (   iX == 0 || iY == 0 || iZ == 0
                    || iX == ${geometry.size_x-1}
                    || iY == ${geometry.size_y-1}
                    || iZ == ${geometry.size_z-1}) {
                    ghost.emplace_back(iCell);
                } else if (iZ == ${geometry.size_z-2}) {
                    lid_bc.emplace_back(iCell);
                } else if (   iX == 1 || iX == ${geometry.size_x-2}
                           || iY == 1 || iY == ${geometry.size_y-2}
                           || iZ == 1) {
                    box_bc.emplace_back(iCell);
                } else {
                    bulk.emplace_back(iCell);
                }
            }
% endif
        }
    }

    std::cout << "#ghost  : " << ghost.size()  << std::endl;
    std::cout << "#bulk   : " << bulk.size()   << std::endl;
    std::cout << "#lid    : " << lid_bc.size() << std::endl;
    std::cout << "#wall   : " << box_bc.size() << std::endl;
    std::cout << std::endl;

    std::size_t* device_ghost_cells;
    std::size_t* device_bulk_cells;
    std::size_t* device_lid_bc_cells;
    std::size_t* device_box_bc_cells;

    cudaMalloc(&device_ghost_cells,  ghost.size()  * sizeof(std::size_t));
    cudaMalloc(&device_bulk_cells,   bulk.size()   * sizeof(std::size_t));
    cudaMalloc(&device_lid_bc_cells, lid_bc.size() * sizeof(std::size_t));
    cudaMalloc(&device_box_bc_cells, box_bc.size() * sizeof(std::size_t));

    cudaMemcpy(device_ghost_cells,  ghost.data(),  ghost.size() * sizeof(std::size_t), cudaMemcpyHostToDevice);
    cudaMemcpy(device_bulk_cells,   bulk.data(),   bulk.size()  * sizeof(std::size_t), cudaMemcpyHostToDevice);
    cudaMemcpy(device_lid_bc_cells, lid_bc.data(), lid_bc.size()* sizeof(std::size_t), cudaMemcpyHostToDevice);
    cudaMemcpy(device_box_bc_cells, box_bc.data(), box_bc.size()* sizeof(std::size_t), cudaMemcpyHostToDevice);

    cudaDeviceSynchronize();

    const std::size_t block_size = 32;
    std::size_t block_count = 0;

    block_count = (ghost.size() + block_size - 1) / block_size;
    equilibrilize<<<block_count,block_size>>>(f, device_ghost_cells, ghost.size());

    block_count = (bulk.size() + block_size - 1) / block_size;
    equilibrilize<<<block_count,block_size>>>(f, device_bulk_cells, bulk.size());

    block_count = (box_bc.size() + block_size - 1) / block_size;
    equilibrilize<<<block_count,block_size>>>(f, device_box_bc_cells, box_bc.size());

    block_count = (lid_bc.size() + block_size - 1) / block_size;
    equilibrilize<<<block_count,block_size>>>(f, device_lid_bc_cells, lid_bc.size());

    cudaDeviceSynchronize();

    auto start = std::chrono::high_resolution_clock::now();

    for (std::size_t iStep = 1; iStep <= nStep; ++iStep) {
        block_count = (ghost.size() + block_size - 1) / block_size;
        equilibrilize<<<block_count,block_size>>>(f, device_ghost_cells, ghost.size());

        block_count = (bulk.size() + block_size - 1) / block_size;
        collide_and_stream<<<block_count,block_size>>>(f, device_bulk_cells, bulk.size());

        block_count = (box_bc.size() + block_size - 1) / block_size;
% if descriptor.d == 2:
        velocity_momenta_boundary<<<block_count,block_size>>>(f, device_box_bc_cells, box_bc.size(), 0.0, 0.0);
% else:
        velocity_momenta_boundary<<<block_count,block_size>>>(f, device_box_bc_cells, box_bc.size(), 0.0, 0.0, 0.0);
% endif

        block_count = (lid_bc.size() + block_size - 1) / block_size;
% if descriptor.d == 2:
        velocity_momenta_boundary<<<block_count,block_size>>>(f, device_lid_bc_cells, lid_bc.size(), 0.05, 0.0);
% else:
        velocity_momenta_boundary<<<block_count,block_size>>>(f, device_lid_bc_cells, lid_bc.size(), 0.05, 0.0, 0.0);
% endif

        cudaDeviceSynchronize();
        update_sss_control_structure<<<1,1>>>(f);
        cudaDeviceSynchronize();

        if (iStep % 1000 == 0) {
            auto duration = std::chrono::duration_cast<std::chrono::duration<float>>(
                std::chrono::high_resolution_clock::now() - start);
                std::cout << "iStep = " << iStep << "; ~" << 1000*${geometry.volume}/(1e6*duration.count()) << " MLUPS" << std::endl;

            block_count = (bulk.size() + block_size - 1) / block_size;
            collect_moments<<<block_count,block_size>>>(f, device_bulk_cells, bulk.size(), device_moments_rho, device_moments_u);
            cudaMemcpy(moments_u.data(), device_moments_u, ${geometry.volume*descriptor.d}*sizeof(${float_type}), cudaMemcpyDeviceToHost);
            write_moments_to_vtk("result/ldc_" + std::to_string(iStep) + ".vtk", moments_u.data());

            start = std::chrono::high_resolution_clock::now();
        }
    }

    cudaFree(device_ghost_cells);
    cudaFree(device_bulk_cells);
    cudaFree(device_lid_bc_cells);
    cudaFree(device_box_bc_cells);
    cudaFree(device_moments_rho);
    cudaFree(device_moments_u);
    cudaFree(f);
    cudaFree(f_aa);
}

int main() {
    simulate(20000);
}
