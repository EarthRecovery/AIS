# Target

### Persona-based Conversational Agents 人格化对话智能体 (or named project AIS)

### target

This project focuses on persona-grounded dialogue agents with persistent character traits.
We aim to build an agent that maintains long-term memory and persona consistency, generates character-conditioned dialogue, and supports tool invocation and multi-modal actions, such as Live2D-based avatar behaviors, during interactive sessions.

Additionally, the agent is designed to adapt its behaviors and personality traits through ongoing dialogue, enabling controlled and experience-driven character evolution while preserving core persona constraints.

本项目聚焦于具有人格设定约束的对话智能体，强调持久且一致的角色特征。
我们的目标是构建一个能够维持长期记忆与人格一致性的智能体，使其能够生成受角色条件约束的对话内容，并在交互过程中支持工具调用与多模态动作，例如基于 Live2D 的虚拟形象行为。

此外，智能体将能够基于持续的对话交互对其行为模式与性格特征进行调整，在保持核心人格设定不变的前提下，实现可控的人格演化

### framework

backend: FastAPI + async SQLAlchemy + Alembic, layered routers/services/models under `app/`; LangChain/LangGraph-based RAG with Chroma in `app/rag`; JWT auth helpers in `app/security`.

frontend: Vite + Vue 3 + Pinia + Naive UI (`frontend/`), using Axios to call the FastAPI backend.

agent: gpt-4.1 + RAG + langchain/langgraph

### features: 功能特性
1. Agent Invocation and Conversational Interaction
智能体调用与多轮对话交互
2. Streaming Output of Final Responses
最终回复的实时流式输出
3. End-to-End Backend and Frontend Deployment
端到端的前后端一体化部署
4. RAG for long-term memory
基于RAG的长期记忆机制
5. Persistent data storage
对话记录与智能体状态的持久化数据存储

### future plans: 未来规划
1. Security and Safety Validation
安全性与可靠性校验机制
2. Advanced Prompt Engineering for Persona Consistency and Control
用于人格一致性与可控性的高级 Prompt 工程
3. Multi-modal Actions and Live2D Avatar Integration
多模态动作支持与 Live2D 虚拟形象集成
4. more tool calls (like internet searching)
更丰富的工具调用能力（如互联网搜索等）

website: http://18.170.57.90:5173/