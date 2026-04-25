# -*- coding: UTF-8 -*-
import base64
import binascii
def base64_encode(data: str) -> str:
    """
    Base64编码函数
    
    Args:
        data: 需要编码的字符串
        
    Returns:
        Base64编码后的字符串
    """
    if not data:
        return ""
    
    # 将字符串转换为bytes
    data_bytes = data.encode('utf-8')
    
    # 进行base64编码
    encoded_bytes = base64.b64encode(data_bytes)
    
    # 将bytes转换为字符串
    return encoded_bytes.decode('utf-8')


def base64_decode(encoded_data: str) -> str:
    """
    Base64解码函数
    
    Args:
        encoded_data: Base64编码的字符串
        
    Returns:
        解码后的原始字符串
        
    Raises:
        binascii.Error: 如果输入不是有效的base64编码
    """
    if not encoded_data:
        return ""
    
    try:
        # 将字符串转换为bytes
        encoded_bytes = encoded_data.encode('utf-8')
        
        # 进行base64解码
        decoded_bytes = base64.b64decode(encoded_bytes)
        
        # 将bytes转换为字符串
        return decoded_bytes.decode('utf-8')
    except binascii.Error as e:
        raise ValueError(f"无效的base64编码: {e}")


def base64_encode_bytes(data: bytes) -> bytes:
    """
    Base64编码函数（字节版本）
    
    Args:
        data: 需要编码的字节数据
        
    Returns:
        Base64编码后的字节数据
    """
    if not data:
        return b""
    
    return base64.b64encode(data)


def base64_decode_bytes(encoded_data: bytes) -> bytes:
    """
    Base64解码函数（字节版本）
    
    Args:
        encoded_data: Base64编码的字节数据
        
    Returns:
        解码后的原始字节数据
        
    Raises:
        binascii.Error: 如果输入不是有效的base64编码
    """
    if not encoded_data:
        return b""
    
    try:
        return base64.b64decode(encoded_data)
    except binascii.Error as e:
        raise ValueError(f"无效的base64编码: {e}")


def base64_url_safe_encode(data: str) -> str:
    """
    URL安全的Base64编码函数
    
    Args:
        data: 需要编码的字符串
        
    Returns:
        URL安全的Base64编码字符串（+和/被替换为-和_）
    """
    if not data:
        return ""
    
    # 标准base64编码
    standard_encoded = base64_encode(data)
    
    # 转换为URL安全格式
    url_safe = standard_encoded.replace('+', '-').replace('/', '_').rstrip('=')
    
    return url_safe


def base64_url_safe_decode(encoded_data: str) -> str:
    """
    URL安全的Base64解码函数
    
    Args:
        encoded_data: URL安全的Base64编码字符串
        
    Returns:
        解码后的原始字符串
        
    Raises:
        binascii.Error: 如果输入不是有效的base64编码
    """
    if not encoded_data:
        return ""
    
    # 恢复为标准base64格式
    # 添加填充字符
    padding_needed = len(encoded_data) % 4
    if padding_needed:
        encoded_data += '=' * (4 - padding_needed)
    
    # 替换回标准字符
    standard_encoded = encoded_data.replace('-', '+').replace('_', '/')
    
    # 使用标准解码
    return base64_decode(standard_encoded)


if __name__ == "__main__":
    # 测试代码
    test_string = """
"""
    print(base64_encode(test_string))
    
    # # 测试标准base64编码
    # encoded = base64_encode(test_string)
    # print(f"原始字符串: {test_string}")
    # print(f"Base64编码: {encoded}")
    
    # # 测试解码
    # decoded = base64_decode(encoded)
    # print(f"Base64解码: {decoded}")
    
    # # 测试URL安全编码
    # url_encoded = base64_url_safe_encode(test_string)
    # print(f"URL安全Base64编码: {url_encoded}")
    
    # # 测试URL安全解码
    # url_decoded = base64_url_safe_decode(url_encoded)
    # print(f"URL安全Base64解码: {url_decoded}")
    
    # # 验证结果
    # assert test_string == decoded == url_decoded, "编解码测试失败"
    # print("所有测试通过！")