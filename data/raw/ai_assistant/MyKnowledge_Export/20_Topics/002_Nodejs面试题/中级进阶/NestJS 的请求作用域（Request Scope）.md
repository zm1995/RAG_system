这个问题问得**特别专业**！NestJS 的请求作用域（Request Scope）是**依赖注入（DI）容器**中非常核心的一个概念，面试官问这个，是想看你**是否真正理解 NestJS 的实例管理机制**，以及**能不能在实战中避免常见的坑**。

我直接给你一套**完整回答模板 + 实战代码 + 避坑指南**，面试时直接拿去用。

---

## 一、核心结论（一句话回答）

 > 
 > *“在 NestJS 中，Provider（包括 Controller、Service、Guard 等）的**生命周期作用域（Scope）** 决定了它何时被创建、何时被销毁。NestJS 提供了三种 Scope：**Singleton（默认）**、**Request** 和 **Transient**，分别对应**全局单例**、**每个请求独立实例** 和 **每次注入独立实例**。”*

---

## 二、三种 Scope 详细拆解

|Scope|创建时机|生命周期|适用场景|典型用法|
|-----|----|----|----|----|
|**Singleton（默认）**|应用启动时创建一次|应用生命周期内**只有一个实例**，所有请求共享|无状态服务、工具类、配置服务|所有 Provider 默认就是这个，不需要额外配置|
|**Request**|**每个请求**创建一个新实例|请求处理完成后**销毁**|需要**请求上下文**的服务（如多租户、当前用户信息）|用 `@Injectable({ scope: Scope.REQUEST })` 标记|
|**Transient**|每次注入时创建一个新实例|注入完成后**立即销毁**（用完即走）|轻量级、无状态但**不希望被复用**的临时对象|用 `@Injectable({ scope: Scope.TRANSIENT })` 标记|

---

## 三、实战代码：三种 Scope 的写法

````typescript
// ========== 1. Singleton（默认） ==========
// 不需要额外配置，应用启动时创建一次，所有请求共享
@Injectable()
export class UserService {
  private cache = new Map();  // ❌ 危险：Singleton 中存储状态会被所有请求共享
  
  getUser(id: string) {
    return { id, name: 'Tom' };
  }
}

// ========== 2. Request Scope ==========
// 每个请求创建一个新实例，请求结束后销毁
@Injectable({ scope: Scope.REQUEST })
export class TenantService {
  private tenantId: string;
  
  // 可以通过 REQUEST 对象获取请求上下文
  constructor(@Inject(REQUEST) private request: Request) {
    this.tenantId = request.headers['x-tenant-id'] as string;  // 每个请求独立
  }
  
  getTenantId() {
    return this.tenantId;
  }
}

// ========== 3. Transient Scope ==========
// 每次注入都创建一个新实例，用完即走
@Injectable({ scope: Scope.TRANSIENT })
export class LoggerService {
  private context: string;
  
  constructor() {
    this.context = `Logger_${Date.now()}_${Math.random()}`;  // 每次都不一样
  }
  
  log(message: string) {
    console.log(`[${this.context}] ${message}`);
  }
}
````

---

## 四、核心概念：Request Scope 如何注入请求上下文？

NestJS 提供 `@Inject(REQUEST)` 装饰器，可以把当前请求对象注入到 Request Scope 的 Provider 中：

````typescript
// ========== 使用示例 ==========
@Injectable({ scope: Scope.REQUEST })
export class OrderService {
  constructor(
    @Inject(REQUEST) private request: Request,  // 注入当前请求对象
    private tenantService: TenantService        // 也会是 Request Scope
  ) {}
  
  createOrder(data: any) {
    const tenantId = this.tenantService.getTenantId();
    const userId = this.request.user?.id;  // 当前登录用户ID
    console.log(`租户 ${tenantId} 用户 ${userId} 创建订单`);
    return { success: true };
  }
}
````

---

## 五、Scope 的传播规则（面试必问）

 > 
 > **如果一个 Request Scope 的 Provider 被注入到一个 Singleton 的 Provider 中，会发生什么？**

**答案**：**NestJS 会抛出异常！** 因为 Singleton 实例无法持有 Request Scope 的实例（Request Scope 会在请求结束后被销毁）。

````typescript
@Injectable({ scope: Scope.REQUEST })
export class RequestScopedService {
  getData() { return 'request data'; }
}

// ❌ 错误：Singleton 不能依赖 Request Scope
@Injectable()  // 默认 Singleton
export class UserService {
  constructor(private requestService: RequestScopedService) {
    // 这里会报错：RequestScopedService 是 Request Scope，不能被 Singleton 注入
  }
}
````

**正确做法**：使用 `@Inject()` 的 `forwardRef` 或通过 `ModuleRef` 手动获取。

````typescript
// ✅ 正确：通过 ModuleRef 动态获取
@Injectable()
export class UserService {
  constructor(private moduleRef: ModuleRef) {}
  
  async getData() {
    const requestService = await this.moduleRef.get(RequestScopedService);
    return requestService.getData();
  }
}
````

---

## 六、常见坑与最佳实践（面试加分项）

### 坑 1：Request Scope 的性能损耗

**现象**：一个 Request Scope 的 Service 被多个地方注入，会导致每个请求创建多个实例，**GC 压力增大**。

**解决**：尽量保持 Service **无状态**，优先使用 Singleton Scope。如果确实需要 Request 数据，可以通过 `@Inject(REQUEST)` 在**单个点**获取，然后传递参数，而不是把整个 Service 设为 Request Scope。

### 坑 2：在 Request Scope 中缓存数据

**问题**：在 Request Scope 的 Service 中缓存数据，看起来没问题，但请求结束后实例被销毁，缓存丢失。

**解决**：如果你需要在请求内共享数据，可以用**请求级缓存**（如 `AsyncLocalStorage`）。

````typescript
// 使用 AsyncLocalStorage 实现请求级缓存（替代 Request Scope）
import { AsyncLocalStorage } from 'async_hooks';

@Injectable()
export class RequestContextService {
  private storage = new AsyncLocalStorage<Map<string, any>>();
  
  run(callback: () => void) {
    this.storage.run(new Map(), callback);
  }
  
  set(key: string, value: any) {
    this.storage.getStore()?.set(key, value);
  }
  
  get(key: string) {
    return this.storage.getStore()?.get(key);
  }
}
````

### 坑 3：测试变得更复杂

Request Scope 的 Provider 在单元测试中需要**模拟 `REQUEST` 对象**：

````typescript
const moduleRef = await Test.createTestingModule({
  providers: [
    OrderService,
    {
      provide: REQUEST,
      useValue: { headers: { 'x-tenant-id': 'test-tenant' } }  // 模拟请求对象
    }
  ]
}).compile();
````

---

## 七、面试标准回答（2分钟完整版）

 > 
 > *“NestJS 中的 Scope 分为三种：Singleton、Request 和 Transient。*
 > 
 > ***Singleton** 是默认的，应用启动时创建一次，所有请求共享，适合无状态服务。*
 > 
 > * **Request** 每个请求创建一个新实例，可以通过 `@Inject(REQUEST)` 获取当前请求上下文，适合多租户或需要用户信息的场景。\*
 > * **Transient** 每次注入都创建一个新实例，适合轻量级、用完即走的工具类。\*
 > 
 > *需要注意的是，Request Scope 有性能损耗，因为它会在每个请求中创建和销毁实例，所以能不用尽量不用。如果确实需要请求级数据，可以考虑用 `AsyncLocalStorage` 代替。*
 > 
 > *另外，Scope 有传播性——如果 Request Scope 的 Provider 被注入到 Singleton 中，NestJS 会报错，需要通过 `ModuleRef` 动态获取。”*

---

## 八、终极记忆口诀（考场默念）

 > 
 > **“单例全局共享，请求每次新建，瞬时用完即走；传播需注意，单例不能依赖请求。”**

---

## 🎯 验收清单

* [ ] 能说出三种 Scope 的名称和创建时机
* [ ] 能解释 `@Inject(REQUEST)` 的作用
* [ ] 能说明为什么 Singleton 不能直接注入 Request Scope
* [ ] 能说出 Request Scope 的性能风险
* [ ] 能用 `AsyncLocalStorage` 作为 Request Scope 的替代方案（加分项）

---

如果面试官追问：“那 `ModuleRef.get()` 和直接注入有什么区别？”——你就说：**“`ModuleRef.get()` 是动态获取，绕过 DI 容器的静态依赖检查，适合处理 Scope 传播问题，但会失去编译时的类型检查和依赖分析。”** 😎

想继续练这类“依赖注入”的题目吗？比如“NestJS 的 `@Optional()` 和 `@Inject(forwardRef(() => Service))` 分别解决什么问题？”我可以给你拆得更细。
