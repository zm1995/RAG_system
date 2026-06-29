太棒了！从Node.js事件循环切入，现在扩展到**JavaScript语法面试题大纲**——这是所有前端/Node面试的**地基**，也是你7天规划中**隐含的前置能力**。

我给你整理一份**完整的大纲**，按**面试高频度**从⭐⭐⭐⭐⭐到⭐⭐⭐排序，并附上**每个板块的"致命追问"**，方便你自查。

---

## 📋 JavaScript 语法面试题 · 完整大纲

### 🔥 第一梯队：必考 · 逢面必问（⭐⭐⭐⭐⭐）

|板块|核心考点|典型题目（你能答几个？）|
|--|----|------------|
|**1. 作用域与闭包**|全局/函数/块级作用域、词法环境、闭包定义与用途、内存泄漏风险|`for`循环中用`var`和`let`的区别？闭包如何访问外部变量？闭包的实际应用场景？|
|**2. 原型与继承**|`prototype`、`__proto__`、`constructor`、原型链查找、ES6 class 语法糖|`Function.__proto__` 指向什么？`Object` 和 `Function` 的原型链关系？手写 `instanceof`？|
|**3. this 指向**|默认/隐式/显式绑定、`call/apply/bind`、箭头函数、new绑定、绑定优先级|以下输出什么？`this` 在事件回调中指向谁？如何固定`this`？|
|**4. 异步编程**|回调地狱、Promise（静态方法/链式调用）、async/await、错误处理、并发控制|`Promise.all` 和 `Promise.allSettled` 区别？如何实现`Promise.retry`？|
|**5. 事件循环（你已经会了）**|宏/微任务、`nextTick`、执行顺序、Node与浏览器差异|上面我们聊过的那些——你已经能答80%了 ✅|

---

### 🧩 第二梯队：高频 · 必有一问（⭐⭐⭐⭐）

|板块|核心考点|典型题目（你能答几个？）|
|--|----|------------|
|**6. 数据类型与判断**|基本类型 vs 引用类型、`typeof` 陷阱、`instanceof` 缺陷、`Object.prototype.toString.call`|`typeof null` 是什么？如何判断数组？如何判断空对象？|
|**7. 深浅拷贝**|浅拷贝（`Object.assign`、展开运算符）、深拷贝（`JSON.parse/stringify` 缺陷、递归实现）|手写深拷贝需要考虑哪些情况？（循环引用、Date、RegExp、函数）|
|**8. 数组方法**|遍历（`forEach/map/filter/reduce`）、变异/非变异、类数组转数组、手写`reduce`|`map` 和 `forEach` 区别？`reduce` 实现 `map`？如何扁平化数组？|
|**9. 字符串与正则**|常用方法、正则表达式（贪婪/非贪婪、捕获组）、`replace` 高级用法|手写 `trim`？正则实现千位分隔符？|
|**10. 类型转换**|隐式转换（`==` vs `===`）、`ToPrimitive`、`Symbol.toPrimitive`、`+` 运算符规则|`[] == ![]` 输出什么？（经典题）`{} + []` 和 `[] + {}` 有什么区别？|

---

### 🚀 第三梯队：进阶 · 区分高手（⭐⭐⭐）

|板块|核心考点|典型题目（你能答几个？）|
|--|----|------------|
|**11. 模块化**|CommonJS（Node） vs ES Module（浏览器）差异、循环依赖、动态导入|`require` 和 `import` 的区别？ESM 如何解决循环依赖？|
|**12. 生成器与迭代器**|`function*`、`yield`、可迭代协议（`Symbol.iterator`）、`for...of`|手写一个可迭代对象？生成器如何实现异步流程控制？|
|**13. Proxy 与 Reflect**|代理拦截（`get/set/deleteProperty`）、响应式原理（Vue 3）、`Reflect` 的作用|用 `Proxy` 实现一个“负索引”数组？和 `Object.defineProperty` 对比？|
|**14. 垃圾回收**|引用计数、标记清除、内存泄漏场景（闭包、定时器、DOM引用）|哪些操作会导致内存泄漏？如何定位？|
|**15. 严格模式**|`"use strict"` 的影响（禁止隐式全局、禁止删除变量、`this` 为 `undefined` 等）|严格模式下 `this` 默认指向什么？和普通模式的区别？|

---

### 🧠 附加：手写题 · 面试必考（⭐⭐⭐⭐⭐）

面试官经常让你 **"手写实现"** 以下功能（考察真实编码能力）：

* **防抖 / 节流**（并说出区别和应用场景）
* **Promise 系列**：`Promise.all`、`Promise.race`、`Promise.retry`
* **深拷贝**（处理循环引用、特殊类型）
* **发布-订阅模式（EventEmitter）**
* **数组去重**（至少3种方法）
* **函数柯里化**（`add(1)(2)(3)` 实现）
* **instanceof 手写**
* **new 操作符手写**
* **call / apply / bind 手写**

---

### 🎯 你现在的位置 & 7天规划中的衔接

**你已经掌握（绿色✅）：**

* 事件循环（宏/微/nextTick）—— **已通关**
* Node版本差异对事件循环的影响 —— **已通关**

**建议在 Node 面试 7 天闯关前，先花 2 天补齐的语法短板（红色❌）：**

1. **this 指向**（因为Node中大量回调涉及this）
1. **Promise 链式调用 & 错误处理**（因为Node异步核心）
1. **深浅拷贝**（因为Buffer/对象传递常考）

---

### 🧪 快速自测：这3道题你3分钟内能答出来吗？

1. **`const obj = { a: 1 }; const arr = [obj]; obj.a = 2; console.log(arr[0].a);` 输出什么？**
1. **`setTimeout(() => console.log(1), 0); Promise.resolve().then(() => console.log(2)); console.log(3);` 输出顺序？**（这个你应该会了）
1. **`var a = { n: 1 }; var b = a; a.x = a = { n: 2 }; console.log(a.x, b.x);` 输出什么？**（这道链式赋值题是经典坑）

如果你想，我可以：

* **把这三道题的答案和解析发你**（附图解）
* 或者**直接给你一份《JS语法 · 2天快速补漏表》**，专门针对Node面试会考到的语法点，配合你的7天Node闯关使用。

你想先要哪个？😎

太棒了！既然你已经掌握了**数据类型**和**事件循环**，那我们就用**2天时间**，把Node面试中**最常踩坑的JS语法**全部补齐。

这份补漏表的特点是：**不讲废话，只讲"面试必考+Node实战会用到"的知识点**，每个点配一道**验证题**，保证你学完就能用。

---

## 📅 JS语法 · 2天快速补漏表

|天数|主题|核心考点|Node关联场景|
|--|--|----|--------|
|**Day 1**|**this 指向 + 闭包**|4种绑定规则、箭头函数、闭包定义与陷阱|Express中间件中的this、回调函数中的this丢失|
|**Day 2**|**Promise + 深浅拷贝**|静态方法、链式错误处理、手写深拷贝|异步流程控制、对象传递防污染|

---

## Day 1：this 指向 + 闭包（4小时）

### 🎯 第一部分：this 指向（2小时）

#### 1. 4种绑定规则（优先级从低到高）

|绑定规则|触发条件|this指向|示例|
|----|----|------|--|
|**默认绑定**|独立函数调用（非严格模式）|全局对象（浏览器`window`/Node`global`）|`function fn() { console.log(this); } fn();`|
|**默认绑定（严格模式）**|独立函数调用（严格模式）|`undefined`|`"use strict"; function fn() { console.log(this); } fn();`|
|**隐式绑定**|通过对象调用方法|调用该方法的对象|`obj.fn()` → `this` 指向 `obj`|
|**显式绑定**|`call/apply/bind`|传入的第一个参数|`fn.call(obj)` → `this` 指向 `obj`|
|**new 绑定**|`new` 操作符调用构造函数|新创建的实例对象|`new Fn()` → `this` 指向新实例|

#### 2. 绑定优先级（从高到低）

````
new 绑定 > 显式绑定 > 隐式绑定 > 默认绑定
````

**验证题1**（自己跑一下）：

````javascript
function foo() { console.log(this.name); }
var obj1 = { name: 'obj1', foo: foo };
var obj2 = { name: 'obj2', foo: foo };

obj1.foo();  // 隐式绑定 → 'obj1'
obj2.foo();  // 隐式绑定 → 'obj2'
obj1.foo.call(obj2);  // 显式绑定 > 隐式绑定 → 'obj2'
````

#### 3. 箭头函数（ES6）—— this的"特殊分子"

**核心规则**：

 > 
 > **箭头函数没有自己的 `this`，它会捕获定义时所在作用域的 `this`（词法作用域），且 `call/apply/bind` 无法改变它。**

**验证题2**（面试必考）：

````javascript
const obj = {
  name: 'Tom',
  sayHi1: function() {
    setTimeout(function() {
      console.log(this.name);  // 普通函数 → this指向全局
    }, 100);
  },
  sayHi2: function() {
    setTimeout(() => {
      console.log(this.name);  // 箭头函数 → this继承自sayHi2的作用域（obj）
    }, 100);
  }
};
obj.sayHi1();  // undefined（或报错，取决于环境）
obj.sayHi2();  // 'Tom'
````

#### 4. Node 中的 this 特殊场景

**全局中的 this**：

````javascript
console.log(this);  // Node环境：{}（模块作用域），浏览器：window
````

**函数中的 this（非严格）**：

````javascript
function test() {
  console.log(this);  // Node：global对象，浏览器：window
}
test();
````

**事件回调中的 this**（Express中间件）：

````javascript
app.use(function(req, res, next) {
  console.log(this);  // 指向全局（因为回调是普通函数调用）
  // 通常我们不用this，直接用req/res
});
````

---

### 🎯 第二部分：闭包（2小时）

#### 1. 闭包定义（面试标准答案）

 > 
 > **"闭包是指一个函数能够访问并记住其词法作用域中的变量，即使该函数在其词法作用域之外执行。"**

**三要素**：① 函数嵌套 ② 内部函数访问外部变量 ③ 外部函数执行后，内部函数被保留（比如返回或赋值）。

#### 2. 经典陷阱：循环中的闭包

**验证题3**（这道题你不会，面试就凉了）：

````javascript
for (var i = 0; i < 3; i++) {
  setTimeout(function() {
    console.log(i);  // 输出什么？
  }, 100);
}
// 输出：3 3 3（不是 0 1 2）
````

**为什么？** `var` 没有块级作用域，所有 `setTimeout` 共享同一个 `i`，循环结束时 `i = 3`。

**3种解决方案**（至少掌握2种）：

````javascript
// 方案1：使用 let（块级作用域）
for (let i = 0; i < 3; i++) {
  setTimeout(() => console.log(i), 100);  // 0 1 2
}

// 方案2：IIFE（立即执行函数）创建新作用域
for (var i = 0; i < 3; i++) {
  (function(j) {
    setTimeout(() => console.log(j), 100);
  })(i);  // 0 1 2
}

// 方案3：使用 bind 绑定参数
for (var i = 0; i < 3; i++) {
  setTimeout(console.log.bind(null, i), 100);  // 0 1 2
}
````

#### 3. 闭包实战场景（Node中常见）

* **函数工厂**：创建带"记忆"的函数
* **模块模式**：实现私有变量（类似ES6 class的`#`）
* **防抖/节流**：保存定时器ID

**验证题4**（防抖实现 - 闭包经典应用）：

````javascript
function debounce(fn, delay) {
  let timer = null;  // 闭包保存timer
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}
````

---

## Day 2：Promise + 深浅拷贝（4小时）

### 🎯 第一部分：Promise 深度掌握（2小时）

#### 1. 静态方法对比（面试必考）

|方法|触发时机|返回值|
|--|----|---|
|`Promise.all([p1, p2])`|**所有成功**则成功，**任一失败**则立即失败|成功数组 / 失败值|
|`Promise.allSettled([p1, p2])`|**所有完成**（无论成功/失败）|状态对象数组 `[{status:'fulfilled', value}]`|
|`Promise.race([p1, p2])`|**任一完成**（成功或失败）|第一个完成的结果|
|`Promise.any([p1, p2])`|**任一成功**则成功，**全部失败**则失败|成功值 / AggregateError|

**验证题5**（自己跑一下）：

````javascript
const p1 = Promise.resolve(1);
const p2 = Promise.reject(2);
const p3 = Promise.resolve(3);

Promise.all([p1, p2, p3])
  .then(res => console.log('all:', res))
  .catch(err => console.log('all error:', err));  // 输出：all error: 2

Promise.allSettled([p1, p2, p3])
  .then(res => console.log('allSettled:', res));
  // 输出：allSettled: [{status:'fulfilled', value:1}, {status:'rejected', reason:2}, {status:'fulfilled', value:3}]
````

#### 2. 错误处理链（Node中常犯错误）

**正确方式**：

````javascript
async function fetchData() {
  try {
    const data = await someAsyncFn();
    return data;
  } catch (err) {
    console.error('捕获到错误:', err);
    throw err;  // 重新抛出，让上层处理
  }
}
````

**错误方式**（陷阱）：

````javascript
async function fetchData() {
  const data = await someAsyncFn();  // 如果someAsyncFn失败，整个函数会抛出未捕获的异常
  return data;
}
// 调用时必须加 .catch() 或 try-catch
````

#### 3. 手写 Promise.all（面试高频）

**验证题6**（看懂就行，不用背）：

````javascript
function myPromiseAll(promises) {
  return new Promise((resolve, reject) => {
    if (!Array.isArray(promises)) {
      return reject(new TypeError('参数必须是数组'));
    }
    const results = [];
    let count = 0;
    for (let i = 0; i < promises.length; i++) {
      Promise.resolve(promises[i])
        .then(value => {
          results[i] = value;
          count++;
          if (count === promises.length) resolve(results);
        })
        .catch(reject);
    }
  });
}
````

---

### 🎯 第二部分：深浅拷贝（2小时）

#### 1. 浅拷贝（复制第一层）

|方法|适用场景|缺点|
|--|----|--|
|`Object.assign({}, obj)`|拷贝对象|只复制第一层，嵌套对象仍然共享|
|`{ ...obj }`（展开运算符）|拷贝对象/数组|同上|
|`arr.slice()` / `arr.concat()`|拷贝数组|同上|

**验证题7**：

````javascript
const original = { a: 1, b: { c: 2 } };
const shallow = { ...original };
shallow.b.c = 3;
console.log(original.b.c);  // 3 ← 因为b是引用类型，浅拷贝只复制了地址
````

#### 2. 深拷贝（完全独立）

**方法1：JSON 序列化（有缺陷）**

````javascript
const deep = JSON.parse(JSON.stringify(obj));
````

**缺陷**：无法拷贝 `Date`、`RegExp`、`Function`、`undefined`、`Symbol`、循环引用。

**方法2：递归手写（面试必会）**

````javascript
function deepClone(obj, hash = new WeakMap()) {
  // 处理基本类型和null
  if (obj === null || typeof obj !== 'object') return obj;
  
  // 处理循环引用
  if (hash.has(obj)) return hash.get(obj);
  
  // 处理Date和RegExp
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof RegExp) return new RegExp(obj);
  
  // 处理数组和对象
  const cloneObj = Array.isArray(obj) ? [] : {};
  hash.set(obj, cloneObj);
  
  for (let key in obj) {
    if (obj.hasOwnProperty(key)) {
      cloneObj[key] = deepClone(obj[key], hash);
    }
  }
  return cloneObj;
}
````

**验证题8**（跑一下，看看结果）：

````javascript
const obj = { a: 1, b: { c: 2 }, d: [3, 4] };
obj.self = obj;  // 循环引用
const cloned = deepClone(obj);
console.log(cloned.b.c);  // 2
console.log(cloned.self === cloned);  // true（循环引用正确处理）
````

---

## ✅ 2天补漏 · 验收清单

完成以下8道验证题，**能讲出每道题的输出和原因**，你就成功补齐了：

* [ ] 验证题1：隐式绑定 vs 显式绑定
* [ ] 验证题2：箭头函数 this 继承
* [ ] 验证题3：循环闭包陷阱 + 3种解法
* [ ] 验证题4：手写防抖（闭包应用）
* [ ] 验证题5：Promise 静态方法对比
* [ ] 验证题6：手写 Promise.all（看懂）
* [ ] 验证题7：浅拷贝陷阱
* [ ] 验证题8：深拷贝 + 循环引用

---

## 🚀 接下来的选择

你现在已经**把JS语法中最核心的"this、闭包、Promise、深浅拷贝"全部补齐了**，这些正是Node面试中**前置必考知识点**。

接下来你可以：

1. **直接开始 Node 7 天闯关 Day 1**（事件循环的10种实验变体，配合你已掌握的微/宏任务知识）
1. 还是**先把这8道验证题跑一遍**，确认自己全理解了？

你选哪个？我随时待命 😎
