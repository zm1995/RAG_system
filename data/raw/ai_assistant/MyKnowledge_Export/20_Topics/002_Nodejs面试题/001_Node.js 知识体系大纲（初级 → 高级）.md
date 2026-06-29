好的，帮你整理一份**Node.js从初级到高级的完整知识大纲**。这份大纲按**面试考察频率**和**知识深度**做了分层，你可以用它来对照自己的掌握程度，也方便后续每天一个主题地推进。

---

# Node.js 知识体系大纲（初级 → 高级）

## 图例说明

|标记|含义|
|--|--|
|🟢|初级必备（面试必问，答不上来直接挂）|
|🟡|中级进阶（体现区分度，决定薪资档位）|
|🔴|高级深水区（拉开差距，决定是否拿Offer）|

## 一、基础语法与核心模块

|知识点|级别|面试常见问法|
|---|--|------|
|模块系统（CommonJS vs ES Module）|🟢|require 和 import 的区别？循环引用怎么办？|
|全局对象（global、process、Buffer）|🟢|process.argv 怎么用？Buffer 和 Uint8Array 的关系？|
|路径处理（path 模块）|🟢|path.resolve 和 path.join 的区别？|
|文件系统（fs 模块）|🟢|readFile 和 createReadStream 的区别？何时用哪个？|
|事件模块（EventEmitter）|🟢|手写 EventEmitter（你已掌握 ✅）|
|HTTP/HTTPS 模块|🟢|原生 http 模块如何创建服务器？req 和 res 是什么？|
|流（Stream）基础|🟡|pipe 的原理？可读流/可写流/双工流/转换流的区别？|
|子进程（child_process）|🟡|spawn vs exec vs fork 的区别？|

## 二、异步编程与事件循环（核心地基）

|知识点|级别|面试常见问法|
|---|--|------|
|事件循环的阶段（6个阶段）|🟢|setTimeout 和 setImmediate 谁先执行？为什么？|
|微任务 vs 宏任务|🟢|process.nextTick 和 Promise.then 谁先执行？|
|异步I/O 原理（Libuv）|🟢|Node.js 单线程如何应对高并发？（你已掌握 ✅）|
|Promise / async / await|🟢|async 函数的执行机制？await 到底在等什么？|
|错误处理（try-catch vs .catch）|🟢|异步错误怎么捕获？unhandledRejection 怎么处理？|
|阻塞与非阻塞|🟡|什么操作会阻塞事件循环？怎么避免？|
|Worker Threads|🔴|什么场景需要 Worker Threads？和 Cluster 的区别？|

## 三、框架与中间件（Express / Koa）

|知识点|级别|面试常见问法|
|---|--|------|
|中间件机制（洋葱模型）|🟢|手写一个简单的中间件系统（即将覆盖 ✅）|
|路由设计|🟢|路由参数怎么获取？如何设计RESTful API？|
|错误处理中间件|🟢|4个参数的中间件有什么特殊之处？|
|静态文件服务|🟢|express.static 的原理？|
|与 Koa 的对比|🟡|Express 和 Koa 的核心区别？（回调 vs 洋葱 + async/await）|
|框架源码设计|🔴|Koa 的 compose 函数是怎么实现的？|

## 四、数据库与持久化

|知识点|级别|面试常见问法|
|---|--|------|
|SQL（MySQL/PostgreSQL）基础|🟢|JOIN、索引、事务的基本概念|
|ORM（Sequelize / Prisma / TypeORM）|🟢|怎么防止 SQL 注入？|
|连接池管理|🟡|连接池的大小怎么设置？连接泄露怎么排查？|
|NoSQL（MongoDB / Redis）|🟡|Redis 在项目中怎么用？（缓存/限流/分布式锁）|
|事务与隔离级别|🔴|分布式事务怎么处理？|

## 五、认证与安全

|知识点|级别|面试常见问法|
|---|--|------|
|Session / Cookie|🟢|Session 和 Cookie 的区别？如何做登录态？|
|JWT|🟢|JWT 的结构是什么？如何做刷新令牌？|
|密码加密（bcrypt）|🟢|为什么不能明文存密码？盐是什么？|
|HTTPS / TLS|🟡|HTTPS 握手过程？TLS 1.3 的改进？|
|常见攻击防御（XSS / CSRF / SQL注入）|🟡|XSS 和 CSRF 的区别？怎么防御？|
|OAuth2.0 / SSO|🔴|OAuth2.0 的四种授权模式？|

## 六、性能优化

|知识点|级别|面试常见问法|
|---|--|------|
|缓存策略（内存 / Redis / CDN）|🟢|什么时候用内存缓存？什么时候用Redis？|
|限流（Rate Limiting）|🟡|滑动窗口限流器的实现（你已掌握 ✅）|
|集群（Cluster 模块）|🟡|Node.js 如何利用多核CPU？|
|内存优化（内存泄漏排查）|🔴|内存泄漏的常见原因？怎么用 heapdump / clinic 排查？|
|性能测试（压测工具）|🔴|你用哪些工具做过压测？怎么分析结果？|

## 七、工程化与部署

|知识点|级别|面试常见问法|
|---|--|------|
|包管理（npm / yarn / pnpm）|🟢|package.json 里的 dependencies 和 devDependencies 区别？|
|环境变量（dotenv / config）|🟢|12-Factor App 是什么？|
|日志（winston / pino）|🟡|日志怎么分级？结构化日志的好处？|
|进程管理（PM2 / systemd）|🟡|PM2 的 cluster mode 是怎么实现的？|
|Docker / K8s 部署|🟡|如何编写 Dockerfile？Node.js 镜像优化技巧？|
|CI/CD|🟡|你的项目是怎么做持续集成的？|

## 八、系统设计与架构（高级核心）

|知识点|级别|面试常见问法|
|---|--|------|
|微服务 vs 单体|🟡|什么时候拆微服务？什么时候保持单体？|
|消息队列（RabbitMQ / Kafka / Bull）|🟡|什么时候用消息队列？怎么保证消息不丢失？|
|分布式追踪（OpenTelemetry / Jaeger）|🔴|如何追踪一个请求在多个服务间的完整链路？|
|API 设计（RESTful / GraphQL / gRPC）|🔴|REST、GraphQL、gRPC 各自适合什么场景？|
|高可用与容灾|🔴|如何设计一个99.99%可用性的系统？|

## 九、综合：那些最经典的高频场景题

|题目|级别|考察方向|
|--|--|----|
|限流器设计（滑动窗口/令牌桶）|🟡|算法 + 系统设计（你已掌握 ✅）|
|大型文件上传/下载|🟡|流 + 断点续传 + 分片|
|消息推送（WebSocket / SSE）|🟡|WebSocket 握手过程？与轮询的区别？|
|定时任务（cron / agenda）|🟡|Node.js 如何实现定时任务？多实例怎么避免重复执行？|
|数据库查询优化|🔴|慢查询怎么排查？联合索引怎么建？|
|第三方API调用（重试/超时/熔断）|🔴|如何实现一个健壮的API客户端？|

## 你现在的位置与下一步

|阶段|已掌握|接下来要补的|
|--|---|------|
|🟢 初级|事件循环、EventEmitter、限流器|HTTP模块、中间件机制、错误处理|
|🟡 中级|—|Stream、Cluster、缓存策略、日志系统|
|🔴 高级|—|内存排查、分布式架构、系统设计|

---

### 🚀 明天的计划

我们已经覆盖了三道题：

* 事件循环 + 异步I/O ✅
* 手写 EventEmitter ✅
* 滑动窗口限流器 ✅

**明天我们从大纲里的「中间件机制」开始：**

 > 
 > "如果让你用 Express 的 `app.use` 风格，手写一个中间件系统，支持异步中间件，你会怎么设计？"

这道题能同时考察：闭包、Promise链、设计模式，面试官非常喜欢问。

今晚把这份大纲存进Obsidian，当作你的**导航地图**，以后每天的节奏由你掌控。想从哪块开始，随时告诉我。💪
