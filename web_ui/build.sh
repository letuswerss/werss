#!/bin/bash

# 设置路径变量
DIST_DIR="dist"
TARGET_DIR="../static"
pnpm install
# 执行构建
pnpm build

# 复制文件到static目录
echo "正在复制构建文件到$TARGET_DIR..."
rm -rf $TARGET_DIR/*
cp -rf $DIST_DIR/* $TARGET_DIR/