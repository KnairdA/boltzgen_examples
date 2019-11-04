#include <cstdint>
#include <memory>
#include <vector>
#include <chrono>
#include <iostream>
#include <fstream>

#include "kernel.h"

void collect_moments_to_vtk(const std::string& path, ${float_type}* f) {
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

    ${float_type} rho;
    ${float_type} u[${descriptor.d}];

    fout << "VECTORS velocity float\n";
% if descriptor.d == 2:
    for ( std::size_t y = 1; y < ${geometry.size_y-1}; ++y ) {
        for ( std::size_t x = 1; x < ${geometry.size_x-1}; ++x ) {
            collect_moments(f, x*${geometry.size_y}+y, rho, u);
            fout << u[0] << " " << u[1] << " 0\n";
        }
    }
% else:
    for ( std::size_t z = 1; z < ${geometry.size_z-1}; ++z ) {
        for ( std::size_t y = 1; y < ${geometry.size_y-1}; ++y ) {
            for ( std::size_t x = 1; x < ${geometry.size_x-1}; ++x ) {
                collect_moments(f, x*${geometry.size_y*geometry.size_z}+y*${geometry.size_z}+z, rho, u);
                fout << u[0] << " " << u[1] << " " << u[2] << "\n";
            }
        }
    }
% endif

    fout << "SCALARS density float 1\n";
    fout << "LOOKUP_TABLE default\n";
% if descriptor.d == 2:
    for ( std::size_t y = 1; y < ${geometry.size_y-1}; ++y ) {
        for ( std::size_t x = 1; x < ${geometry.size_x-1}; ++x ) {
            collect_moments(f, x*${geometry.size_y}+y, rho, u);
            fout << rho << "\n";
        }
    }
% else:
    for ( std::size_t z = 1; z < ${geometry.size_z-1}; ++z ) {
        for ( std::size_t y = 1; y < ${geometry.size_y-1}; ++y ) {
            for ( std::size_t x = 1; x < ${geometry.size_x-1}; ++x ) {
                collect_moments(f, x*${geometry.size_y*geometry.size_z}+y*${geometry.size_z}+z, rho, u);
                fout << rho << "\n";
            }
        }
    }
% endif

    fout.close();
}

void simulate(std::size_t nStep)
{
    auto f_a = std::make_unique<${float_type}[]>(${geometry.volume*descriptor.q});
    auto f_b = std::make_unique<${float_type}[]>(${geometry.volume*descriptor.q});

    ${float_type}* f_prev = f_a.get();
    ${float_type}* f_next = f_b.get();

    std::vector<std::size_t> bulk;
    std::vector<std::size_t> lid_bc;
    std::vector<std::size_t> box_bc;

    for (int iX = 1; iX < ${geometry.size_x-1}; ++iX) {
        for (int iY = 1; iY < ${geometry.size_y-1}; ++iY) {
% if descriptor.d == 2:
            const std::size_t iCell = iX*${geometry.size_y} + iY;
            if (iY == ${geometry.size_y-2}) {
                lid_bc.emplace_back(iCell);
            } else if (iX == 1 || iX == ${geometry.size_x-2} || iY == 1) {
                box_bc.emplace_back(iCell);
            } else {
                bulk.emplace_back(iCell);
            }
% elif descriptor.d == 3:
            for (int iZ = 0; iZ < ${geometry.size_z}; ++iZ) {
                const std::size_t iCell = iX*${geometry.size_y*geometry.size_z} + iY*${geometry.size_z} + iZ;
                if (iZ == ${geometry.size_z-2}) {
                    lid_bc.emplace_back(iCell);
                } else if (iX == 1 || iX == ${geometry.size_x-2} || iY == 1 || iY == ${geometry.size_y-2} || iZ == 1) {
                    box_bc.emplace_back(iCell);
                } else {
                    bulk.emplace_back(iCell);
                }
            }
% endif
        }
    }

    std::cout << "#bulk   : " << bulk.size()   << std::endl;
    std::cout << "#lid    : " << lid_bc.size() << std::endl;
    std::cout << "#wall   : " << box_bc.size() << std::endl;
    std::cout << "#steps  : " << nStep         << std::endl;
    std::cout << std::endl;

#pragma omp parallel for
    for (std::size_t iCell = 0; iCell < ${geometry.volume}; ++iCell) {
        equilibrilize(f_prev, f_next, iCell);
        equilibrilize(f_next, f_prev, iCell);
    }

    const auto start = std::chrono::high_resolution_clock::now();

    for (std::size_t iStep = 0; iStep < nStep; ++iStep) {
        if (iStep % 2 == 0) {
            f_next = f_a.get();
            f_prev = f_b.get();
        } else {
            f_next = f_b.get();
            f_prev = f_a.get();
        }

#pragma omp parallel for
        for (std::size_t i = 0; i < bulk.size(); ++i) {
            collide_and_stream(f_next, f_prev, bulk[i]);
        }
        ${float_type} u[${descriptor.d}] { 0. };
#pragma omp parallel for
        for (std::size_t i = 0; i < box_bc.size(); ++i) {
            velocity_momenta_boundary(f_next, f_prev, box_bc[i], u);
        }
        u[0] = 0.05;
#pragma omp parallel for
        for (std::size_t i = 0; i < lid_bc.size(); ++i) {
            velocity_momenta_boundary(f_next, f_prev, lid_bc[i], u);
        }
    }

    auto duration = std::chrono::duration_cast<std::chrono::duration<double>>(
        std::chrono::high_resolution_clock::now() - start);

    std::cout << "MLUPS   : " << nStep*${geometry.volume}/(1e6*duration.count()) << std::endl;

    collect_moments_to_vtk("test.vtk", f_next);
}

int main() {
    simulate(10000);
}
