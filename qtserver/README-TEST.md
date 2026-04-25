# MQTT客户端测试

这个目录包含MQTT服务器和客户端测试工具。

## 文件说明

- `mqtt-server.js` - MQTT服务器实现，支持TCP和WebSocket连接
- `mqtt-client-test.js` - MQTT客户端测试工具
- `package.json` - 项目依赖配置

## 使用方法

### 1. 启动MQTT服务器

```bash
# 安装依赖（如果尚未安装）
npm install

# 启动MQTT服务器
npm start
```

### 2. 运行客户端测试

```bash
# 运行完整的MQTT客户端测试
node mqtt-client-test.js
```

### 3. 单独测试特定功能

```javascript
const MQTTClientTest = require('./mqtt-client-test');

// 创建测试客户端
const testClient = new MQTTClientTest({
    host: 'localhost',    // MQTT服务器地址
    port: 1883,           // MQTT端口
    wsPort: 8083,         // WebSocket端口
    clientId: 'my_test_client'
});

// 只测试MQTT连接
await testClient.testMQTTConnection();

// 只测试MQTT消息收发
await testClient.testMQTTMessaging();

// 只测试WebSocket MQTT
await testClient.testWebSocketMQTT();

// 运行所有测试
await testClient.runAllTests();
```

## 测试内容

测试工具会验证以下功能：

1. **MQTT连接测试**
   - 建立TCP连接
   - 连接状态验证

2. **MQTT消息测试**
   - 主题订阅
   - 消息发布
   - 消息接收
   - 取消订阅

3. **WebSocket MQTT测试**
   - WebSocket连接
   - WebSocket消息收发

## 测试结果

测试完成后会显示详细的测试结果：
- 总测试数
- 通过/失败的测试数
- 每个测试的详细状态

## 注意事项

1. 运行测试前请确保MQTT服务器已启动
2. 默认使用localhost和默认端口（1883/8083）
3. 测试会自动清理连接资源
4. 如果测试失败，会显示详细的错误信息

## 故障排除

如果测试失败，请检查：

1. MQTT服务器是否正常运行
2. 端口是否被占用
3. 防火墙设置是否允许连接
4. 依赖包是否正确安装

## 自定义配置

可以通过构造函数参数自定义测试配置：

```javascript
const testClient = new MQTTClientTest({
    host: '192.168.1.100',  // 自定义服务器地址
    port: 8883,             // 自定义MQTT端口
    wsPort: 8884,           // 自定义WebSocket端口
    clientId: 'custom_client_id'
});
```