[QA环境部署](QA%E7%8E%AF%E5%A2%83%E9%83%A8%E7%BD%B2.md)

在 QA 环境部署 Web3 TEE 私钥存储，核心思路是：**将 TEE 机密计算框架（如 Flare FCC、Phala、EigenCompute）集成到你已有的 QA 测试流程中**。

由于本地通常不具备真实 TEE 硬件，QA 阶段主要采用“**模拟 TEE 环境**”进行功能验证，待预发或生产环境再切换为真实硬件。

这里为你整理了两种主流部署方案，以及一个可直接落地的 QA 流程。

---

### ⚙️ 方案一：使用开源框架本地模拟（Flare / Marlin 方案）

这种方式适合功能测试和集成测试，不需要特殊的 CPU 硬件（如 Intel SGX/AMD SEV）。

#### 1. 准备工作

* **安装 Docker & Docker Compose**：TEE 扩展通常以 Docker 容器形式运行。
* **安装 CLI 工具**：
  * **Flare FCC Workbench**：`npm install -g @flarestudio/fcc-workbench`，用于生成项目脚手架和模拟密钥。
  * **Marlin Oyster CLI**：用于在本地模拟完整的 TEE 行为（如 Keygen、Attestation）。

#### 2. 搭建模拟 TEE 节点

你可以克隆 Flare 官方的私钥管理示例仓库，并启动模拟服务：

````bash
# 克隆 TEE 私钥扩展项目
git clone https://github.com/flare-foundation/fcc-private-key-extension
cd fcc-private-key-extension

# 配置环境变量（填入测试网私钥）
cp .env.example .env

# 启动 TEE 模拟环境
docker compose up -d
````

此时，你会得到一个运行在本地的“虚拟安全 enclave”，它支持：

* **密钥生成**：通过 `flare-fcc keygen` 生成模拟的 TEE 机器身份。
* **密钥注入**：通过 `flare-fcc encrypt` 加密你的测试私钥，并发送给模拟 TEE。

#### 3. 部署测试合约

如果你涉及链上交互，需要将指令发送合约部署到**测试网**：

````bash
# 部署 InstructionSender 合约（以 Flare Coston2 测试网为例）
cd go/tools
go run ./cmd/deploy-contract
````

#### 4. 启动隧道服务

为了方便链上 Indexer 访问你的本地 QA 环境，需要暴露本地端口：

````bash
# 使用 cloudflared 将本地 6676 端口暴露到公网
cloudflared tunnel --url http://localhost:6676
````

 > 
 > **QA 验收点**：此时应能通过 `curl http://localhost:6676/info` 获取到 TEE 的公钥信息，表明模拟环境运行正常。

---

### 📦 方案二：使用云平台托管环境（Phala / EigenCompute 方案）

这种方式适合测试**远程证明（Remote Attestation）** 或 **Key Sharding** 等需要真实硬件特性的场景，无需自建硬件。

#### 1. 准备 Docker 镜像

将你的私钥管理逻辑打包成 Docker 镜像，这是部署到 TEE 云平台的标准格式。

````dockerfile
FROM --platform=linux/amd64 node:18
USER root
WORKDIR /app
COPY . .
RUN npm install

# 暴露服务端口
EXPOSE 3000
CMD ["npm", "start"]
````

#### 2. 使用平台 CLI 部署

以 **EigenCompute** 为例，其 CLI 支持一键将镜像部署到 TEE 节点：

````bash
# 安装 CLI
npm install -g @layr-labs/ecloud-cli

# 登录并选择测试网环境
ecloud auth login
ecloud compute env set sepolia

# 部署应用到 TEE（平台自动注入加密的私钥或助记词）
ecloud compute app deploy
````

#### 3. 验证私钥隔离性

在 Phala Cloud 等平台上，环境变量中的 `MNEMONIC` 或私钥是由平台 KMS 自动注入的，且**仅在 TEE 内部解密**。

 > 
 > **QA 验收点**：在应用代码中打印私钥，若在 TEE 外（如日志）无法获取明文，则说明隔离生效。

---

### 📝 关键 QA 测试用例建议

在 QA 环境中，无论采用哪种方案，都应重点覆盖以下场景：

1. **密钥注入测试**：
   
   * **操作**：使用 TEE 公钥加密一个测试私钥（如 `0xac...`），通过链上交易或 API 发送给 TEE 节点。
   * **断言**：查询 TEE 状态，确认私钥已存入内存，且外部无法读取。
1. **签名功能测试**：
   
   * **操作**：发送一个 `Sign` 指令（例如对字符串 `"Hello QA"` 进行签名）。
   * **断言**：返回的签名可通过对应的公钥验签，证明私钥确实在 TEE 内部被正确使用。
1. **数据持久化测试**：
   
   * **场景**：重启 TEE 容器后，之前注入的私钥是否丢失？（通常设计是不持久化，需验证业务逻辑的兜底策略）。

### 💎 总结与最佳实践

|阶段|推荐方案|核心工具|
|:-|:---|:---|
|**单元/集成测试**|本地模拟|Flare FCC, Marlin Oyster, Docker|
|**系统/验收测试**|云 TEE 环境|Phala Cloud, EigenCompute, AWS Nitro Enclaves|
|**回归测试**|自动化脚本 + Mock|直接 Mock `sign` 接口返回值，不启动真实 TEE|

最后有一个关键点需要注意：**QA 与生产环境的差异处理**

* **本地模拟**：密钥是软生成的在内存中，`Attestation` 报告通常是硬编码的 mock 数据。
* **生产环境**：密钥由 CPU 硬件保护，`Attestation` 报告需通过 IAS/DCAP 服务验证。

建议在 CI 流程中，将**模拟 TEE 容器**作为数据库或 Redis 类似的依赖服务一并拉起，这样才能实现自动化测试。

考虑到你的项目主要基于哪些技术栈（如 EVM 兼容链、Solana 或普通后端服务）？如果有具体的框架限制，我可以帮你进一步细化模拟层的实现方案。
