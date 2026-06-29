# 📅 Day 4：Buffer 与二进制 —— 终极实战手册

## 🎯 今日目标（3～4 小时）

* 彻底搞懂 **Buffer 是什么、为什么存在、怎么用**
* 掌握 **Buffer 的创建、读写、编码转换、合并与切片**
* 理解 **Node.js 中二进制数据处理的典型场景**：文件上传、图片处理、网络协议解析、加密/解密
* 能够**手写**一个简单的 **二进制协议解析器**（模拟网络通信）

---

## 第一部分：Buffer 是什么？（30 分钟）

### 一句话粗暴定义

 > 
 > **Buffer 是 Node.js 中用于处理二进制数据的类数组对象，它直接分配在 V8 堆内存之外（由 C++ 层面管理），用于高效处理原始字节流。**

### 为什么需要 Buffer？

|场景|不用 Buffer 会怎样|用 Buffer 的优势|
|--|-------------|------------|
|文件读写|字符串无法处理图片/视频/压缩包|Buffer 可以表示任意二进制数据|
|网络通信|TCP/WebSocket 传输的是字节流|Buffer 是底层传输的标准单元|
|加密/解密|加密算法操作的是字节|Buffer 天然支持位运算和字节操作|
|性能|字符串转二进制需要额外编码开销|Buffer 直接操作内存，零拷贝|

### Buffer vs ArrayBuffer vs Uint8Array（面试必问）

|概念|所属环境|特点|
|--|----|--|
|**Buffer**|Node.js|继承自 `Uint8Array`，支持更多 Node 特有方法（如 `alloc`、`from`、`concat`）|
|**ArrayBuffer**|浏览器/ES6|原始二进制数据缓冲区，不能直接读写，需通过 TypedArray 操作|
|**Uint8Array**|浏览器/ES6|是 ArrayBuffer 的"视图"，可以用索引读写 8 位无符号整数|
|**关系**|`Buffer` 是 `Uint8Array` 的子类，因此 Buffer 可以使用所有 TypedArray 方法||

**面试金句**：*"Buffer 是 Node.js 对 Uint8Array 的扩展，它解决了 Node 环境中处理二进制数据（文件、网络、加密）的性能和便利性问题。"*

---

## 第二部分：Buffer 的创建与初始化（30 分钟）

### 1. 创建 Buffer 的 3 种方式（面试必考）

````javascript
// 方式 1：alloc —— 推荐（安全，初始化为 0）
const buf1 = Buffer.alloc(10);        // 10 字节，全为 0
const buf2 = Buffer.alloc(10, 0x1);   // 10 字节，全为 0x01
console.log(buf1);  // <Buffer 00 00 00 ...>

// 方式 2：from —— 从已有数据创建
const buf3 = Buffer.from('hello');     // 从字符串创建（UTF-8）
const buf4 = Buffer.from([0x68, 0x65, 0x6c, 0x6c, 0x6f]); // 从数组创建
const buf5 = Buffer.from(buf3);        // 从 Buffer 拷贝（浅拷贝，但数据独立）

// 方式 3：allocUnsafe —— 不推荐（速度快但可能包含敏感数据）
const buf6 = Buffer.allocUnsafe(10);   // 可能包含旧数据（未清零）
// 注意：必须立即用 fill() 覆盖，否则可能泄露敏感信息
buf6.fill(0);  // 手动清零
````

### 2. alloc vs allocUnsafe 的区别（面试加分项）

|方法|速度|安全性|使用场景|
|--|--|---|----|
|`Buffer.alloc(size)`|慢（需要初始化）|安全（全部置 0）|绝大多数场景|
|`Buffer.allocUnsafe(size)`|快（不初始化）|不安全（可能含有旧数据）|需要极致性能且立即填充的场合|

**面试金句**：*"`allocUnsafe` 之所以快，是因为它直接分配内存但不做清零操作，但如果分配后立即用 `fill()` 覆盖，则完全安全且性能更高。"*

---

## 第三部分：Buffer 的读写操作（30 分钟）

### 1. 基本读写

````javascript
const buf = Buffer.alloc(10);

// 写入
buf.write('hello', 0, 'utf8');  // 从偏移 0 写入 'hello'
buf[5] = 0x21;                   // 直接赋值（ASCII '!'）
buf.writeUInt16BE(0x1234, 6);    // 大端序写入 2 字节（内存地址：12 34）

console.log(buf);
// <Buffer 68 65 6c 6c 6f 21 12 34 00 00>

// 读取
console.log(buf.toString('utf8', 0, 5));   // 'hello'
console.log(buf[5]);                        // 33（'!' 的 ASCII 码）
console.log(buf.readUInt16BE(6));           // 0x1234
console.log(buf.readUInt16LE(6));           // 0x3412（小端序）
````

### 2. 常用读写方法速查表

|方法|说明|示例|
|--|--|--|
|`writeUInt8(value, offset)`|写入 1 字节|`buf.writeUInt8(0xFF, 0)`|
|`writeUInt16BE(value, offset)`|写入 2 字节（大端序）|`buf.writeUInt16BE(0x1234, 0)`|
|`writeUInt16LE(value, offset)`|写入 2 字节（小端序）|`buf.writeUInt16LE(0x1234, 0)`|
|`writeUInt32BE(value, offset)`|写入 4 字节（大端序）|`buf.writeUInt32BE(0x12345678, 0)`|
|`readUInt8(offset)`|读取 1 字节|`buf.readUInt8(0)`|
|`readUInt16BE(offset)`|读取 2 字节（大端序）|`buf.readUInt16BE(0)`|
|`readUInt16LE(offset)`|读取 2 字节（小端序）|`buf.readUInt16LE(0)`|
|`toString(encoding, start, end)`|转字符串|`buf.toString('hex', 0, 4)`|

---

## 第四部分：编码与转换（30 分钟）

### 1. 常见编码对比

|编码|说明|示例|
|--|--|--|
|`utf8`|变长编码，1～4 字节/字符|`'中'` → `E4 B8 AD`（3 字节）|
|`ascii`|7 位 ASCII，1 字节/字符|`'A'` → `41`|
|`hex`|十六进制字符串表示|`Buffer.from('hello').toString('hex')` → `'68656c6c6f'`|
|`base64`|用于网络传输，将二进制转 ASCII|`Buffer.from('hello').toString('base64')` → `'aGVsbG8='`|
|`utf16le`|UTF-16 小端序|`'中'` → `2D 4E`（2 字节）|

### 2. 编码转换实战

````javascript
// 从字符串到 Buffer
const buf = Buffer.from('Hello 世界', 'utf8');
console.log(buf);            // <Buffer 48 65 6c 6c 6f 20 e4 b8 96 e7 95 8c>
console.log(buf.length);     // 12（'Hello ' 6 字节 + '世界' 6 字节）

// 从 Buffer 到字符串
console.log(buf.toString('utf8'));      // 'Hello 世界'
console.log(buf.toString('hex'));       // '48656c6c6f20e4b896e7958c'
console.log(buf.toString('base64'));    // 'SGVsbG8g5LiW55WM'

// 编码转换（常见坑）
const euro = Buffer.from([0xE2, 0x82, 0xAC]);  // UTF-8 编码的 €
console.log(euro.toString('utf8'));    // '€'
console.log(euro.toString('ascii'));   // 'â\x82¬'（乱码！）
````

**面试金句**：*"不同编码之间转换务必明确指定编码，否则 Node 默认使用 `utf8`，可能导致乱码。"*

---

## 第五部分：实验 1 —— 图片处理（30 分钟）

### 场景：读取图片，提取宽高信息，裁剪或转换格式

````javascript
const fs = require('fs');
const path = require('path');

// 读取图片文件（假设是 PNG）
const imageBuffer = fs.readFileSync('./test.png');

// PNG 文件头固定为 8 字节：89 50 4E 47 0D 0A 1A 0A
const pngHeader = imageBuffer.subarray(0, 8);
if (pngHeader.toString('hex') !== '89504e470d0a1a0a') {
  console.error('不是有效的 PNG 图片');
  return;
}

// 读取图片宽高（PNG 中宽高在 IHDR 块中，偏移 16～23）
const width = imageBuffer.readUInt32BE(16);
const height = imageBuffer.readUInt32BE(20);
console.log(`图片尺寸: ${width} x ${height}`);

// 转换为 Base64（用于前端展示或 API 返回）
const base64Image = imageBuffer.toString('base64');
console.log(`Base64 长度: ${base64Image.length}`);

// 裁剪图片（模拟：只保留前 1000 字节）
const croppedBuffer = imageBuffer.subarray(0, 1000);
fs.writeFileSync('./cropped.png', croppedBuffer);
console.log('裁剪完成（文件已损坏，仅演示）');
````

---

## 第六部分：实验 2 —— 手写二进制协议解析器（面试必杀技，30 分钟）

### 场景：模拟客户端/服务器通信协议

**协议定义**（自定义二进制协议）：

* `1 字节`：版本号（固定 `0x01`）
* `2 字节`：包体长度（大端序）
* `N 字节`：包体（JSON 字符串或二进制数据）

````javascript
const { EventEmitter } = require('events');

class BinaryProtocol extends EventEmitter {
  constructor() {
    super();
    this.buffer = Buffer.alloc(0);  // 累积缓冲区
    this.state = 'HEADER';          // 状态机：HEADER → BODY
    this.bodyLength = 0;
  }

  // 接收数据（通常来自网络 socket）
  feed(data) {
    this.buffer = Buffer.concat([this.buffer, data]);

    while (this.buffer.length > 0) {
      if (this.state === 'HEADER') {
        // 至少需要 3 字节才能解析头部（版本号 1 + 长度 2）
        if (this.buffer.length < 3) break;

        const version = this.buffer.readUInt8(0);
        if (version !== 0x01) {
          throw new Error(`不支持的协议版本: ${version}`);
        }

        this.bodyLength = this.buffer.readUInt16BE(1);
        this.state = 'BODY';

        // 移除已解析的头部
        this.buffer = this.buffer.subarray(3);
        continue;
      }

      if (this.state === 'BODY') {
        // 检查是否收完整包体
        if (this.buffer.length < this.bodyLength) break;

        // 提取包体
        const bodyBuffer = this.buffer.subarray(0, this.bodyLength);
        const body = bodyBuffer.toString('utf8');

        // 触发消息事件
        this.emit('message', {
          version: 0x01,
          body: JSON.parse(body),  // 假设包体是 JSON
          raw: bodyBuffer
        });

        // 移除已解析的包体
        this.buffer = this.buffer.subarray(this.bodyLength);
        this.state = 'HEADER';
        this.bodyLength = 0;
      }
    }
  }
}

// 测试
const protocol = new BinaryProtocol();

protocol.on('message', (msg) => {
  console.log('收到消息:', msg.body);
});

// 模拟发送：构造一个符合协议的数据包
const body = JSON.stringify({ action: 'ping', timestamp: Date.now() });
const bodyBuffer = Buffer.from(body, 'utf8');
const packet = Buffer.alloc(3 + bodyBuffer.length);
packet.writeUInt8(0x01, 0);          // 版本号
packet.writeUInt16BE(bodyBuffer.length, 1);  // 包体长度
bodyBuffer.copy(packet, 3);          // 复制包体

// 模拟网络传输（可能分片）
protocol.feed(packet.subarray(0, 2));   // 先发 2 字节（不完整）
protocol.feed(packet.subarray(2));      // 再发剩余部分
// 输出: 收到消息: { action: 'ping', timestamp: 1734567890123 }
````

---

## 第七部分：实验 3 —— Buffer + Stream 组合（大文件处理，30 分钟）

### 场景：计算大文件的 MD5 哈希（流式处理，不占内存）

````javascript
const fs = require('fs');
const crypto = require('crypto');

function computeFileHash(filePath, algorithm = 'md5') {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash(algorithm);
    const stream = fs.createReadStream(filePath);

    stream.on('data', (chunk) => {
      hash.update(chunk);  // 直接处理 Buffer
    });

    stream.on('end', () => {
      resolve(hash.digest('hex'));
    });

    stream.on('error', reject);
  });
}

// 测试
computeFileHash('./largefile.bin', 'sha256')
  .then(hash => console.log('SHA-256:', hash))
  .catch(console.error);
````

---

## 第八部分：今日验收清单

* [ ] 能**说出** Buffer 是什么，以及它和 ArrayBuffer / Uint8Array 的关系
* [ ] 能**写出** 3 种创建 Buffer 的方式（`alloc` / `from` / `allocUnsafe`）
* [ ] 能**写出** Buffer 的读写操作（`writeUInt16BE` / `readUInt16BE` / `toString`）
* [ ] 能**解释**大端序和小端序的区别
* [ ] 能**手写**一个简单的二进制协议解析器（状态机 + Buffer 切片）
* [ ] 能**解释** `Buffer` 和 `Stream` 如何配合处理大文件

---

## 📝 今日核心速查表

|知识点|关键代码|记忆口诀|
|---|----|----|
|创建 Buffer|`Buffer.alloc(size)` / `Buffer.from(data)`|alloc 安全，from 转换|
|写入数值|`buf.writeUInt16BE(value, offset)`|BE 大端，LE 小端|
|转字符串|`buf.toString('hex')`|二进制用 hex，文本用 utf8|
|合并 Buffer|`Buffer.concat([buf1, buf2])`|拼合数据流|
|切片|`buf.subarray(start, end)`|不复制，共享内存|
|协议解析|状态机 + Buffer 累积|读完就切走|

---

## 🚀 今日完成后你的进度

* ✅ 事件循环（Day 1）
* ✅ 异步编程 + 全局异常（Day 2）
* ✅ Stream（Day 3）
* ✅ Buffer 与二进制（Day 4） ← 你在这里

**明天 Day 5：进程管理（Cluster / child_process）** —— 多核利用、进程通信、守护进程

---

现在，**从第一部分开始跑代码**，把每个实验都跑通。如果哪个实验的结果和预期不一样，**截图发我**，我帮你分析！

你开始了吗？😎
