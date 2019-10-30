cmake_minimum_required(VERSION 3.10)
project(ldc LANGUAGES CXX)

if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release)
endif()

set(CMAKE_CXX_FLAGS_RELEASE "-O3")

add_custom_command(
	OUTPUT
		kernel.h
		ldc.cpp
	COMMAND
		${CMAKE_CURRENT_SOURCE_DIR}/generate.py --output ${CMAKE_CURRENT_BINARY_DIR}
	WORKING_DIRECTORY
		${CMAKE_CURRENT_SOURCE_DIR}
	DEPENDS
		generate.py config.py ldc.cpp.mako
)

include_directories(
	${CMAKE_BINARY_DIR}
)

add_executable(
	ldc
		${CMAKE_CURRENT_BINARY_DIR}/ldc.cpp
)

target_compile_features(
	ldc
	PUBLIC
		cxx_std_17
)

find_package(OpenMP)
if(OpenMP_CXX_FOUND)
	target_link_libraries(
		ldc
		PUBLIC
			OpenMP::OpenMP_CXX
	)
endif()
