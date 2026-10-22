cmake_minimum_required(VERSION 3.13)
set(PICO_BOARD pico2 CACHE STRING "Board type")   # RP2350-Plus is Pico 2 compatible
include(pico_sdk_import.cmake)
project(hamref_fw C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

add_executable(hamref
    src/main.c src/dac.c src/gnss.c src/disciplining.c)
pico_generate_pio_header(hamref ${CMAKE_CURRENT_LIST_DIR}/src/hamref_gate.pio)
target_include_directories(hamref PRIVATE src)
target_link_libraries(hamref pico_stdlib hardware_pio hardware_i2c hardware_uart)
pico_enable_stdio_usb(hamref 1)
pico_enable_stdio_uart(hamref 0)
pico_add_extra_outputs(hamref)

# Host-side simulation of the disciplining loop (no hardware needed):
#   cc -O2 -o sim sim/sim_main.c src/disciplining.c -Isrc -lm
