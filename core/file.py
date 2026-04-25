import hashlib
import hmac
import os
from base64 import b64encode, b64decode

class FileCrypto:
    """
    简化版对称加解密类(使用HMAC和SHA256)
    安全性低于AES，但不需要额外安装库
    """
    
    def __init__(self, password: str):
        """
        初始化加密器
        :param password: 加密密码，如果为空字符串则跳过加解密
        """
        self.key = hashlib.sha256(password.encode()).digest() if password !=None else None
    
    def encrypt(self, data: bytes) -> bytes:
        """
        加密数据
        :param data: 要加密的原始数据
        :return: 加密后的数据（如果密钥为空则直接返回原始数据）
        """
        if self.key is None:
            return data
        h = hmac.new(self.key, data, hashlib.sha256)
        return h.digest() + data
    
    def decrypt(self, encrypted_data: bytes) -> bytes:
        """
        解密数据
        :param encrypted_data: 加密数据
        :return: 解密后的原始数据（如果密钥为空则直接返回原始数据）
        """
        if self.key is None:
            return encrypted_data
            
        if len(encrypted_data) < 32:
            raise ValueError("Invalid encrypted data")
        
        mac = encrypted_data[:32]
        data = encrypted_data[32:]
        
        h = hmac.new(self.key, data, hashlib.sha256)
        if not hmac.compare_digest(mac, h.digest()):
            raise ValueError("MAC verification failed")
        
        return data
    
    def encrypt_to_file(self, file_path: str, data: bytes):
        """
        加密数据并存储到文件
        :param file_path: 文件路径
        :param data: 要加密的原始数据（如果密钥为空则直接存储原始数据）
        """
        encrypted_data = self.encrypt(data)
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
    
    def decrypt_from_file(self, file_path: str) -> bytes:
        """
        从文件读取并解密数据
        :param file_path: 文件路径
        :return: 解密后的原始数据（如果密钥为空则直接返回文件内容）
        """
        with open(file_path, 'rb') as f:
            data = f.read()
        
        return self.decrypt(data)


if __name__ == '__main__':
    # 使用示例
    password = "my_secret_password"  # 设置加密密码
    crypto = FileCrypto(password)  # 初始化加密器
    
    # 加密解密字符串示例
    original_text = "这是一段需要加密的敏感数据"
    print(f"原始数据: {original_text}")
    
    # 加密
    encrypted_data = crypto.encrypt(original_text.encode('utf-8'))
    print(f"加密后数据: {b64encode(encrypted_data).decode('utf-8')}")
    
    # 解密
    decrypted_data = crypto.decrypt(encrypted_data).decode('utf-8')
    print(f"解密后数据: {decrypted_data}")
    
    # 文件加密解密示例
    file_path = "encrypted_data.bin"
    print(f"\n文件加密示例 - 将数据加密保存到: {file_path}")
    
    # 加密数据到文件
    crypto.encrypt_to_file(file_path, original_text.encode('utf-8'))
    print("数据已加密保存到文件")
    
    # 从文件解密数据
    decrypted_from_file = crypto.decrypt_from_file(file_path).decode('utf-8')
    print(f"从文件解密的数据: {decrypted_from_file}")