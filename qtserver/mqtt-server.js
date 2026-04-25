const aedes = require('aedes');
const WebSocket = require('ws');
const net = require('net');

class MQTTServer {
    constructor(options = {}) {
        this.port = options.port || 1883;
        this.wsPort = options.wsPort || 8083;
        this.clients = new Map();
        this.topics = new Map();
        
        // 创建MQTT服务器
        this.createMQTTServer();
        
        // 创建WebSocket服务器（用于浏览器客户端）
        this.createWebSocketServer();
        
        console.log(`MQTT服务器启动成功:`);
        console.log(`- MQTT端口: ${this.port}`);
        console.log(`- WebSocket端口: ${this.wsPort}`);
    }
    
    createMQTTServer() {
        // 使用aedes库创建MQTT服务器
        this.aedes = aedes();
        
        // 创建TCP服务器
        this.server = net.createServer(this.aedes.handle);
        
        // 监听客户端连接事件
        this.aedes.on('client', (client) => {
            console.log(`客户端连接: ${client.id}`);
            this.clients.set(client.id, client);
        });
        
        // 监听客户端断开事件
        this.aedes.on('clientDisconnect', (client) => {
            console.log(`客户端断开连接: ${client.id}`);
            this.clients.delete(client.id);
        });
        
        // 监听发布消息事件
        this.aedes.on('publish', (packet, client) => {
            if (client) {
                console.log(`收到消息: ${packet.topic} - ${packet.payload.toString()}`);
                
                // 存储消息到对应主题
                if (!this.topics.has(packet.topic)) {
                    this.topics.set(packet.topic, []);
                }
                this.topics.get(packet.topic).push({
                    payload: packet.payload.toString(),
                    timestamp: new Date().toISOString(),
                    clientId: client.id
                });
                
                // 广播消息给所有订阅该主题的客户端
                this.broadcastMessage(packet.topic, packet.payload.toString(), client.id);
            }
        });
        
        // 监听订阅事件
        this.aedes.on('subscribe', (subscriptions, client) => {
            if (client) {
                const topics = subscriptions.map(sub => sub.topic);
                console.log(`客户端 ${client.id} 订阅主题: ${topics.join(', ')}`);
                
                topics.forEach(topic => {
                    if (!this.topics.has(topic)) {
                        this.topics.set(topic, []);
                    }
                });
            }
        });
        
        // 监听取消订阅事件
        this.aedes.on('unsubscribe', (unsubscriptions, client) => {
            if (client) {
                console.log(`客户端 ${client.id} 取消订阅: ${unsubscriptions.join(', ')}`);
            }
        });
        
        // 监听错误事件
        this.aedes.on('clientError', (client, error) => {
            console.error(`客户端 ${client.id} 错误:`, error);
        });
        
        this.server.listen(this.port, () => {
            console.log(`MQTT服务器监听端口 ${this.port}`);
        });
    }
    
    createWebSocketServer() {
        this.wsServer = new WebSocket.Server({ port: this.wsPort });
        
        this.wsServer.on('connection', (ws, req) => {
            const clientId = `ws_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
            console.log(`WebSocket客户端连接: ${clientId}`);
            
            ws.clientId = clientId;
            ws.subscriptions = new Set();
            
            // 发送连接成功消息
            ws.send(JSON.stringify({
                type: 'connected',
                clientId: clientId
            }));
            
            ws.on('message', (message) => {
                try {
                    const data = JSON.parse(message);
                    this.handleWebSocketMessage(ws, data);
                } catch (error) {
                    console.error('解析WebSocket消息错误:', error);
                    ws.send(JSON.stringify({
                        type: 'error',
                        message: '消息格式错误'
                    }));
                }
            });
            
            ws.on('close', () => {
                console.log(`WebSocket客户端断开连接: ${clientId}`);
                // 清理订阅
                ws.subscriptions.clear();
            });
            
            ws.on('error', (error) => {
                console.error(`WebSocket客户端 ${clientId} 错误:`, error);
            });
        });
        
        console.log(`WebSocket MQTT服务器监听端口 ${this.wsPort}`);
    }
    
    handleWebSocketMessage(ws, data) {
        switch (data.type) {
            case 'subscribe':
                if (data.topic) {
                    ws.subscriptions.add(data.topic);
                    console.log(`WebSocket客户端 ${ws.clientId} 订阅主题: ${data.topic}`);
                    
                    // 发送订阅确认
                    ws.send(JSON.stringify({
                        type: 'suback',
                        topic: data.topic,
                        success: true
                    }));
                    
                    // 发送该主题的历史消息
                    if (this.topics.has(data.topic)) {
                        const messages = this.topics.get(data.topic);
                        messages.forEach(msg => {
                            ws.send(JSON.stringify({
                                type: 'message',
                                topic: data.topic,
                                payload: msg.payload,
                                timestamp: msg.timestamp,
                                clientId: msg.clientId
                            }));
                        });
                    }
                }
                break;
                
            case 'unsubscribe':
                if (data.topic && ws.subscriptions.has(data.topic)) {
                    ws.subscriptions.delete(data.topic);
                    console.log(`WebSocket客户端 ${ws.clientId} 取消订阅: ${data.topic}`);
                    
                    ws.send(JSON.stringify({
                        type: 'unsuback',
                        topic: data.topic,
                        success: true
                    }));
                }
                break;
                
            case 'publish':
                if (data.topic && data.payload) {
                    console.log(`WebSocket客户端 ${ws.clientId} 发布消息: ${data.topic} - ${data.payload}`);
                    
                    // 存储消息
                    if (!this.topics.has(data.topic)) {
                        this.topics.set(data.topic, []);
                    }
                    this.topics.get(data.topic).push({
                        payload: data.payload,
                        timestamp: new Date().toISOString(),
                        clientId: ws.clientId
                    });
                    
                    // 广播消息
                    this.broadcastMessage(data.topic, data.payload, ws.clientId);
                    
                    ws.send(JSON.stringify({
                        type: 'puback',
                        topic: data.topic,
                        success: true
                    }));
                }
                break;
                
            case 'ping':
                ws.send(JSON.stringify({
                    type: 'pong'
                }));
                break;
                
            default:
                console.warn(`未知的消息类型: ${data.type}`);
        }
    }
    
    broadcastMessage(topic, payload, fromClientId) {
        // 使用aedes的publish方法广播消息给所有订阅该主题的MQTT客户端
        this.aedes.publish({
            topic: topic,
            payload: payload,
            qos: 0
        }, (error) => {
            if (error) {
                console.error(`广播MQTT消息失败:`, error);
            }
        });
        
        // 广播给所有WebSocket客户端
        this.wsServer.clients.forEach(client => {
            if (client.readyState === WebSocket.OPEN && 
                client.subscriptions.has(topic) && 
                client.clientId !== fromClientId) {
                
                client.send(JSON.stringify({
                    type: 'message',
                    topic: topic,
                    payload: payload,
                    timestamp: new Date().toISOString(),
                    clientId: fromClientId
                }));
            }
        });
    }
    
    // 获取服务器状态
    getStatus() {
        return {
            mqttClients: this.clients.size,
            wsClients: this.wsServer.clients.size,
            topics: Array.from(this.topics.keys()),
            totalMessages: Array.from(this.topics.values()).reduce((sum, messages) => sum + messages.length, 0)
        };
    }
    
    // 关闭服务器
    close() {
        this.server.close();
        this.aedes.close();
        this.wsServer.close();
        console.log('MQTT服务器已关闭');
    }
}

// 创建服务器实例
const mqttServer = new MQTTServer({
    port: process.env.MQTT_PORT || 1883,
    wsPort: process.env.WS_PORT || 8083
});

// 处理进程退出
process.on('SIGINT', () => {
    console.log('收到SIGINT信号，正在关闭服务器...');
    mqttServer.close();
    process.exit(0);
});

process.on('SIGTERM', () => {
    console.log('收到SIGTERM信号，正在关闭服务器...');
    mqttServer.close();
    process.exit(0);
});

module.exports = MQTTServer;