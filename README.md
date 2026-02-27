# OpenManus-GUI

基于 [OpenManus](https://github.com/FoundationAgents/OpenManus) 改进的通用浏览器自动化智能体，专注于解决动态网页交互与复杂推理任务。

## 项目简介

本项目在 OpenManus 基础上进行了多项优化，增强了其处理复杂网页任务的能力：

- **GUI 增强交互**：支持图形界面交互，提升用户体验
- **多模型支持**：集成通义千问（Qwen-Max/VL-Plus）、GPT、Claude 等多种大模型
- **中文搜索优化**：默认使用百度搜索，优化中文场景下的搜索效果
- **安全沙箱集成**：集成 Daytona 沙箱环境，保障代码执行安全
- **反检测机制**：添加浏览器反检测参数，提升自动化成功率
- **MCP 协议支持**：支持 MCP 协议，可扩展更多工具

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    Manus Agent                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Planner    │→ │  Executor   │→ │  Reviewer   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ Browser Agent │  │ SWE Agent     │  │ Tool Agent    │
│ (Playwright)  │  │ (代码开发)    │  │ (MCP/搜索)    │
└───────────────┘  └───────────────┘  └───────────────┘
        │                                         
        ▼                                         
┌───────────────┐                          
│ Daytona       │ ← 安全沙箱执行 Python 代码
│ Sandbox       │                          
└───────────────┘                          
```

## 核心特性

### 1. ReAct 分层状态机
- **Planner**：任务规划与拆解
- **Executor**：执行具体操作
- **Reviewer**：结果审查与失败重试

### 2. Daytona 安全沙箱
- 网络隔离与资源限制
- 防止恶意代码执行
- 支持 Python 脚本安全运行

### 3. GUI-Plus 元素定位
- DOM 语义解析 + Vision 感知双通道
- 元素定位成功率大幅提升
- 解决动态网页、JS 控件定位难题

### 4. 多模型集成
- 通义千问（Qwen-Max/VL-Plus）
- OpenAI GPT-4o
- Anthropic Claude
- Google Gemini
- 支持 function calling

## 安装部署

### 环境要求
- Python 3.12+
- Playwright
- API Key（通义千问/GPT/Claude 等）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/Ding-god/OpenManus-gui.git
cd OpenManus-gui

# 2. 创建虚拟环境
uv venv --python 3.12
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. 安装依赖
uv pip install -r requirements.txt

# 4. 安装浏览器
playwright install

# 5. 配置 API Key
cp config/config.example.toml config/config.toml
# 编辑 config/config.toml 添加你的 API Key
```

### 配置说明

编辑 `config/config.toml`：

```toml
[llm]
api_type = "openai"
model = "qwen-max"
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key = "your-dashscope-api-key"

[llm.vision]
model = "qwen-vl-plus"

[search]
engine = "baidu"
lang = "zh"
country = "cn"

[daytona]
daytona_api_key = "your-daytona-api-key"
```

## 使用方法

### 命令行交互

```bash
python main.py
```

### MCP 工具版本

```bash
python run_mcp.py
```

### 多 Agent 版本

```bash
python run_flow.py
```

## 项目结构

```
OpenManus-gui/
├── app/
│   ├── agent/           # Agent 实现
│   │   ├── browser.py   # 浏览器自动化 Agent
│   │   ├── manus.py     # 主 Agent
│   │   ├── mcp.py       # MCP 协议支持
│   │   └── react.py     # ReAct 模式
│   ├── tool/            # 工具集
│   │   ├── browser_use_tool.py
│   │   ├── search/      # 搜索工具
│   │   └── sandbox/    # 沙箱工具
│   └── sandbox/         # Daytona 沙箱
├── config/              # 配置文件
├── examples/           # 使用示例
├── static/             # 静态资源
├── templates/          # HTML 模板
└── logs/               # 运行日志
```

## 技术栈

- **语言**: Python
- **LLM**: 通义千问、GPT-4o、Claude、Gemini
- **浏览器**: Playwright
- **框架**: LangChain、ReAct
- **沙箱**: Daytona
- **搜索**: 百度、Google、DuckDuckGo

## 应用场景

- 机票/酒店预订自动化
- 跨平台价格比价
- 竞品分析数据采集
- 表单自动填写
- 网页内容监控
- 自动化测试

## 注意事项

1. 请遵守目标网站的服务条款
2. 敏感操作建议在沙箱环境中运行
3. 部分网站可能有反爬机制，需合理设置请求间隔

## License

MIT License
