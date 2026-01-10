# GAAP 智能 Stop 处理与消息压缩设计

## 概述

GAAP 提供三种 LLM 模式来处理 Stop 事件通知：

| 模式 | 描述 | API 调用 | 成本 |
|------|------|----------|------|
| `none` | 规则过滤 + 纯文本 | 无 | 免费 |
| `smart` | 规则过滤 + LLM 压缩 | 仅在需要时 | 低 |
| `compress_all` | 全量 LLM 压缩 | 每次 Stop | 高 |

## 工作流程

```
Stop 事件触发
    ↓
[llm_mode = none]
    ├── 规则检测是否需要用户输入
    ├── 需要 → 发送纯文本消息
    └── 不需要 → 跳过

[llm_mode = smart]
    ├── 规则检测是否需要用户输入
    ├── 需要 → LLM 压缩 → 发送
    └── 不需要 → 跳过 (节省 tokens)

[llm_mode = compress_all]
    └── LLM 压缩 → 发送 (每次都调用)
```

## 配置文件

`.claude/gaap.json`:

### none 模式 (默认)
```json
{
  "llm_mode": "none"
}
```

### smart 模式
```json
{
  "llm_mode": "smart",
  "compress": {
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-haiku-20240307",
    "api_key": "$GAAP_API_KEY",
    "lang": "zh"
  }
}
```

### compress_all 模式
```json
{
  "llm_mode": "compress_all",
  "compress": {
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-haiku-20240307",
    "api_key": "$GAAP_API_KEY",
    "lang": "zh"
  }
}
```

## 规则检测逻辑

当 `llm_mode` 为 `none` 或 `smart` 时，使用以下规则检测是否需要用户输入：

```bash
# 检测问号
\? | ？

# 中文关键词
要不要|是否|可以吗|怎么样|如何|什么|哪个|吗$|呢$|确认|选择|输入|告诉我

# 英文关键词
need|want|should|would you|can you|please|let me know|confirm|choose|select|prefer|approve|accept|reject
```

## 支持的 LLM Provider

| Provider | base_url | model 示例 |
|----------|----------|------------|
| Anthropic | (默认) | claude-3-haiku-20240307 |
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| GLM | https://open.bigmodel.cn/api/paas/v4 | glm-4-flash |
| Ollama | http://localhost:11434/v1 | llama3.2 |

## 配置示例

### Anthropic Haiku (推荐)
```json
{
  "llm_mode": "smart",
  "compress": {
    "base_url": "https://api.anthropic.com",
    "model": "claude-3-haiku-20240307",
    "api_key": "$GAAP_API_KEY",
    "lang": "zh"
  }
}
```

### DeepSeek
```json
{
  "llm_mode": "smart",
  "compress": {
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "api_key": "$GAAP_API_KEY",
    "lang": "zh"
  }
}
```

### GLM (智谱)
```json
{
  "llm_mode": "smart",
  "compress": {
    "base_url": "https://open.bigmodel.cn/api/paas/v4",
    "model": "glm-4-flash",
    "api_key": "$GAAP_API_KEY",
    "lang": "zh"
  }
}
```

### 本地 Ollama
```json
{
  "llm_mode": "compress_all",
  "compress": {
    "base_url": "http://localhost:11434/v1",
    "model": "llama3.2",
    "lang": "en"
  }
}
```

## Fallback 策略

```
尝试 LLM 压缩
    ↓
成功 → 发送压缩消息
失败 → 发送纯文本消息 (fallback)
```

失败情况：
- API key 未配置
- 网络错误
- API 返回错误
- 超时 (5秒)

## 压缩 Prompt

```
中文: 将消息压缩成简短口语化的中文，去除所有Markdown格式。保留核心信息，最多100字。只输出压缩结果。

English: Compress the message into concise conversational English. Remove all Markdown formatting. Keep core info only, max 50 words. Output only the result.
```

## 成本估算

以 Claude 3 Haiku 为例 ($0.25/1M input tokens):

| 模式 | 场景 | 每日调用 | 每月成本 |
|------|------|----------|----------|
| none | - | 0 | $0 |
| smart | 50% 需要通知 | ~50 | ~$0.01 |
| compress_all | 每次 Stop | ~100 | ~$0.02 |

*假设每条消息 ~500 tokens，每天 100 次 Stop 事件*
