cmake_minimum_required(VERSION 3.20)
project(mobigo2_unsp_emu LANGUAGES CXX)
include(CheckIPOSupported)
include(CTest)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(NOT CMAKE_CONFIGURATION_TYPES AND NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()

option(MOBIGO2_NATIVE_OPTIMIZATIONS "Build with host-native CPU optimizations" ON)

find_package(PkgConfig REQUIRED)
pkg_check_modules(SDL2 REQUIRED sdl2)

add_executable(mobigo2_emu
  src/main.cpp
  src/audio.hpp
  src/boot.hpp
  src/bus.hpp
  src/common.hpp
  src/cpu.hpp
  src/devices.hpp
  src/mba_overlay.hpp
  src/usb_panel.hpp
  src/video.hpp
)
target_include_directories(mobigo2_emu PRIVATE ${SDL2_INCLUDE_DIRS})
target_link_directories(mobigo2_emu PRIVATE ${SDL2_LIBRARY_DIRS})
target_link_libraries(mobigo2_emu PRIVATE ${SDL2_LIBRARIES})
target_compile_options(mobigo2_emu PRIVATE ${SDL2_CFLAGS_OTHER} -Wall -Wextra -Wpedantic)
if(MOBIGO2_NATIVE_OPTIMIZATIONS AND CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU")
  target_compile_options(mobigo2_emu PRIVATE $<$<CONFIG:Release>:-march=native>)
endif()

check_ipo_supported(RESULT MOBIGO2_IPO_SUPPORTED OUTPUT MOBIGO2_IPO_ERROR)
if(MOBIGO2_IPO_SUPPORTED)
  set_property(TARGET mobigo2_emu PROPERTY INTERPROCEDURAL_OPTIMIZATION_RELEASE TRUE)
endif()

if(BUILD_TESTING)
  add_executable(audio_test tests/audio_test.cpp)
  target_include_directories(audio_test PRIVATE src ${SDL2_INCLUDE_DIRS})
  target_link_directories(audio_test PRIVATE ${SDL2_LIBRARY_DIRS})
  target_link_libraries(audio_test PRIVATE ${SDL2_LIBRARIES})
  target_compile_options(audio_test PRIVATE ${SDL2_CFLAGS_OTHER} -Wall -Wextra -Wpedantic)
  add_test(NAME audio_test COMMAND audio_test)

  add_executable(watchdog_test tests/watchdog_test.cpp)
  target_include_directories(watchdog_test PRIVATE src ${SDL2_INCLUDE_DIRS})
  target_link_directories(watchdog_test PRIVATE ${SDL2_LIBRARY_DIRS})
  target_link_libraries(watchdog_test PRIVATE ${SDL2_LIBRARIES})
  target_compile_options(watchdog_test PRIVATE ${SDL2_CFLAGS_OTHER} -Wall -Wextra -Wpedantic)
  add_test(NAME watchdog_test COMMAND watchdog_test)

  add_executable(hardware_accuracy_test tests/hardware_accuracy_test.cpp)
  target_include_directories(hardware_accuracy_test PRIVATE src ${SDL2_INCLUDE_DIRS})
  target_link_directories(hardware_accuracy_test PRIVATE ${SDL2_LIBRARY_DIRS})
  target_link_libraries(hardware_accuracy_test PRIVATE ${SDL2_LIBRARIES})
  target_compile_options(hardware_accuracy_test PRIVATE ${SDL2_CFLAGS_OTHER} -Wall -Wextra -Wpedantic)
  add_test(NAME hardware_accuracy_test COMMAND hardware_accuracy_test)
endif()
