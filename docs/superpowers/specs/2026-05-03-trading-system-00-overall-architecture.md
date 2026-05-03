# 个股+板块共振右侧交易系统 - 总体架构设计

## 系统概述

本系统基于 OpenClaw Skill 架构，实现一个完整的"个股+板块共振右侧交易"量化交易系统。系统采用分层设计，从数据获取、信号分析、持仓跟踪到策略自我进化，形成完整的交易闭环。

## 核心设计原则

1. **分层解耦**: 每层 Skill 独立运行，通过标准化 JSON 接口通信
2. **公开 Skill 优先**: 优先复用公开 Skill，减少重复开发
3. **用户审核机制**: 所有交易信号需用户确认后执行
4. **自我进化**: 通过交易日志记录和策略评估，动态适应市场风格切换

## 系统架构图

```mermaid
graph TB
    subgraph L1["Layer 1: 编排层"]
        A[trading-system-orchestrator<br/>交易编排器]
    end
    
    subgraph L2["Layer 2: 分析层"]
        B[market-environment-analyzer<br/>大盘环境判断]
        C[sector-resonance-analyzer<br/>板块共振分析]
        D[stock-right-pattern-screener<br/>个股右侧筛选]
        E[position-tracker<br/>持仓跟踪管理]
    end
    
    subgraph L3["Layer 3: 数据获取层"]
        F[tushare-data-fetcher<br/>Tushare数据接口]
        G[eastmoney-sector-scraper<br/>东方财富板块爬取]
        H[web-scraper<br/>通用网页爬取-公开]
        I[data-parser<br/>数据解析-公开]
        M[stock-kline-fetcher<br/>个股K线数据]
    end
    
    subgraph L4["Layer 4: 记忆与进化层"]
        J[trade-journal<br/>交易日志记录]
        K[strategy-reviewer<br/>策略效果评估]
        L[adaptive-strategy-tuner<br/>策略参数自适应]
    end
    
    A --> B
    A --> C
    A --> D
    A --> E
    A --> J
    
    B --> F
    B --> H
    C --> G
    C --> I
    D --> F
    D --> M
    D --> H
    E --> F
    E --> M
    E --> H
    
    J --> K
    K --> L
    L -.参数更新.-> B
    L -.参数更新.-> C
    L -.参数更新.-> D
    
    style L1 fill:#e1f5fe
    style L2 fill:#f3e5f5
    style L3 fill:#e8f5e9
    style L4 fill:#fff3e0
```

## 分层说明

| 层级 | 职责 | Skill 类型 |
|------|------|-----------|
| Layer 1 | 编排整个交易流程，协调各层 Skill | 全部自建 |
| Layer 2 | 核心交易逻辑：大盘判断、板块分析、个股筛选、持仓跟踪 | 全部自建 |
| Layer 3 | 数据获取：API 接口、网页爬取、数据解析、K线数据 | 公开 Skill 优先 + 按需自建 |
| Layer 4 | 记忆与进化：交易日志、策略评估、参数自适应 | 全部自建 |

## 数据流总览

```mermaid
sequenceDiagram
    participant User as 用户
    participant Orch as Orchestrator
    participant L2 as 分析层 Skills
    participant L3 as 数据层 Skills
    participant L4 as 进化层 Skills
    participant Storage as 数据存储
    
    User->>Orch: 触发交易分析
    Orch->>L3: 获取大盘数据
    L3-->>Orch: 大盘数据
    Orch->>L2: 大盘环境判断
    L2-->>Orch: 可交易: true/false
    
    alt 不可交易
        Orch-->>User: 今日不宜交易
    else 可交易
        Orch->>L3: 获取板块数据
        L3-->>Orch: 板块数据
        Orch->>L2: 板块共振分析
        L2-->>Orch: 强势板块列表
        
        Orch->>L3: 获取个股数据
        L3-->>Orch: 个股数据
        Orch->>L2: 个股右侧筛选
        L2-->>Orch: 候选标的列表
        
        Orch-->>User: 候选标的 + 信号详情
        User->>Orch: 审核确认买入
        
        Orch->>L4: 记录交易日志
        L4->>Storage: 保存交易记录
        Orch->>L2: 开始持仓跟踪
        
        Note over L4,Storage: 定期策略评估与参数调整
    end
```

## 文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 总体架构 | `00-overall-architecture.md` | 本文档 |
| Layer 1 编排层 | `01-layer1-orchestrator.md` | 交易编排器设计 |
| Layer 2 分析层 | `02-layer2-analyzers.md` | 大盘/板块/个股/持仓分析器设计 |
| Layer 3 数据层 | `03-layer3-data-fetchers.md` | 数据获取 Skill 设计 |
| Layer 4 进化层 | `04-layer4-evolution.md` | 交易日志/策略评估/参数自适应设计 |
| 数据格式规范 | `05-data-schema.md` | 统一 JSON Schema 定义 |
| Demo 运行指南 | `06-demo-run-guide.md` | 以半导体板块为例的完整运行流程 |
