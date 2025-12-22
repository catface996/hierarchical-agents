# EC2 Docker 快速部署指南

本文档介绍如何在 EC2 上使用 Docker Compose 快速部署层级多智能体系统，并使用测试脚本验证。

## 前置要求

- EC2 实例 (Amazon Linux 2023 / Ubuntu)
- Docker 和 Docker Compose
- AWS 认证配置 (API Key 或 IAM Role)

---

## 一、准备 EC2 实例

### 1.1 安装 Docker

**Amazon Linux 2023:**
```bash
sudo yum update -y
sudo yum install -y docker git
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ec2-user

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 重新登录以应用 docker 组
exit
```

**Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose git python3 python3-pip
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -a -G docker ubuntu
exit
```

### 1.2 配置 IAM 角色 (推荐)

为 EC2 实例附加 IAM 角色，包含以下权限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 二、部署服务

### 2.1 克隆代码

```bash
git clone https://github.com/catface996/hierarchical-agents.git
cd hierarchical-agents
```

### 2.2 配置环境变量

**方式 A: 使用 IAM Role (推荐用于 EC2)**

```bash
cat > .env << 'EOF'
# 数据库配置
DB_TYPE=mysql
DB_HOST=mysql
DB_PORT=3306
DB_NAME=hierarchical_agents
DB_USER=root
DB_PASSWORD=hierarchical123

# AWS 配置 - IAM Role 认证
USE_IAM_ROLE=true
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# 服务器配置
PORT=8080
DEBUG=false
EOF
```

**方式 B: 使用 AK/SK 认证**

```bash
cat > .env << 'EOF'
# 数据库配置
DB_TYPE=mysql
DB_HOST=mysql
DB_PORT=3306
DB_NAME=hierarchical_agents
DB_USER=root
DB_PASSWORD=hierarchical123

# AWS 配置 - AK/SK 认证
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# 服务器配置
PORT=8080
DEBUG=false
EOF
```

**方式 C: 使用 API Key 认证**

```bash
cat > .env << 'EOF'
# 数据库配置
DB_TYPE=mysql
DB_HOST=mysql
DB_PORT=3306
DB_NAME=hierarchical_agents
DB_USER=root
DB_PASSWORD=hierarchical123

# AWS 配置 - API Key 认证
AWS_BEDROCK_API_KEY=your-api-key
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0

# 服务器配置
PORT=8080
DEBUG=false
EOF
```

### 2.3 启动服务

```bash
# 使用 docker-compose 启动 (本地构建)
docker-compose up -d --build

# 或使用预构建镜像 (更快)
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
```

### 2.4 验证服务

```bash
# 健康检查
curl http://localhost:18080/health

# 预期输出:
# {"status":"healthy","timestamp":"...","version":"1.0.0"}
```

---

## 三、创建测试层级团队

### 3.1 通过 API 创建层级团队

```bash
curl -X POST http://localhost:18080/api/v1/hierarchies/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "量子力学研究团队",
    "global_prompt": "你是量子力学研究团队的首席科学家，负责协调理论和应用研究。",
    "execution_mode": "sequential",
    "teams": [
      {
        "name": "理论研究组",
        "supervisor_prompt": "你是理论研究组的负责人，协调量子理论和数学物理研究。",
        "workers": [
          {
            "name": "量子力学专家",
            "role": "理论物理学家",
            "system_prompt": "你是量子力学专家，专注于量子理论基础研究。"
          },
          {
            "name": "数学物理专家",
            "role": "数学物理学家",
            "system_prompt": "你是数学物理专家，专注于量子力学的数学框架。"
          }
        ]
      },
      {
        "name": "应用研究组",
        "supervisor_prompt": "你是应用研究组的负责人，协调量子计算和量子通信研究。",
        "workers": [
          {
            "name": "量子计算专家",
            "role": "量子计算研究员",
            "system_prompt": "你是量子计算专家，专注于量子算法和量子计算机研究。"
          },
          {
            "name": "量子通信专家",
            "role": "量子通信研究员",
            "system_prompt": "你是量子通信专家，专注于量子密钥分发和量子网络研究。"
          }
        ]
      }
    ]
  }'
```

返回示例：
```json
{
  "success": true,
  "data": {
    "id": "838d04ad-3422-4f39-a2e2-bd6c2ec4441e",
    "name": "量子力学研究团队",
    ...
  }
}
```

记录返回的 `id`，后续测试需要使用。

---

## 四、运行流式测试

### 4.1 安装测试依赖

```bash
pip3 install requests
```

### 4.2 运行测试脚本

**方式 A: 自动获取第一个层级团队**

```bash
python3 test_stream.py "请用100字解释量子纠缠"
```

**方式 B: 指定层级团队 ID**

```bash
python3 test_stream.py --hierarchy=838d04ad-3422-4f39-a2e2-bd6c2ec4441e "请用100字解释量子纠缠"
```

**方式 C: 指定 API 地址 (远程访问)**

```bash
python3 test_stream.py --api=http://your-ec2-ip:18080 "请用100字解释量子纠缠"
```

### 4.3 预期输出

```
╔══════════════════════════════════════════════════════════════╗
║       层级多智能体系统 - 流式事件测试                        ║
╚══════════════════════════════════════════════════════════════╝

📊 层级团队结构:
────────────────────────────────────────────────────────────
🏢 量子力学研究团队 (Global Supervisor)
   ├── 👔 理论研究组 (Team Supervisor)
   │      ├── 🔬 量子力学专家 (理论物理学家)
   │      └── 🔬 数学物理专家 (数学物理学家)
   └── 👔 应用研究组 (Team Supervisor)
          ├── 🔬 量子计算专家 (量子计算研究员)
          └── 🔬 量子通信专家 (量子通信研究员)
────────────────────────────────────────────────────────────

📋 共 2 个团队, 4 个成员

============================================================
启动任务: 请用100字解释量子纠缠
============================================================

运行 ID: c9b9955c-50c7-4549-999a-2f58a81c7d5b
状态: pending

开始监听事件流...

[output] [Global Supervisor] 🎯 开始分析任务
[output] [Global Supervisor] 💭 思考中...
[output] [Team: 理论研究组 | Supervisor] 💭 思考中...
[output] [Team: 理论研究组 | Worker: 量子力学专家] 🔬 开始工作
...

============================================================
✅ 执行完成!
============================================================

【最终结果】
量子纠缠是...
```

---

## 五、常用命令

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f api

# 重新构建
docker-compose up -d --build
```

### 数据库管理

```bash
# 连接数据库
docker exec -it hierarchical-agents-mysql mysql -uroot -phierarchical123

# 查看层级团队
SELECT id, name FROM hierarchy_teams;

# 查看运行记录
SELECT id, status, created_at FROM execution_runs ORDER BY created_at DESC LIMIT 10;
```

### 调试

```bash
# 查看 API 容器日志
docker logs -f hierarchical-agents-api

# 进入 API 容器
docker exec -it hierarchical-agents-api /bin/bash

# 检查网络
docker network ls
docker network inspect hierarchical-agents_hierarchical-agents-network
```

---

## 六、故障排查

### 问题 1: 服务启动失败

```bash
# 检查端口占用
sudo netstat -tlnp | grep 18080

# 检查 Docker 日志
docker-compose logs api
```

### 问题 2: 数据库连接失败

```bash
# 等待数据库完全启动
docker-compose logs mysql

# 检查数据库健康状态
docker inspect hierarchical-agents-mysql | grep -A 10 Health
```

### 问题 3: AWS 认证失败

```bash
# 检查 IAM Role (EC2)
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# 检查环境变量
docker exec hierarchical-agents-api env | grep AWS
```

### 问题 4: 测试脚本找不到层级团队

```bash
# 列出所有层级团队
curl -X POST http://localhost:18080/api/v1/hierarchies/list \
  -H "Content-Type: application/json" \
  -d '{"page": 1, "size": 10}'
```

---

## 七、生产环境建议

1. **使用 IAM Role** - 避免在服务器上存储凭证
2. **配置 HTTPS** - 使用 Nginx + Let's Encrypt
3. **设置资源限制** - 在 docker-compose.yml 中配置内存和 CPU 限制
4. **启用日志轮转** - 防止日志文件过大
5. **配置监控** - 使用 CloudWatch 或 Prometheus
6. **定期备份数据库** - 设置 MySQL 自动备份

---

## 八、相关文档

- [完整部署指南](EC2_DEPLOYMENT_GUIDE.md)
- [认证配置指南](AUTHENTICATION_GUIDE.md)
- [API 参考文档](API_REFERENCE.md)
- [配置说明](CONFIGURATION.md)
