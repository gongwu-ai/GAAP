# GAAP 消息压缩功能设计

## 需求

飞书不渲染 Markdown，原始消息可能包含：
- 代码块 \`\`\`
- 表格 |---|
- 加粗 **text**
- 列表 - item

用 fast model 压缩成人类聊天风格的消息。

## 配置文件

`~/.claude/gaap.json`:

```json
{
  "message_format": "compressed",
  "compress": {
    "provider": "anthropic",
    "model": "claude-3-haiku-20240307",
    "api_key": "sk-xxx",
    "base_url": null
  }
}
```

## 支持的 Provider

| Provider | base_url | model 示例 |
|----------|----------|------------|
| anthropic | (默认) | claude-3-haiku-20240307 |
| openai | https://api.openai.com/v1 | gpt-4o-mini |
| deepseek | https://api.deepseek.com/v1 | deepseek-chat |
| glm | https://open.bigmodel.cn/api/paas/v4 | glm-4-flash |
| ollama | http://localhost:11434/v1 | llama3.2 |

## 配置示例

### Anthropic Haiku (推荐)
```json
{
  "message_format": "compressed",
  "compress": {
    "provider": "anthropic",
    "model": "claude-3-haiku-20240307",
    "api_key": "sk-ant-xxx"
  }
}
```

### DeepSeek
```json
{
  "message_format": "compressed",
  "compress": {
    "provider": "openai",
    "model": "deepseek-chat",
    "api_key": "sk-xxx",
    "base_url": "https://api.deepseek.com/v1"
  }
}
```

### GLM (智谱)
```json
{
  "message_format": "compressed",
  "compress": {
    "provider": "openai",
    "model": "glm-4-flash",
    "api_key": "xxx.xxx",
    "base_url": "https://open.bigmodel.cn/api/paas/v4"
  }
}
```

### 本地 Ollama
```json
{
  "message_format": "compressed",
  "compress": {
    "provider": "openai",
    "model": "llama3.2",
    "base_url": "http://localhost:11434/v1"
  }
}
```

## Fallback 策略

```
尝试压缩
    ↓
成功 → 发送压缩消息
失败 → 发送全量消息 (fallback)
```

失败情况：
- API key 未配置
- 网络错误
- API 返回错误
- 超时 (5秒)

## 实现方案

### 方案 A: Claude API 直接调用

```bash
# 需要 ANTHROPIC_API_KEY
curl -X POST "https://api.anthropic.com/v1/messages" \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-3-haiku-20240307",
    "max_tokens": 200,
    "messages": [{"role": "user", "content": "压缩这段消息成简短的聊天风格..."}]
  }'
```

**优点**: 简单直接
**缺点**: 需要用户配置 API key，有成本

### 方案 B: Prompt-based Hook

使用 Claude Code 的 `type: "prompt"` hook：

```json
{
  "type": "prompt",
  "prompt": "将以下消息压缩成简短的聊天风格，去除 Markdown 格式：\n$MESSAGE"
}
```

**优点**: 不需要额外 API key
**缺点**: 不确定是否支持发送到外部服务

### 方案 C: Python 脚本 + 本地模型

使用 ollama 或其他本地模型压缩。

**优点**: 无成本，离线可用
**缺点**: 需要安装额外依赖

## 推荐

**方案 A** - 最简单，Haiku 很便宜 ($0.25/1M input tokens)

用户配置：
1. 设置 `ANTHROPIC_API_KEY` 环境变量
2. 在 `~/.claude/gaap.json` 设置 `"message_format": "compressed"`

## 压缩 Prompt

```
你是一个消息压缩助手。将以下 Claude Code 的回复压缩成简短的聊天消息：
- 去除所有 Markdown 格式（代码块、表格、加粗等）
- 保留核心信息
- 用口语化的中文表达
- 最多 100 字

原始消息：
{message}

压缩后：
```
