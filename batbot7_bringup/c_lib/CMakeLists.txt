cmake_minimum_required(VERSION 3.20)
project(CBatLib)

set(BUILD_SHARED_LIBS true)

find_package(Python3 COMPONENTS Interpreter Development)

include_directories((include))

add_executable(main main.cpp)

add_subdirectory(src)
target_link_libraries(main PUBLIC serial)
