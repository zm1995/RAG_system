太棒了！**Day 2 异步编程 + 全局异常处理** 你已经拿下了，现在进入 **Node 7 天闯关 Day 3：Stream（流）**。

这是 Node 面试中**区分中高级工程师**的核心知识点，也是**处理大文件、网络传输、数据转换**的利器。今天的目标是：**彻底吃透 Stream 的 4 种类型 + 背压机制 + 实战应用**。

---

## 📅 Day 3：Stream（流） · 终极实战手册

### 🎯 今日目标（3~4 小时）

* 掌握 **Stream 的 4 种类型**（Readable / Writable / Duplex / Transform）
* 理解 **背压（Backpressure）** 机制
* 能**手写**文件拷贝、大文件处理、数据转换
* 能**对比** `fs.readFile` vs `Stream` 的内存占用差异

---

## 第一部分：Stream 是什么？（30 分钟）

### 一句话粗暴定义

 > 
 > **Stream 是"数据流的管道"** —— 数据像水一样，一点一点地流过，而不是一次性全部倒进内存。

**类比**：

* **`fs.readFile`** = 把整桶水倒进浴缸，再处理 → **内存占用大**
* **Stream** = 接一根水管，边流边处理 → **内存占用小**

### 4 种 Stream 类型（面试必背）

|类型|作用|示例|
|--|--|--|
|**Readable（可读流）**|产生数据，供读取|`fs.createReadStream()`、`process.stdin`|
|**Writable（可写流）**|接收数据，写入目标|`fs.createWriteStream()`、`process.stdout`|
|**Duplex（双工流）**|既可读又可写（独立）|`net.Socket`（网络套接字）|
|**Transform（转换流）**|可读可写，且数据会被转换|`zlib.createGzip()`（压缩）、`crypto.createCipher`（加密）|

---

## 第二部分：基础实验（1 小时）

### 实验 1：Readable 流 —— 读取大文件

````javascript
const fs = require('fs');

// ❌ 错误方式：一次性读取（内存爆炸风险）
const data = fs.readFileSync('./bigfile.txt', 'utf8');  // 1GB 文件 → 内存占 1GB
console.log(data.length);

// ✅ 正确方式：流式读取
const readStream = fs.createReadStream('./bigfile.txt', {
  encoding: 'utf8',
  highWaterMark: 64 * 1024  // 每次读取 64KB（默认 16KB）
});

let chunkCount = 0;
readStream.on('data', (chunk) => {
  chunkCount++;
  console.log(`收到第 ${chunkCount} 块数据，大小: ${chunk.length} 字节`);
  // 模拟处理数据
});

readStream.on('end', () => {
  console.log('文件读取完成，总块数:', chunkCount);
});

readStream.on('error', (err) => {
  console.error('读取错误:', err);
});
````

**关键结论**：`highWaterMark` 控制每次读取的**缓冲区大小**，调大可以减少读取次数，但会增加内存占用。

---

### 实验 2：Writable 流 —— 写入大文件

````javascript
const fs = require('fs');

const writeStream = fs.createWriteStream('./output.txt', {
  encoding: 'utf8',
  highWaterMark: 64 * 1024  // 缓冲区大小 64KB
});

// 写入 10 万行数据
for (let i = 0; i < 100000; i++) {
  const canWrite = writeStream.write(`第 ${i} 行数据\n`);
  if (!canWrite) {
    console.log(`缓冲区满了，暂停写入（第 ${i} 行）`);
    break;  // 实际应用需要等待 drain 事件
  }
}

writeStream.end(() => {
  console.log('写入完成');
});

writeStream.on('drain', () => {
  console.log('缓冲区已清空，可以继续写入');
});

writeStream.on('error', (err) => {
  console.error('写入错误:', err);
});
````

**关键概念**：`write()` 返回 `false` 表示**缓冲区已满**，需要等待 `drain` 事件后再继续写入 —— 这就是**背压机制**。

---

### 实验 3：pipe —— 连接读写流（最常用）

````javascript
const fs = require('fs');

const readStream = fs.createReadStream('./source.txt');
const writeStream = fs.createWriteStream('./dest.txt');

// 方式1：手动监听 data 和 write（繁琐）
// readStream.on('data', (chunk) => writeStream.write(chunk));

// 方式2：pipe（自动处理背压，推荐）
readStream.pipe(writeStream);

// 监听完成
writeStream.on('finish', () => {
  console.log('文件复制完成');
});

// 监听错误
readStream.on('error', console.error);
writeStream.on('error', console.error);
````

**为什么 `pipe` 是首选？**

* 自动处理**背压**（数据生产速度 > 消费速度时自动暂停）
* 自动处理**错误传播**
* 代码简洁、可读性高

---

## 第三部分：背压机制（Backpressure）—— 面试必考（1 小时）

### 什么是背压？

 > 
 > **"当数据生产速度 > 消费速度时，消费者需要告诉生产者'慢一点'，这就是背压。"**

**现实类比**：

* 水龙头（生产者）出水太快
* 水桶（消费者）接不过来
* 水满了 → 溢出（数据丢失）
* **背压机制** = 水满了自动关小水龙头

### 背压在 Stream 中的实现

````javascript
const fs = require('fs');

const readStream = fs.createReadStream('./bigfile.txt', {
  highWaterMark: 16 * 1024  // 每次读 16KB
});

const writeStream = fs.createWriteStream('./output.txt', {
  highWaterMark: 16 * 1024  // 缓冲区 16KB
});

// 手动实现背压（pipe 内部就是这样做的）
readStream.on('data', (chunk) => {
  // 尝试写入
  const canWrite = writeStream.write(chunk);
  
  if (!canWrite) {
    // 缓冲区满了 → 暂停读取
    console.log('缓冲区满了，暂停读取');
    readStream.pause();
    
    // 等待 drain 事件 → 缓冲区空了 → 继续读取
    writeStream.once('drain', () => {
      console.log('缓冲区空了，恢复读取');
      readStream.resume();
    });
  }
});

readStream.on('end', () => {
  writeStream.end();
  console.log('复制完成');
});
````

**关键点**：

* `readStream.pause()` → 暂停触发 `data` 事件
* `writeStream.write()` 返回 `false` → 缓冲区满
* `writeStream.on('drain')` → 缓冲区清空，可继续写入
* `readStream.resume()` → 恢复读取

---

## 第四部分：Transform 流（1 小时）—— 面试加分项

### 场景：数据转换（加密 / 压缩 / 格式转换）

````javascript
const { Transform } = require('stream');
const fs = require('fs');

// 自定义 Transform 流：将文本转换为大写
const upperCaseTransform = new Transform({
  transform(chunk, encoding, callback) {
    // chunk 是 Buffer，需要转为字符串
    const upper = chunk.toString().toUpperCase();
    // 输出转换后的数据
    this.push(upper);
    callback();
  }
});

// 使用：读取文件 → 转大写 → 写入新文件
const readStream = fs.createReadStream('./input.txt');
const writeStream = fs.createWriteStream('./output.txt');

readStream
  .pipe(upperCaseTransform)
  .pipe(writeStream);

writeStream.on('finish', () => {
  console.log('转换完成');
});
````

### 实战：压缩 + 加密组合（真实场景）

````javascript
const fs = require('fs');
const zlib = require('zlib');
const crypto = require('crypto');

// 读取 → 加密 → 压缩 → 写入
const readStream = fs.createReadStream('./secret.txt');
const writeStream = fs.createWriteStream('./secret.txt.gz.enc');

// 加密流（使用 AES-256）
const cipher = crypto.createCipher('aes-256-cbc', 'my-password');

// 压缩流
const gzip = zlib.createGzip();

// 链式管道
readStream
  .pipe(cipher)    // 加密
  .pipe(gzip)      // 压缩
  .pipe(writeStream); // 写入

writeStream.on('finish', () => {
  console.log('加密压缩完成');
});
````

---

## 第五部分：实验 4 —— 对比内存占用（面试必秀）

````javascript
const fs = require('fs');

// 测试文件大小：100MB
const filePath = './test-100mb.txt';

console.log('========== 方式1：一次性读取 ==========');
console.time('fs.readFile');
const data = fs.readFileSync(filePath);
console.log('内存占用:', (process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2), 'MB');
console.timeEnd('fs.readFile');

console.log('\n========== 方式2：流式读取 ==========');
console.time('stream');
const readStream = fs.createReadStream(filePath, { highWaterMark: 64 * 1024 });
let size = 0;
readStream.on('data', (chunk) => {
  size += chunk.length;
});
readStream.on('end', () => {
  console.log('读取总大小:', (size / 1024 / 1024).toFixed(2), 'MB');
  console.log('内存占用:', (process.memoryUsage().heapUsed / 1024 / 1024).toFixed(2), 'MB');
  console.timeEnd('stream');
});
````

**预期结果**：

* `fs.readFileSync`：内存占用 ≈ 100MB（整个文件）
* `Stream`：内存占用 ≈ 几 MB（只有当前 chunk）

**面试金句**：**"对于大文件处理，Stream 的内存占用是 O(1)，而 readFile 是 O(n)。"**

---

## 第六部分：今日验收清单

* [ ] 能**说出** 4 种 Stream 类型（Readable / Writable / Duplex / Transform）
* [ ] 能**解释**背压机制（生产速度 > 消费速度时的处理）
* [ ] 能**手写**文件拷贝（使用 `pipe`）
* [ ] 能**手写**自定义 Transform 流（数据转换）
* [ ] 能**对比** `fs.readFile` 和 Stream 的内存占用差异
* [ ] 能**手写**手动背压控制（`pause` + `drain`）

---

## 📝 今日核心速查表

|知识点|关键代码|记忆口诀|
|---|----|----|
|Readable 流|`createReadStream().on('data', chunk => {})`|生产数据|
|Writable 流|`createWriteStream().write(chunk)`|消费数据|
|Pipe|`readStream.pipe(writeStream)`|自动连接|
|背压|`writeStream.write()` 返回 `false` → `pause()` → `drain` → `resume()`|慢下来|
|Transform|`new Transform({ transform(chunk, enc, cb) {} })`|边读边改|

---

## 🚀 Day 3 完成后你的进度

* ✅ 事件循环（Day 1）
* ✅ 异步编程 + 全局异常（Day 2）
* ✅ Stream（Readable / Writable / Transform + 背压）
* ✅ 大文件处理（内存占用对比）

**明天 Day 4：Buffer 与二进制** —— 处理网络协议、图片、文件格式的核心。

---

现在，**打开终端，从实验 1 开始跑**。如果你手边没有大文件，可以用以下命令生成一个测试文件：

````bash
# 生成 100MB 测试文件（Mac/Linux）
dd if=/dev/zero of=./test-100mb.txt bs=1M count=100
````

跑完实验 3（文件拷贝），告诉我你的 `highWaterMark` 设置和内存占用情况，我帮你优化参数！😎
