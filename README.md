# Target

### Title

ACG-Knowledge-Explorer: A conversational AI agent that answers questions about anime worlds, characters, relationships, and storylines in English

### short-term target

Q&A(Easiest way)

reasoning

### Long-term target

multiple input(Website, image...)

Multiple agent(draw graph/tables/search from website...)

real-time conversation

Chinese support

### Framework

#### LLM/fineturn



#### RAG/Neo4j



#### Server/API



#### Frontend



### Framework & Stack

#### LLM / finetune and reasoning

HuggingFace Transformers + PEFT（LoRA/QLoRA）/ TRL（SFT、PPO/GRPO）

**vLLM**（PagedAttention、continuous batching）

bitsandbytes（NF4/FP4）/ AWQ / GPTQ / EXL2

vLLM OpenAI-compatible server

#### RAG / Neo4j

Neo4j

**Spring AI** 

Postgres + **pgvector**

先向量检索（Top-k）→ 图谱查询（限定实体/关系）→ 合并上下文 → 重排 → 生成（带引用）

#### Server / API

FastAPI

**Spring Boot + Spring AI**

Redis

Docker Compose +  **K8s**



### 路线

**1. RAG/知识图谱**

- 建立向量库（pgvector/Qdrant）+ Neo4j 图谱 → 搭一个基本问答系统。
- 用现成的通用 LLM（如 LLaMA/Qwen/Mistral）调用 RAG pipeline，立刻能验证效果



2. 模型微调

3. 后端开发
4. 前端开发

### **第 1 阶段：基础打通（2–3 周）**

- 数据预处理 → pgvector & Neo4j 入库。
- FastAPI + Spring AI + 前端（Streamlit/Next.js）打通最小对话链路。
- 本地 4070Ti 部署量化模型，跑通小规模对话。

### **第 2 阶段：模型微调（2–3 周）**

- 在服务器（4×A100-80G）做一次 SFT 或 LoRA/QLoRA。
- 尝试 adapter 部署在本地（量化）和服务器（全精度）。
- 基本评估：模型是否比基础版更符合领域任务。

### **第 3 阶段：推理优化 + Agent（1–2 周）**

- vLLM 部署（continuous batching + KV cache）。
- 增加 Redis 缓存、请求限流。
- Agent 工具调用（Neo4j 查询、向量检索、函数调用）。

### **第 4 阶段：打磨与展示（1–2 周）**

- 前端 UI 优化（消息流式、引用文档展示）。
- 加入最小评测 pipeline（retrieval precision/recall、输出参考率）。
- 完成一个可 demo 的 end-to-end 系统。