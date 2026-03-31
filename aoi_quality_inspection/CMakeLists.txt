cmake_minimum_required(VERSION 3.18)
project(aoi_inference_engine VERSION 1.0.0 LANGUAGES CXX)

# 设置C++标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 查找依赖包
find_package(OpenCV REQUIRED)
find_package(CUDA REQUIRED)
find_package(TensorRT REQUIRED)

# FAISS库
find_path(FAISS_INCLUDE_DIRS faiss/IndexFlat.h
    HINTS /usr/local/include/faiss
    /usr/include/faiss
)
find_library(FAISS_LIBRARIES faiss
    HINTS /usr/local/lib
    /usr/lib
)

# 包含目录
include_directories(
    ${OpenCV_INCLUDE_DIRS}
    ${CUDA_INCLUDE_DIRS}
    ${TENSORRT_INCLUDE_DIR}
    ${FAISS_INCLUDE_DIRS}
    ${CMAKE_SOURCE_DIR}/include
)

# 推理引擎核心库
add_library(inference_core SHARED
    src/tensorrt_engine.cpp
    src/feature_extractor.cpp
    src/faiss_searcher.cpp
    src/anomaly_detector.cpp
    src/inference_engine.cpp
)

target_link_libraries(inference_core
    ${OpenCV_LIBS}
    ${CUDA_LIBRARIES}
    ${TENSORRT_LIBRARIES}
    ${FAISS_LIBRARIES}
    nvinfer
    nvonnxparser
    cudart
)

# gRPC服务
add_executable(inference_server
    src/grpc_server.cpp
    src/main.cpp
)

target_link_libraries(inference_server
    inference_core
    grpc++
    protobuf
    pthread
)

# 测试
enable_testing()
add_subdirectory(tests)

# 安装
install(TARGETS inference_core inference_server
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
