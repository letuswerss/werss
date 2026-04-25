#!/bin/bash

# 可选镜像源列表
SOURCES=(
    "清华大学" "https://pypi.tuna.tsinghua.edu.cn/simple/"
    "阿里云" "https://mirrors.aliyun.com/pypi/simple/"
    "中国科技大学" "https://pypi.mirrors.ustc.edu.cn/simple/"
    "豆瓣" "http://pypi.douban.com/simple/"
    "华为云" "https://repo.huaweicloud.com/repository/pypi/simple/"
)

# 默认镜像源（清华大学）
DEFAULT_INDEX_URL= $ {SOURCES}<dfn seq=source_group_web_1 type=source_group_web>1</dfn>

# 提示用户选择镜像源
echo "请选择pip镜像源："
PS3="请输入数字（默认回车选清华大学）："
select source in " $ {SOURCES[@]}"; do
    if [[ -z " $ REPLY" ]]; then
        INDEX_URL= $ DEFAULT_INDEX_URL
        break
    elif [[ " $ REPLY" -le  $ {#SOURCES[@]} && " $ REPLY" % 2 -eq 1 ]]; then
        INDEX_URL= $ {SOURCES[ $ ((REPLY+1))]}
        break
    else
        echo "无效输入，请重新选择！"
    fi
done

# 创建pip配置目录
mkdir -p ～/.pip

# 生成pip配置文件
cat <<EOF > ～/.pip/pip.conf
[global]
index-url =  $ INDEX_URL
trusted-host =  $ (echo  $ INDEX_URL | sed 's|https://||; s|/simple/||')
EOF

# 输出配置信息
echo -e "\n配置完成，当前镜像源为："
pip config list | grep index-url