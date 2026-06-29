这个问题问得**特别实战**！在 Node.js 中处理 Session 和 Cookie 是**面试必考**的 Web 基础知识，面试官问这个，是想看你**是否真正理解有状态 Web 服务的核心机制**，以及**能不能在实战中避免安全漏洞**。

我帮你拆成 **Cookie 和 Session 两大块**，附带**完整代码、对比表格、安全注意事项**。

---

## 一、核心概念速通（面试必答开场白）

 > 
 > **Cookie 是存储在客户端的"身份证"（最多 4KB），而 Session 是存储在服务端的"档案室"。** Cookie 里存的是 Session ID（档案编号），服务端通过这个编号在内存/Redis 里找到用户的具体信息。

|特性|**Cookie**|**Session**|
|--|------|-------|
|**存储位置**|浏览器本地|服务器内存 / Redis / 数据库|
|**大小限制**|≤ 4KB|无限制（视存储介质而定）|
|**生命周期**|可持久化（设置 `Max-Age`）|通常较短（30分钟~几天）|
|**安全性**|可被篡改（需签名/加密）|服务端存储，相对安全|
|**典型用途**|保存 Session ID、用户偏好|保存用户信息、登录状态|

## 二、原生 Node.js 设置 Cookie（底层实现）

**1. 服务端设置 Cookie（通过 `Set-Cookie` 响应头）**

````javascript
const http = require('http');

const server = http.createServer((req, res) => {
  // 1. 设置一个简单的 Cookie（不带属性）
  res.setHeader('Set-Cookie', 'username=Tom');
  
  // 2. 设置多个 Cookie
  res.setHeader('Set-Cookie', [
    'username=Tom; Max-Age=3600; HttpOnly; Secure; SameSite=Strict',
    'theme=dark; Max-Age=86400',
    'sessionId=abc123; HttpOnly; Secure; SameSite=Lax'
  ]);
  
  // 3. 删除 Cookie（把 Max-Age 设为 0 或过去的时间）
  res.setHeader('Set-Cookie', 'username=; Max-Age=0; Path=/');
  
  res.end('Cookie 已设置');
});
server.listen(3000);
````

**2. 服务端读取 Cookie（解析 `Cookie` 请求头）**

````javascript
const http = require('http');

const server = http.createServer((req, res) => {
  // 原生方式：手动解析 Cookie 字符串
  const cookieHeader = req.headers.cookie; // "username=Tom; theme=dark"
  
  // 手写解析函数
  const parseCookies = (str) => {
    if (!str) return {};
    return str.split(';').reduce((acc, pair) => {
      const [key, value] = pair.trim().split('=');
      acc[key] = decodeURIComponent(value);
      return acc;
    }, {});
  };
  
  const cookies = parseCookies(cookieHeader);
  console.log('当前用户:', cookies.username);
  
  res.end('Hello');
});
````

**Cookie 属性速查表**：

|属性|作用|示例|
|--|--|--|
|`Max-Age`|有效期（秒）|`Max-Age=3600`（1小时）|
|`Expires`|过期日期（GMT时间）|`Expires=Wed, 21 Oct 2025 07:28:00 GMT`|
|`HttpOnly`|禁止 JS 读取（防 XSS）|`HttpOnly`|
|`Secure`|仅 HTTPS 传输|`Secure`|
|`SameSite`|跨站请求控制（防 CSRF）|`Strict` / `Lax` / `None`|
|`Path`|Cookie 生效路径|`Path=/admin`|

## 三、Express 中设置 Cookie（推荐）

Express 提供了更简洁的 `res.cookie()` 和 `res.clearCookie()`。

**1. 安装 Cookie 解析中间件**

````bash
npm install cookie-parser
````

**2. 设置和读取 Cookie**

````javascript
const express = require('express');
const cookieParser = require('cookie-parser');

const app = express();
app.use(cookieParser());  // 解析 Cookie，挂载到 req.cookies

// ========== 设置 Cookie ==========
app.get('/set-cookie', (req, res) => {
  // 基础 Cookie
  res.cookie('username', 'Tom', {
    maxAge: 3600000,        // 1小时（毫秒）
    httpOnly: true,         // 禁止 JS 读取
    secure: true,           // 仅 HTTPS
    sameSite: 'strict',     // 防 CSRF
    path: '/',              // 全局生效
  });
  
  // 带签名的 Cookie（防篡改）
  res.cookie('sessionId', 'abc123', {
    signed: true,           // 启用签名（需要 cookie-parser 的 secret）
    maxAge: 7 * 24 * 3600000,
  });
  
  res.send('Cookie 已设置');
});

// ========== 读取 Cookie ==========
app.get('/get-cookie', (req, res) => {
  // 普通 Cookie
  console.log(req.cookies.username);  // 'Tom'
  
  // 签名 Cookie（需要 secret）
  console.log(req.signedCookies.sessionId);  // 'abc123'
  
  res.json({ cookies: req.cookies, signedCookies: req.signedCookies });
});

// ========== 删除 Cookie ==========
app.get('/clear-cookie', (req, res) => {
  res.clearCookie('username', { path: '/' });
  res.send('Cookie 已删除');
});
````

**签名 Cookie 原理**：服务端用 `secret` 对 Cookie 值做 HMAC 签名，防止客户端篡改。如果客户端修改了 Cookie，服务端会识别并拒绝。

````javascript
const cookieParser = require('cookie-parser');
app.use(cookieParser('my-secret-key'));  // 传入 secret
````

## 四、Express 中设置 Session（生产级方案）

最常用的是 **`express-session`** 中间件，默认把 Session 存在内存中，生产环境要配合 Redis 使用。

**1. 安装**

````bash
npm install express-session
npm install connect-redis  # 如果要用 Redis 存储
````

**2. 基础用法（内存存储，仅开发测试）**

````javascript
const express = require('express');
const session = require('express-session');

const app = express();

app.use(session({
  secret: 'your-secret-key',           // 用于签名 Session ID
  name: 'sessionId',                   // Cookie 名称（默认 connect.sid）
  resave: false,                       // 是否强制保存未修改的 Session
  saveUninitialized: false,            // 是否保存空 Session
  cookie: {
    maxAge: 3600000,                   // 1小时
    httpOnly: true,
    secure: false,                     // 开发环境用 false，生产环境用 true（HTTPS）
    sameSite: 'lax',
  }
}));

// ========== 设置 Session ==========
app.get('/login', (req, res) => {
  // 用户登录成功后
  req.session.user = {
    id: 1,
    name: 'Tom',
    role: 'admin'
  };
  req.session.isLoggedIn = true;
  res.send('登录成功');
});

// ========== 读取 Session ==========
app.get('/profile', (req, res) => {
  if (req.session.isLoggedIn) {
    res.json({
      user: req.session.user,
      sessionId: req.sessionID  // 当前 Session ID
    });
  } else {
    res.status(401).send('请先登录');
  }
});

// ========== 删除 Session（退出登录） ==========
app.get('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) {
      console.error('注销失败:', err);
      res.send('注销失败');
    } else {
      res.clearCookie('sessionId');  // 删除客户端 Cookie
      res.send('已退出登录');
    }
  });
});
````

**3. 生产环境：Session 存到 Redis**

````javascript
const express = require('express');
const session = require('express-session');
const RedisStore = require('connect-redis')(session);
const redisClient = require('ioredis');

const app = express();

app.use(session({
  store: new RedisStore({ client: redisClient }),  // Session 存 Redis
  secret: 'your-secret-key',
  resave: false,
  saveUninitialized: false,
  cookie: {
    maxAge: 3600000,
    httpOnly: true,
    secure: true,  // 生产环境必须 HTTPS
    sameSite: 'strict',
  }
}));
````

## 五、安全最佳实践（面试加分项）

|攻击类型|防护措施|代码配置|
|----|----|----|
|**XSS（跨站脚本攻击）**|Cookie 设置 `HttpOnly`，禁止 JS 读取|`httpOnly: true`|
|**CSRF（跨站请求伪造）**|Cookie 设置 `SameSite=Strict/Lax`；使用 CSRF Token|`sameSite: 'strict'`|
|**中间人攻击（MITM）**|生产环境强制 HTTPS + `Secure` Cookie|`secure: true`|
|**会话固定攻击**|登录后重新生成 Session ID|`req.session.regenerate()`|
|**Cookie 篡改**|使用签名 Cookie|`cookieParser(secret)` + `signed: true`|

## 六、面试标准回答（2分钟完整版）

 > 
 > *"在 Node.js 中设置 Session 和 Cookie 主要通过 `express-session` 和 `cookie-parser` 这两个中间件。*
 > *`cookie-parser` 负责解析客户端发来的 Cookie 到 `req.cookies`，而 `res.cookie()` 可以设置带有 HttpOnly、Secure、SameSite 等安全属性的 Cookie。*
 > *`express-session` 则管理服务端的 Session，它会在客户端设置一个包含 Session ID 的 Cookie，然后把真实的用户数据存储到内存或 Redis 中。*
 > *生产环境需要注意三点：一是 Session 要用 Redis 存储，不能存内存（会导致多实例无法共享，且内存泄漏风险）；二是 Cookie 必须设置 `HttpOnly` 和 `Secure` 防止 XSS 和中间人攻击；三是登录成功后要调用 `req.session.regenerate()` 防止会话固定攻击。"*

## 七、验收清单

* [ ] 能说出 Cookie 和 Session 的核心区别（存储位置、大小、安全性）
* [ ] 能写出 `res.cookie()` 设置 Cookie 的完整属性
* [ ] 能说出 `httpOnly`、`secure`、`sameSite` 分别防御什么攻击
* [ ] 能说出 Session 存 Redis 的原因（多实例共享、持久化、防内存泄漏）
* [ ] 能说出 `req.session.destroy()` 和 `req.session.regenerate()` 的区别

---

如果面试官追问：“JWT 和 Session 有什么区别？什么时候用哪个？”——你就说：**“Session 依赖服务端存储，适合有状态场景（如管理后台）；JWT 是无状态的，适合分布式系统（如 API 网关），但它无法主动失效，需要配合黑名单或短过期时间。”** 😎

想继续深入这个话题吗？比如“JWT 如何结合 Cookie 实现安全的身份认证？”可以接着聊！
