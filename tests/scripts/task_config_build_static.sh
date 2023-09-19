#!/bin/bash
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

set -euxo pipefail

BUILD_DIR=$1
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"
cp ../cmake/config.cmake .

""" 需要的选项加上 """
# 关掉这个可以解决掉 make 时的某个 warning
echo set\(USE_LIBBACKTRACE OFF\) >> config.cmake
# 使用contrib sort
echo set\(USE_SORT ON\) >> config.cmake
# 编译时自动找到 CUDA
echo set\(USE_CUDA OFF\) >> config.cmake
echo set\(BUILD_STATIC_RUNTIME ON\) >> config.cmake
echo set\(USE_FALLBACK_STL_MAP ON\) >> config.cmake
echo set\(USE_MSVC_MT ON\) >> config.cmake
echo set\(USE_RPC OFF\) >> config.cmake
echo set\(USE_GRAPH_EXECUTOR OFF\) >> config.cmake
echo set\(USE_PROFILER OFF\) >> config.cmake
echo set\(USE_AOT_EXECUTOR OFF\) >> config.cmake
