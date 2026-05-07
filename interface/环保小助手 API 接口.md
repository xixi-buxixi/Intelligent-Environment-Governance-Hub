# 环保小助手 API 接口文档

## 概述

环保小助手是基于 RAG（检索增强生成）和 Tool（工具调用）技术的智能问答系统，能够回答环保相关问题，并可调用数据工具获取实时环境数据。

**基础URL**: `http://localhost:8080`

**认证方式**: Bearer Token（JWT）

---

## 接口列表

### 1. 对话接口

**接口描述**: 发送消息与环保小助手进行对话

**请求URL**: `/api/assistant/chat`

**请求方式**: `POST`

**Content-Type**: `application/json`

#### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | String | 是 | Bearer Token，格式：`Bearer {token}` |
| Content-Type | String | 是 | 固定值：`application/json` |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| message | String | 是 | 用户输入的问题内容 |
| sessionId | String | 否 | 会话ID，用于保持多轮对话上下文，首次对话可不传 |

#### 请求示例

```json
{
    "message": "什么是PM2.5？有哪些危害？",
    "sessionId": "session_1710489600000_abc123def"
}
```

#### 响应参数

| 参数名 | 类型 | 说明 |
|--------|------|------|
| code | Integer | 状态码，200表示成功 |
| message | String | 响应消息 |
| data | Object | 响应数据 |
| data.answer | String | 助手的回答内容 |
| data.toolCalls | Array\<String\> | 调用的工具名称列表 |
| data.references | Array\<String\> | 参考来源列表（RAG检索的相关文档片段） |
| data.sessionId | String | 会话ID，用于后续对话 |

#### 响应示例

**成功响应**:
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "answer": "PM2.5是指空气中直径小于或等于2.5微米的颗粒物...\n\n主要危害包括：\n1. 呼吸系统疾病\n2. 心血管疾病\n3. 降低能见度",
        "toolCalls": ["knowledge_search"],
        "references": [
            "《环境空气质量标准》(GB 3095-2012)",
            "《大气污染防治法》第十二条"
        ],
        "sessionId": "session_1710489600000_abc123def"
    }
}
```

**错误响应**:
```json
{
    "code": 401,
    "message": "未授权，请先登录",
    "data": null
}
```

---

### 2. 获取会话历史

**接口描述**: 获取当前会话的对话历史记录

**请求URL**: `/api/assistant/history`

**请求方式**: `GET`

#### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | String | 是 | Bearer Token |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| sessionId | String | 是 | 会话ID |

#### 响应示例

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "sessionId": "session_1710489600000_abc123def",
        "messages": [
            {
                "role": "user",
                "content": "什么是PM2.5？",
                "createTime": "2024-03-15T10:30:00"
            },
            {
                "role": "assistant",
                "content": "PM2.5是指空气中直径小于或等于2.5微米的颗粒物...",
                "createTime": "2024-03-15T10:30:05"
            }
        ],
        "total": 2
    }
}
```

---

### 3. 清除会话

**接口描述**: 清除当前会话，开始新对话

**请求URL**: `/api/assistant/clear`

**请求方式**: `DELETE`

#### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | String | 是 | Bearer Token |

#### 请求参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| sessionId | String | 是 | 要清除的会话ID |

#### 响应示例

```json
{
    "code": 200,
    "message": "会话已清除",
    "data": null
}
```

---

### 4. 获取可用工具列表

**接口描述**: 获取环保小助手可调用的工具列表

**请求URL**: `/api/assistant/tools`

**请求方式**: `GET`

#### 请求头

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | String | 是 | Bearer Token |

#### 响应示例

```json
{
    "code": 200,
    "message": "success",
    "data": {
        "tools": [
            {
                "name": "knowledge_search",
                "description": "搜索环保知识库，检索相关法规、标准、政策文档",
                "parameters": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                }
            },
            {
                "name": "air_quality_query",
                "description": "查询指定城市的实时空气质量数据",
                "parameters": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                }
            },
            {
                "name": "weather_query",
                "description": "查询指定城市的天气信息",
                "parameters": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    }
                }
            },
            {
                "name": "data_statistics",
                "description": "获取环境数据的统计分析结果",
                "parameters": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "dataType": {
                        "type": "string",
                        "description": "数据类型：AQI/PM25/PM10等"
                    },
                    "period": {
                        "type": "string",
                        "description": "统计周期：day/week/month"
                    }
                }
            }
        ]
    }
}
```

---

## 工具调用说明

环保小助手支持以下工具：

### 1. knowledge_search（知识检索）

**用途**: 从环保知识库中检索相关文档

**触发场景**: 用户询问环保法规、标准、政策等问题时

**参数**:
- `query`: 搜索关键词

**示例调用**:
```json
{
    "tool": "knowledge_search",
    "parameters": {
        "query": "大气污染防治法 排放标准"
    }
}
```

### 2. air_quality_query（空气质量查询）

**用途**: 查询实时空气质量数据

**触发场景**: 用户询问某城市当前空气质量时

**参数**:
- `city`: 城市名称

**示例调用**:
```json
{
    "tool": "air_quality_query",
    "parameters": {
        "city": "北京"
    }
}
```

### 3. weather_query（天气查询）

**用途**: 查询天气信息

**触发场景**: 用户询问某城市天气情况时

**参数**:
- `city`: 城市名称

### 4. data_statistics（数据统计）

**用途**: 获取环境数据的统计分析

**触发场景**: 用户需要环境数据趋势分析时

**参数**:
- `city`: 城市名称
- `dataType`: 数据类型（AQI/PM25/PM10等）
- `period`: 统计周期（day/week/month）

---

## 错误码说明

| 错误码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权，请先登录 |
| 403 | 权限不足 |
| 429 | 请求过于频繁，请稍后重试 |
| 500 | 服务器内部错误 |

---

## 后端实现建议

### 1. 技术架构

```
用户请求 → Spring Boot Controller → AI Service
                                    ↓
                    ┌───────────────┴───────────────┐
                    ↓                               ↓
              RAG Service                    Tool Service
                    ↓                               ↓
            向量数据库检索                   外部API调用
            (如Milvus/Pinecone)            (天气/空气质量API)
                    ↓                               ↓
                    └───────────────┬───────────────┘
                                    ↓
                            LLM (Claude/GPT)
                                    ↓
                              生成回答
```

### 2. 核心类设计

```java
// Controller
@RestController
@RequestMapping("/api/assistant")
public class AssistantController {

    @PostMapping("/chat")
    public Result<ChatResponse> chat(@RequestBody ChatRequest request) {
        // 处理对话请求
    }

    @GetMapping("/history")
    public Result<HistoryResponse> getHistory(@RequestParam String sessionId) {
        // 获取历史记录
    }

    @DeleteMapping("/clear")
    public Result<Void> clearSession(@RequestParam String sessionId) {
        // 清除会话
    }

    @GetMapping("/tools")
    public Result<ToolsResponse> getTools() {
        // 获取工具列表
    }
}

// Service
@Service
public class AssistantService {

    // 处理对话
    public ChatResponse chat(String message, String sessionId) {
        // 1. 获取或创建会话上下文
        // 2. 判断是否需要工具调用
        // 3. 执行RAG检索（如需要）
        // 4. 调用LLM生成回答
        // 5. 返回结果
    }
}

// 工具接口
public interface Tool {
    String getName();
    String getDescription();
    Map<String, Object> getParameters();
    ToolResult execute(Map<String, Object> params);
}

// 具体工具实现
@Component
public class KnowledgeSearchTool implements Tool {
    // 实现知识检索
}

@Component
public class AirQualityQueryTool implements Tool {
    // 实现空气质量查询
}
```

### 3. RAG实现要点

1. **文档预处理**: 将环保法规、标准等文档切分成合适大小的片段
2. **向量化**: 使用Embedding模型将文档片段转为向量
3. **存储**: 将向量存入向量数据库
4. **检索**: 根据用户问题检索最相关的文档片段
5. **生成**: 将检索结果作为上下文，让LLM生成回答

### 4. 数据库表设计

```sql
-- 会话表
CREATE TABLE chat_session (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id BIGINT NOT NULL,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 消息记录表
CREATE TABLE chat_message (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL COMMENT 'user/assistant',
    content TEXT NOT NULL,
    tool_calls JSON COMMENT '调用的工具列表',
    references JSON COMMENT '参考来源',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_session_id (session_id)
);

-- 知识库文档表
CREATE TABLE knowledge_document (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    source VARCHAR(255) COMMENT '来源',
    category VARCHAR(50) COMMENT '分类：法规/标准/政策等',
    vector_id VARCHAR(100) COMMENT '向量数据库中的ID',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 前端集成说明

前端页面已创建于 `front-end/assistant.html`，主要功能：

1. **对话界面**: 类似ChatGPT的聊天界面
2. **消息展示**: 支持用户消息和助手消息，支持Markdown格式
3. **工具调用显示**: 显示助手调用了哪些工具
4. **参考来源展示**: 显示RAG检索的参考文档来源
5. **快捷问题**: 提供常见问题快速提问
6. **会话管理**: 自动管理会话ID

### 使用方式

1. 用户登录后，从首页点击"环保小助手"卡片进入
2. 输入问题或点击快捷问题发送
3. 等待助手返回回答

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2024-03-15 | 初始版本，支持基础对话和工具调用 |