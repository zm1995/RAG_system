## 面试题

 > 
 > 不使用 `events` 模块，手写极简版 EventEmitter，包含 `on`、`emit`、`off`。

---

## 核心答案

````
class EventEmitter {
  constructor() {
    // 核心数据结构：一个对象，key 是事件名，value 是回调函数数组
    this.events = {};
  }

  // on：订阅/监听事件
  on(eventName, callback) {
    // 如果该事件还没有对应的队列，初始化一个空数组
    if (!this.events[eventName]) {
      this.events[eventName] = [];
    }
    // 将回调函数放入队列
    this.events[eventName].push(callback);
  }

  // emit：触发事件
  emit(eventName, ...args) {
    const callbacks = this.events[eventName];
    if (!callbacks) return; // 没有监听，直接返回
    // 依次执行所有回调，并传入参数
    callbacks.forEach(cb => cb(...args));
  }

  // off：注销事件监听
  off(eventName, callback) {
    const callbacks = this.events[eventName];
    if (!callbacks) return;
    // 过滤掉要移除的那个回调函数
    this.events[eventName] = callbacks.filter(cb => cb !== callback);
  }
}
````

## 关键点（面试时边写边说）

1. `this.events = {}` 作为核心存储
1. `on` 方法往数组里 push 回调
1. `emit` 方法遍历数组执行回调，用 `...args` 透传参数
1. `off` 方法用 `filter` 移除指定的回调（注意函数引用相等性）

---

## 追问及答案

* **`once` 如何实现？** → 包装函数执行后自动 `off`
* **`off` 传入不存在的回调怎么办？** → `filter` 不动，安全静默
* **重复绑定重复移除？** → 所有匹配的都会移除，面试版本足够清晰

---

## 一句总结（面试开场金句）

 > 
 > "EventEmitter 的核心就是发布-订阅模式：on 登记，emit 通知，off 注销。底层就是一个对象 + 数组的映射结构。"

好，我把**完整版手写 EventEmitter（含 once 实现）** 的代码贴出来，附带**面试时边写边说的注释**，方便你直接存入 Obsidian。

---

## 📝 完整代码（面试官满意的版本）

````javascript
class EventEmitter {
  constructor() {
    // 核心存储：{ eventName: [callback1, callback2, ...] }
    this.events = {};
  }

  /**
   * 订阅事件
   * @param {string} eventName - 事件名
   * @param {Function} callback - 回调函数
   */
  on(eventName, callback) {
    if (!this.events[eventName]) {
      this.events[eventName] = [];
    }
    this.events[eventName].push(callback);
  }

  /**
   * 触发事件
   * @param {string} eventName - 事件名
   * @param {...any} args - 传给回调的参数
   */
  emit(eventName, ...args) {
    const callbacks = this.events[eventName];
    if (!callbacks || callbacks.length === 0) return;
    // 遍历执行所有回调（浅拷贝一份，防止回调中修改数组）
    [...callbacks].forEach(cb => cb(...args));
  }

  /**
   * 移除事件监听
   * @param {string} eventName - 事件名
   * @param {Function} callback - 要移除的回调（必须是同一个引用）
   */
  off(eventName, callback) {
    const callbacks = this.events[eventName];
    if (!callbacks) return;
    this.events[eventName] = callbacks.filter(cb => cb !== callback);
  }

  /**
   * 只监听一次
   * @param {string} eventName - 事件名
   * @param {Function} callback - 回调函数
   */
  once(eventName, callback) {
    // 包装函数：执行一次后自动 off
    const wrapper = (...args) => {
      callback(...args);
      this.off(eventName, wrapper);
    };
    this.on(eventName, wrapper);
  }
}
````

---

## 🧪 测试用例（面试时可以口头演示）

````javascript
const emitter = new EventEmitter();

// 测试 on / emit
emitter.on('greet', (name) => console.log(`Hello, ${name}!`));
emitter.emit('greet', 'Alice'); // 输出: Hello, Alice!

// 测试 once
emitter.once('onceTest', () => console.log('只执行一次'));
emitter.emit('onceTest'); // 输出: 只执行一次
emitter.emit('onceTest'); // 无输出（已被移除）

// 测试 off
const fn = () => console.log('移除我');
emitter.on('test', fn);
emitter.off('test', fn);
emitter.emit('test'); // 无输出（已被移除）
````

---

## 🎯 面试官追问及回答

|追问|回答|
|--|--|
|**once 为什么要用 wrapper？**|因为需要把“执行回调 + 自动移除”打包成一个函数，传给 on。如果不包装，就无法在触发后自动移除自己。|
|**emit 里为什么要 `[...callbacks]` 浅拷贝？**|防止回调函数中调用了 `off` 移除自身，导致数组在遍历过程中被修改。浅拷贝保证遍历的是快照，不影响当前循环。|
|**off 时找不到 callback 怎么办？**|用 `filter` 过滤，如果找不到，数组不变，不会报错。这是安全设计。|
|**怎么支持 `once` 的多个独立调用？**|每个 `once` 都会创建一个新的 `wrapper` 函数，所以多个 `once` 互不影响。|
|**如果同一个事件绑了 1000 个回调，emit 性能怎么样？**|遍历数组执行，O(n) 复杂度。如果事件数巨大，可以考虑用 `Set` 替代数组，或限制最大监听数（`setMaxListeners`）。|
|**和 Node.js 原生 EventEmitter 的差距？**|原生版还支持：`prependListener`、`prependOnceListener`、`listenerCount`、`eventNames`、`setMaxListeners`、`newListener`/`removeListener` 事件、`error` 事件特殊处理等。|

---

## 💡 面试金句（背下来）

 > 
 > “EventEmitter 的核心是发布-订阅模式。on 负责注册，emit 负责遍历执行，off 负责过滤移除。once 本质是一个 **‘带自毁功能的包装函数’**——触发一次后自动注销。生产环境下，我会关注 `setMaxListeners` 防止内存泄漏，以及在 emit 时对回调数组做浅拷贝，防止遍历过程中被修改。”

---

## 📦 今晚存入 Obsidian

直接在之前的 `手写 EventEmitter.md` 文件中，把“once 追问”和“测试用例”补上即可。你已经有了框架，这次只是把缝补完整。🧵
