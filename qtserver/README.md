# QtServer MQTT 服务器

这是一个基于Node.js的MQTT服务器，支持标准的MQTT协议和WebSocket连接。

## 功能特性

- ✅ 支持MQTT 3.1.1协议
- ✅ 支持WebSocket连接（浏览器客户端）
- ✅ 主题订阅和发布
- ✅ 消息持久化存储
- ✅ 心跳检测
- ✅ 多客户端支持

## 快速开始

### 1. 安装依赖

```bash
cd qtserver
npm install
```

### 2. 启动服务器

```bash
# 方式1: 使用npm脚本
npm start

# 方式2: 直接运行
node mqtt-server.js

# 方式3: 使用批处理文件（Windows）
start.bat
```

### 3. 配置环境变量（可选）

```bash
# MQTT端口（默认1883）
export MQTT_PORT=1883

# WebSocket端口（默认8083）
export WS_PORT=8083
```

## 端口说明

- **MQTT端口**: 1883 - 标准MQTT协议端口
- **WebSocket端口**: 8083 - 浏览器客户端连接端口

## 客户端连接示例

### MQTT客户端连接

```javascript
const mqtt = require('mqtt');

// 连接到MQTT服务器
const client = mqtt.connect('mqtt://localhost:1883');

client.on('connect', () => {
    console.log('连接成功');
    
    // 订阅主题
    client.subscribe('test/topic');
    
    // 发布消息
    client.publish('test/topic', 'Hello MQTT!');
});

client.on('message', (topic, message) => {
    console.log(`收到消息: ${topic} - ${message.toString()}`);
});
```

### WebSocket客户端连接

```javascript
// 浏览器端JavaScript
const ws = new WebSocket('ws://localhost:8083');

ws.onopen = () => {
    console.log('WebSocket连接成功');
    
    // 订阅主题
    ws.send(JSON.stringify({
        type: 'subscribe',
        topic: 'test/topic'
    }));
    
    // 发布消息
    ws.send(JSON.stringify({
        type: 'publish',
        topic: 'test/topic',
        payload: 'Hello from WebSocket!'
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'message') {
        console.log(`收到消息: ${data.topic} - ${data.payload}`);
    }
};
```

## API说明

### WebSocket消息格式

#### 订阅主题
```json
{
    "type": "subscribe",
    "topic": "your/topic"
}
```

#### 取消订阅
```json
{
    "type": "unsubscribe", 
    "topic": "your/topic"
}
```

#### 发布消息
```json
{
    "type": "publish",
    "topic": "your/topic",
    "payload": "your message"
}
```

#### 心跳
```json
{
    "type": "ping"
}
```

## 服务器管理

服务器启动后，可以通过以下方式管理：

- **Ctrl+C**: 优雅关闭服务器
- **SIGINT/SIGTERM**: 进程信号关闭

## 故障排除

### 端口被占用
如果端口被占用，可以修改环境变量或直接修改代码中的端口号。

### 依赖安装失败
确保Node.js版本 >= 12.0.0，并尝试清除缓存：
```bash
npm cache clean --force
```

## 许可证

MIT License