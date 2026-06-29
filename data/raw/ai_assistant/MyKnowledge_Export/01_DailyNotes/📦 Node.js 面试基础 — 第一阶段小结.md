好。今天我们做一个**阶段性小结**，然后进入下一个基础问题。

---

## 📦 Node.js 面试基础 — 第一阶段小结

你已经覆盖了以下核心知识点：

|序号|主题|掌握情况|
|--|--|----|
|1|事件循环 + 异步非阻塞I/O|✅ 已掌握核心原理|
|2|require vs import + 循环引用|✅ 已掌握区别与处理方式|
|3|手写 EventEmitter（on/emit/off/once）|✅ 已掌握实现与追问|
|4|滑动窗口限流器设计|✅ 已掌握算法与分布式思路|
|5|HTTP 模块：req / res 核心属性和方法|✅ 已掌握原生解析body的方式|
|6|模块系统与循环依赖的处理|✅ 已补充|

**你现在已经具备了回答以下类型面试题的能力：**

* “Node.js 单线程怎么应对高并发？”

* “require 和 import 有什么区别？”

* “手写一个 EventEmitter”

* “怎么设计一个限流器？”

* “req.body 为什么是 undefined？怎么拿到？”

这些是Node.js面试中**出现频率最高**的基础题，你已经全部过了一遍。

---

## 🚀 下一个基础问题

现在进入**流（Stream）** 模块——这是Node.js高级开发必考、但很多人讲不清楚的知识点。

### 今日问题 #004

 > 
 > **“Node.js 的 Stream 是什么？它和直接操作 Buffer 相比有什么优势？Readable 和 Writable Stream 分别怎么用？”**

**你可以先用自己的话回答这三个小问题：**

1. Stream 是什么？（一句话）

1. 它比直接读/写文件好在哪里？

1. Readable 和 Writable 的区别是什么？

不用写代码，说思路就行。像之前一样，你说你的理解，我来帮你打磨成“面试官想听的版本”。想好了直接发过来就行。🎯

---

title: Node.js 面试第一阶段小结  
date: 2026-06-17  
tags: \[Node.js, 面试, 小结\]  
category: Nodejs面试题

---

## 已覆盖知识点清单

* 事件循环 + 异步非阻塞I/O

* require vs import + 循环引用

* 手写 EventEmitter（含 once 实现）

* 滑动窗口限流器设计（含分布式方案）

* HTTP 模块 req/res 核心属性和方法

* 模块系统与循环依赖处理

## 下一阶段：流（Stream）

* Stream 基本概念与优势

* Readable / Writable / Duplex / Transform

* pipe 方法原理

* 背压（Backpressure）机制

* 自定义 Stream 实现

---

**当前状态：** 基础模块已夯实，准备进入 Stream。  
**目标：** 逐步覆盖所有中级面试题。
