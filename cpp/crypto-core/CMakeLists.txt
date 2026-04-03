cmake_minimum_required(VERSION 3.15)
project(nexus_crypto VERSION 1.0.0 LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Включите эту опцию, только если вам нужен Key Escrow (например, для отладки)
option(NEXUS_ENABLE_ESCROW "Enable key escrow (debug only)" OFF)
if(NEXUS_ENABLE_ESCROW)
    add_definitions(-DNEXUS_ENABLE_ESCROW)
endif()

find_package(PkgConfig REQUIRED)
pkg_check_modules(LIBSODIUM REQUIRED libsodium)
pkg_check_modules(LIBSIGNAL REQUIRED libsignal-protocol-c)
pkg_check_modules(LIBOQS REQUIRED liboqs)

include_directories(include ${LIBSODIUM_INCLUDE_DIRS} ${LIBSIGNAL_INCLUDE_DIRS} ${LIBOQS_INCLUDE_DIRS})
link_directories(${LIBSODIUM_LIBRARY_DIRS} ${LIBSIGNAL_LIBRARY_DIRS} ${LIBOQS_LIBRARY_DIRS})

file(GLOB SOURCES "src/*.cpp")
add_library(nexus_crypto SHARED ${SOURCES})
target_link_libraries(nexus_crypto ${LIBSODIUM_LIBRARIES} ${LIBSIGNAL_LIBRARIES} ${LIBOQS_LIBRARIES} pthread)

install(TARGETS nexus_crypto LIBRARY DESTINATION lib)
install(FILES include/nexus_crypto.h DESTINATION include)