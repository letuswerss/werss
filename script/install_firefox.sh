#!/bin/bash

# 定义安装目录
INSTALL_DIR="/opt/firefox"
TAR_FILE="firefox-139.0.tar.xz"
# 下载Firefox
echo "正在下载Firefox..."
wget https://ftp.mozilla.org/pub/firefox/releases/139.0/linux-x86_64/zh-CN/firefox-139.0.tar.xz -O $TAR_FILE

# 解压安装包
echo "正在解压安装包..."
mkdir -p $INSTALL_DIR
tar -xf $TAR_FILE -C $INSTALL_DIR --strip-components=1

# 清理安装包
rm $TAR_FILE

# 设置权限
chmod -R 755 $INSTALL_DIR

# 添加到PATH
if ! grep -q "$INSTALL_DIR" ~/.bashrc; then
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
    source ~/.bashrc
fi
ln -s $INSTALL_DIR/firefox /usr/local/bin/
echo "Firefox安装完成！"