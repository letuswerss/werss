#!/bin/bash

# 安装GTK开发库

# 检查是否为root用户
if [ "$(id -u)" != "0" ]; then
   echo "请使用root用户或sudo运行此脚本"
   exit 1
fi

# 根据发行版安装依赖
if [ -f /etc/debian_version ]; then
    # Debian/Ubuntu系统
    apt-get update
    apt-get install -y wget build-essential
    wget https://download.gnome.org/sources/gtk+/3.24/gtk+-3.24.33.tar.xz
    tar -xf gtk+-3.24.33.tar.xz
    cd gtk+-3.24.33
    ./configure
    make
    make install
elif [ -f /etc/redhat-release ]; then
    # RedHat/CentOS系统
    yum install -y wget gcc make
    wget https://download.gnome.org/sources/gtk+/3.24/gtk+-3.24.33.tar.xz
    tar -xf gtk+-3.24.33.tar.xz
    cd gtk+-3.24.33
    ./configure
    make
    make install
else
    echo "不支持的Linux发行版"
    exit 1
fi
