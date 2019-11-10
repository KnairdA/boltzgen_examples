cmake_minimum_required(VERSION 3.10)
project(ldc LANGUAGES CXX)
find_package(CUDA QUIET REQUIRED)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

add_custom_command(
	OUTPUT
		kernel.h
		ldc.cu
	COMMAND
		${CMAKE_CURRENT_SOURCE_DIR}/generate.py --output ${CMAKE_CURRENT_BINARY_DIR}
	WORKING_DIRECTORY
		${CMAKE_CURRENT_SOURCE_DIR}
	DEPENDS
		generate.py
		config.py
		ldc.cuda.SSS.mako
)

include_directories(
	${CMAKE_BINARY_DIR}
)

cuda_add_executable(
	ldc
		${CMAKE_CURRENT_BINARY_DIR}/ldc.cu
)
