cmake_minimum_required(VERSION 3.10)
project(ldc_2d LANGUAGES CXX)

add_custom_target(
	boltzgen_kernel
	COMMAND
		${CMAKE_CURRENT_SOURCE_DIR}/generate.py
)

include_directories(
	${CMAKE_BINARY_DIR}
)

add_executable(
	ldc_2d
		ldc_2d.cc
)

add_dependencies(
	ldc_2d
		boltzgen_kernel
)

target_compile_features(
	ldc_2d
	PUBLIC
		cxx_std_17
)

find_package(OpenMP)
if(OpenMP_CXX_FOUND)
	target_link_libraries(
		ldc_2d
		PUBLIC
			OpenMP::OpenMP_CXX
	)
endif()
