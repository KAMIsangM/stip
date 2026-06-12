# TECH-001: SRS/HLD 冲突统一与技术锁定

## 1. Meta
| Key | Value |
| :--- | :--- |
| Owner | @dev |
| Status | Done |
| Due | 2026-06-12 |

## 2. Intent
- **Goal:** 统一 SRS 与 HLD 在主键类型、图存储方案、关系类型 enum 上的冲突，作为 MVP 编码唯一依据。
- **Context (optional, ≤3 bullets):**
  - SRS §3.6.1 使用 UUID 字符串主键；HLD §3.2 使用 INTEGER AUTO_INCREMENT
  - SRS §5.2 描述「图数据库 API」；HLD §3.1 明确关系表 + NetworkX
  - SRS 关系类型为前驱后继/包含/因果；HLD 仅 prerequisite/related
- **NOT Doing:**
  1. Neo4j / 图数据库引入
  2. UUID 主键迁移方案（MVP 不采用）
  3. 用户/学习记录实体表（MVP 简化为 courses.status + 本地 JSON）

## 3. Tech Lock-in
| 决策项 | 锁定值 | 依据 |
| :--- | :--- | :--- |
| 主键类型 | INTEGER AUTO_INCREMENT | HLD §3.2；SQLite/MySQL 一致、ORM 简单 |
| 图存储 | MySQL/SQLite 关系表 + NetworkX 内存计算 | HLD §3.1；单课 ≤1000 节点满足 SRS §4.1 |
| 关系类型 enum | `prerequisite` / `contains` / `causal` / `related` | 扩展 HLD 至 SRS 四种语义 |
| SRS 图数据库表述 | 修正为「关系型表存储 + NetworkX 图计算 API」 | 以 HLD 为准，避免误引 Neo4j |

## 4. 关系类型映射
| enum 值 | SRS 中文 | 语义 | 有向性 |
| :--- | :--- | :--- | :--- |
| `prerequisite` | 前驱后继 | 学习顺序：source 为 target 的前置知识 | 有向 |
| `contains` | 包含 | 层级包含：source 包含 target | 有向 |
| `causal` | 因果 | 因果依赖：source 导致/影响 target | 有向 |
| `related` | 关联 | 弱关联，无严格顺序 | 无向（存为 source→target） |

## 5. Data Schema（MVP 锁定）
- 表 `courses` / `chapters` / `knowledge_nodes` / `knowledge_edges` / `content_modules` / `generation_progress`
- 所有 PK/FK：`INTEGER`，见 HLD §3.2 与 `backend/alembic/versions/001_initial_schema.py`
- `knowledge_edges.relation_type`：`VARCHAR(20) NOT NULL`，CHECK 约束四 enum 值

## 6. API 类型约定
- REST 响应中 ID 字段类型：`integer`（OpenAPI schema）
- 前端 TypeScript：`number`（非 string UUID）

## 7. DoD (Definition of Done)
- [x] 本文档发布，团队以 HLD 表结构 + 本文 enum 扩展为准
- [x] ORM 模型与 Alembic 迁移使用 INTEGER 主键
- [x] `RelationType` enum 含四种值
- [x] config.yaml 不含图数据库配置项
