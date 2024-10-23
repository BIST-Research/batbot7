add_library(serial SHARED 
    serial.cpp
    tendon_hardware_interface.cpp
    serial_object_uart_linux.cpp
)

# target_include_directories(serial PUBLIC
#     "${PROJECT_BINARY_DIR}"
#     "${PROJECT_BINARY_DIR}/include"
# )