  ------------------ ---------------- -------------------
  项目名称           密级             
  智能互动教学平台   仅供收件方查阅   
  项目编号           版本             文档编号
  001                V1.0             Project ID_SD_001
  ------------------ ---------------- -------------------

智能互动教学平台系统概要设计说明书

  -------- -------- ------ ------------
  拟制     任庚辰   日期   2026-06-09
  评审人   刘承远   日期   2026-06-10
  批准     刘承远   日期   2026-06-10
  -------- -------- ------ ------------

**武汉学链科技有限公司**

版权所有 不得复制

Revision Record

修订记录

+-------+------------------+------------------+----------+--------------------+--------+
| Date  | Revision Version | CR ID /Defect ID | Sec No.  | Change Description | Author |
|       |                  |                  |          |                    |        |
| 日期  | 修订版本         | CR/ Defect号     | 修改章节 | 修改描述           | 作者   |
+-------+------------------+------------------+----------+--------------------+--------+
| 06-09 | V1.0             | CR-20250609-001  | ALL      | Init               | 刘承远 |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+
|       |                  |                  |          |                    |        |
+-------+------------------+------------------+----------+--------------------+--------+

**目 录**

1 简介

> [1.1 目的](\l)
>
> [1.2 范围](\l)
>
> [1.2.1软件名称](\l)
>
> [1.2.2 软件功能](\l)
>
> [1.2.3 软件应用](\l)
>
> [1.3 参考资料](\l)

[2 概要设计](\l)

> [2.1 第0层设计描述](\l)
>
> [2.1.1 软件系统上下文定义](\l)
>
> [2.1.2 设计思路](\l)
>
> [2.2 第1层设计描述](\l)
>
> [2.2.1 系统结构](\l)
>
> [2.2.1.1系统结构描述](\l)
>
> [2.2.1.2业务流程说明](\l)
>
> [2.2.2 分解描述](\l)
>
> [2.2.2.1 模块1名](\l)
>
> [2.2.2.1.1 功能一名](\l)
>
> [2.2.2.1.2 功能二名](\l)
>
> [2.2.2.2 模块2名](\l)
>
> [2.2.3 接口描述](\l)
>
> [2.2.3.1 XX接口1](\l)
>
> [2.2.3.2 XX接口2](\l)

[3 数据结构/数据库设计](\l)

> [3.1 概念模型](\l)
>
> [3.2 数据库表设计](\l)
>
> [3.3 存储过程设计](\l)
>
> [3.4 视图设计](\l)
>
> [3.5 触发器设计](\l)
>
> [3.6 函数设计](\l)
>
> [3.7 基础数据配置](\l)

[4 界面设计](\l)

> [4.1 界面1](\l)
>
> [4.2 界面1](\l)

[5 出错处理设计](\l)

**Keywords 关键词：**

智能教学平台；多模态内容生成；知识图谱；LLM

**Abstract 摘 要：**

本文档为智能互动教学平台（Smart Interactive Teaching
Platform）的系统概要设计说明书，描述了平台的总体架构、模块划分、接口设计、数据库设计、界面设计及出错处理策略。平台采用Vue
3 + FastAPI前后端分离架构，通过LLM
Provider抽象层集成多供应商AI能力，以知识图谱驱动课程内容生成，支持6种模态的沉浸式互动教学体验。

**List of abbreviations 缩略语清单：**

  --------------------- ----------------------------------- --------------------------------------------------------------
  Abbreviations缩略语   Full spelling 英文全名              Chinese explanation 中文解释
  MVP                   Minimum Viable Product              最小可行产品，指本平台第一阶段交付的核心功能集。
  LLM                   Large Language Model                大语言模型，如DeepSeek、通义千问等，用于内容生成与知识抽取。
  TTS                   Text-to-Speech                      文本转语音技术，用于生成课程音频旁白。
  ASR                   Automatic Speech Recognition        自动语音识别技术，用于语音输入转文字。
  ORM                   Object-Relational Mapping           对象关系映射
  SPA                   Single Page Application             单页应用
  API                   Application Programming Interface   应用程序接口
  CRUD                  Create, Read, Update, Delete        增删改查
  --------------------- ----------------------------------- --------------------------------------------------------------

# 1 简介

## 1.1 目的

本文档旨在对智能互动教学平台进行概要设计，明确系统的总体架构、模块划分、接口设计、数据库设计及部署方案。文档的预期读者包括项目开发团队、评审人员及相关利益方。

本文档基于《智能互动教学平台软件需求规格说明书》（Project ID:
Proc_RA_002,
V1.0），对MVP阶段（P0优先级）的四大核心功能模块进行概要设计：智能课堂生成（F001）、多模态教学内容生成引擎（F002）、课程知识库与知识图谱管理（F003）以及语音功能集成（F-Voice）。

## 1.2 范围

### 1.2.1 软件名称

智能互动教学平台（Smart Interactive Teaching Platform）

### 1.2.2 软件功能

系统功能结构图如下：

![系统功能结构图](media/image2.png){width="6.041666666666667in"
height="1.9895833333333333in"}

各功能模块概述如下：

\(1\)
**智能课堂生成（F001）：**用户输入学习主题或选择预置课程，系统自动分析并生成结构化课程大纲，每个大纲条目自动编排为互动教学场景。

\(2\)
**多模态教学内容生成引擎（F002）：**基于课程大纲和知识图谱，将课程内容自动转化为沉浸式文本、测验、PPT与旁白、音频课程、思维导图、互动式教材六种以上模态形式。

\(3\)
**课程知识库与知识图谱管理（F003）：**支持知识图谱的构建、存储、可视化展示与编辑。知识图谱以图结构存储，支持前驱后继、包含、因果等多元关系类型。数据来源包括核心预置和AI自动抽取补充。

\(4\)
**语音功能集成（F-Voice）：**支持TTS语音合成（AI教师语音授课）和ASR语音识别（学生语音提问），实现语音驱动的互动教学体验。

### 1.2.3 软件应用

本项目是一个全新的独立项目，旨在构建一个基于多智能体技术的互动教学平台，将传统单向授课转变为沉浸式互动学习体验。平台支持虚拟AI教师实时授课、答疑，并自动生成丰富的多模态互动学习内容。学生可通过自然语言输入学习主题，系统自动生成完整的互动课程内容。

平台的核心价值主张是\"让学习更智能、更互动、更个性\"，致力于搭建一座连接知识与学生的智慧教育桥梁。

MVP阶段面向单用户本地使用场景，采用单机部署模式，通过Web浏览器访问。

## 1.3 参考资料

本设计文档在编制过程中参考了以下标准和文档：

\(1\) GB/T 8567-2006 计算机软件文档编制规范

\(2\) GB/T 11457-2006 信息技术 软件工程术语

\(3\) IEEE 1016-2009 软件设计描述标准

\(4\) 《智能互动教学平台软件需求规格说明书》（Project ID: Proc_RA_002,
V1.0）

\(5\) DeepSeek API 接口文档

\(6\) Vue 3 官方文档 (https://cn.vuejs.org/)

\(7\) FastAPI 官方文档 (https://fastapi.tiangolo.com/)

\(8\) SQLAlchemy 官方文档 (https://docs.sqlalchemy.org/)

# 2 概要设计 

## 2.1 第0层设计描述

### 2.1.1 软件系统上下文定义

智能互动教学平台（Smart Interactive Teaching
Platform）作为一个独立的教学内容生成与消费系统，与外部实体之间的交互关系如下：

用户（学生/教育工作者）：通过Web浏览器访问平台，输入学习主题，获取生成的课程内容并进行互动学习。

LLM服务（DeepSeek/通义千问等）：通过RESTful
API提供课程大纲生成、多模态内容创作、知识点抽取等AI能力。通过Provider抽象层实现多供应商切换。

TTS服务（Edge TTS/阿里云/腾讯云）：通过RESTful
API提供文本转语音能力，用于生成课程音频旁白。

ASR服务（阿里云/腾讯云）：通过WebSocket提供实时语音识别能力，用于语音输入交互。

文件系统：存储课程生成的静态资源文件（HTML课件、音频文件、图片等）。

![01_系统上下文图](media/image3.jpeg){width="5.767361111111111in"
height="3.946527777777778in"}

### 2.1.2 设计思路

（1）架构设计思路：

系统采用前后端分离的分层架构，自上而下分为四层：表示层（Vue 3
SPA）、API网关层（FastAPI REST +
WebSocket）、业务服务层（课程服务/知识图谱服务/内容生成服务/语音服务）、数据层（MySQL/SQLite
+ NetworkX + 文件系统）。

各层之间通过定义良好的接口进行通信：表示层通过HTTP RESTful
API获取数据，通过WebSocket接收实时推送；API网关层负责请求路由和认证（P1阶段实现）；业务服务层封装核心业务逻辑，通过LLM
Provider抽象层统一调用外部AI服务；数据层提供持久化存储和图计算能力。

（2）程序框架与目录结构：

前端采用Vue 3 + TypeScript + Element Plus +
Pinia状态管理，后端采用Python FastAPI + SQLAlchemy
ORM。LLM调用采用适配器模式（Adapter
Pattern），通过统一接口封装不同提供商的API。![02_包图](media/image4.png){width="5.763194444444444in"
height="3.9430555555555555in"}

## 2.2 第1层设计描述

### 2.2.1 系统结构

#### 2.2.1.1 系统结构描述

系统按照功能划分为七大核心模块，各模块之间通过清晰的接口进行协作。系统总体结构如下图所示：

![系统整体架构图](media/image5.png){width="5.748611111111111in"
height="3.227777777777778in"}

#### 2.2.1.2 业务流程说明

系统核心业务流程（课程生成与学习）如下：

步骤1 - 用户输入主题：用户在课程管理页面输入学习主题或选择预置课程。

步骤2 -
知识图谱驱动大纲生成：系统查询知识图谱中相关知识点及其先修关系，通过拓扑排序确定知识点讲授顺序，调用LLM生成结构化课程大纲（含章节划分）。

步骤3 -
多模态内容预生成：基于大纲，逐一生成6种模态的教学内容（沉浸式文本、分段测验、PPT课件、音频旁白、思维导图、互动HTML教材）。生成过程通过WebSocket实时推送进度给前端。

步骤4 -
内容缓存与存储：生成的内容写入MySQL数据库（结构化数据）和文件系统（静态资源），标记课程状态为\"已完成\"。

步骤5 -
课程学习：用户在课程播放器中按章节顺序学习，可使用PPT播放、文本阅读、测验答题、思维导图浏览等多种学习模式。后续访问直接读取缓存，零LLM调用。

步骤6 - PPT导出（可选）：用户可将课程PPT内容导出为.pptx文件下载到本地。

![05_业务流程图](media/image6.png){width="5.763194444444444in"
height="3.9430555555555555in"}

### 2.2.2 分解描述

#### 2.2.2.1 课程管理模块

1、简介

课程管理模块对应需求规格说明书中 F001 智能课堂生成
能力，是平台的核心流程编排模块。负责课程全生命周期管理，承接用户学习主题输入，完成课程大纲生成、教学场景编排、课程状态管控与章节组织，为多模态内容生成提供结构化输入。

2、功能列表

课程基础 CRUD
操作：课程的创建、查询、更新、删除，支持按状态、创建时间筛选排序；

课程大纲生成与管理：基于用户输入主题结合知识图谱生成结构化课程大纲，支持手动调整章节顺序与内容；

课程状态跟踪：维护课程全生命周期状态（草稿 / 生成中 / 已完成 /
失败），实时同步生成进度；

教学场景编排：根据知识点类型（概念型 / 实践型 /
综合型）自动匹配对应教学模态组合，生成标准化教学场景。

##### 2.2.2.1.1 课程创建功能

**1 功能设计描述**

本功能承接用户的学习主题输入，完成课程实体创建、主题解析与结构化大纲生成，是课程生成全流程的入口。

**（1）类**

**1）Course 实体类**

对应数据库 courses 表，封装课程核心属性，包括课程
ID、标题、描述、状态、创建时间、更新时间，作为数据层与业务层的统一传输载体。

**2）Chapter 实体类**

对应数据库 chapters 表，封装章节属性，包括章节 ID、所属课程
ID、标题、排序序号、关联知识点 ID 列表。

**3）CourseController 控制类**

位于 API 网关层，提供课程创建、大纲查询、课程列表获取等 RESTful
接口，负责请求参数校验、响应封装与基础权限校验。

**4）CourseService 业务服务类**

位于业务服务层，封装课程创建、大纲生成核心业务逻辑，调用 LLM Provider
完成主题解析与大纲生成，同步关联知识图谱数据。

**5）CourseRepository 数据访问类**

基于 SQLAlchemy ORM
实现，负责课程与章节数据的数据库持久化操作，提供标准化 CRUD 接口。

**（2）类与类之间关系**

![](media/image7.png){width="5.759027777777778in"
height="4.120138888888889in"}

CourseController 依赖 CourseService，接收前端请求后转发至业务层处理；

CourseService 依赖 CourseRepository 与 LLMProvider，分别完成数据持久化与
AI 能力调用；

Course 与 Chapter 为一对多聚合关系，一门课程包含多个有序章节。

**（3）文件列表**

  ---------------------- ------------ --------------------------------------------- -------------------------------------------
  名称                   类型         存放位置                                      说明
  course.py              Python       backend/app/api/course.py                     后端课程接口控制器，定义课程相关 API 路由
  course_service.py      Python       backend/app/service/course_service.py         课程核心业务逻辑实现类
  course_model.py        Python       backend/app/models/course_model.py            课程与章节实体类定义，SQLAlchemy ORM 映射
  course_repository.py   Python       backend/app/repository/course_repository.py   课程数据访问层，封装数据库操作
  CourseCreate.vue       Vue          frontend/src/views/course/CourseCreate.vue    前端课程创建页面组件
  course.ts              TypeScript   frontend/src/api/course.ts                    前端课程接口请求封装
  ---------------------- ------------ --------------------------------------------- -------------------------------------------

**2 功能实现说明**

用户在前端课程创建页面输入学习主题，提交课程创建请求；

前端调用课程创建 API，将主题参数传递至后端 CourseController；

CourseController 校验参数合法性，调用 CourseService 的课程创建方法；

CourseService 初始化课程实体，状态设为 "生成中"，通过 CourseRepository
持久化到数据库；

CourseService 调用知识图谱服务获取对应领域的知识点与前驱后继关系，结合
LLM Provider 生成符合认知规律的结构化课程大纲；

CourseService 将大纲拆解为有序章节列表，调用 CourseRepository
批量写入章节数据；

CourseService 更新课程状态，将完整课程与大纲数据返回至
CourseController；

CourseController 封装响应结果返回前端，前端跳转至课程详情与生成进度页。

时序图（Sequence Diagram）

![](media/image8.png){width="5.76875in" height="3.48125in"}

协作图（Collaboration Diagram）

![](media/image9.png){width="5.759027777777778in"
height="1.8333333333333333in"}

##### 2.2.2.1.2 课程状态与进度管理功能

**1 功能设计描述**

本功能负责维护课程生成全流程的状态流转，实时同步生成进度，支持异常状态的重试与回滚，保障生成过程的可观测性。

**（1）类**

**1）GenerationProgress 实体类**

对应数据库 generation_progress 表，封装生成进度属性，包括进度
ID、所属课程 ID、状态、当前步骤、总步骤数、错误信息、更新时间。

**2）ProgressService 业务服务类**

负责进度数据的更新、查询与状态流转管控，对接内容生成模块的进度推送，触发
WebSocket 实时通知。

**3）ProgressRepository 数据访问类**

负责生成进度数据的数据库持久化操作。

**（2） 类与类之间关系**

![](media/image10.png){width="5.759027777777778in" height="2.26875in"}

CourseService 依赖 ProgressService，课程创建时同步初始化进度记录；

ProgressService 依赖 ProgressRepository 完成数据持久化；

 Course 与 GenerationProgress
为一对一关联关系，一门课程对应一条生成进度记录。

**（3）文件列表**

  ------------------------ -------- ------------------------------------------------ ----------------------
  名称                     类型     存放位置                                         说明
  progress_model.py        Python   backend/app/models/progress_model.py             生成进度实体类定义
  progress_service.py      Python   backend/app/service/progress_service.py          进度管理业务逻辑实现
  progress_repository.py   Python   backend/app/repository/progress_repository.py    进度数据访问层
  GenerationProgress.vue   Vue      frontend/src/components/GenerationProgress.vue   前端生成进度展示组件
  ------------------------ -------- ------------------------------------------------ ----------------------

**2 功能实现**

内容生成模块每完成一个生成步骤，调用 ProgressService
更新当前进度与状态；

ProgressService 校验状态流转合法性，通过 ProgressRepository
更新数据库进度记录；

ProgressService 通过 WebSocket 服务端向前端推送最新进度数据；

前端 WebSocket
客户端接收进度消息，实时更新页面进度条、步骤描述与状态展示；

若生成过程出现异常，ProgressService
将课程状态标记为失败，记录错误信息并推送至前端；

用户触发重试操作时，CourseService 重置进度状态，重新启动内容生成流程。

时序图（Sequence Diagram）

![](media/image11.png){width="5.759027777777778in"
height="1.6111111111111112in"}

协作图（Collaboration Diagram）

![](media/image12.png){width="5.759027777777778in"
height="3.0555555555555554in"}

#### 2.2.2.2 多模态内容生成模块

**1、简介**

多模态内容生成模块对应需求规格说明书中 F002 多模态教学内容生成引擎
能力，是平台的核心内容生产引擎。基于课程大纲与知识图谱数据，通过策略调度生成沉浸式文本、测验题目、PPT
课件、音频旁白、思维导图、互动式教材六种模态的教学内容，支持生成过程的进度推送与异常重试。

2、功能列表

生成任务调度：按章节顺序串行调度各模态生成任务，维护任务执行状态，支持异常重试；

多模态内容生成：支持六种模态内容的标准化生成，输出结构化数据与静态资源文件；

内容缓存管理：已生成内容持久化存储，重复访问直接读取缓存，零 LLM 调用；

内容导出：支持 PPT 课件、思维导图等内容的本地文件导出。

##### 2.2.2.2.1 生成任务调度功能

**1 功能设计描述**

本功能负责多模态内容生成的全流程调度，按照教学场景编排结果依次执行各模态生成任务，管控任务执行顺序、异常重试与进度同步。

**（1）类**

**1）ContentModule 实体类**

对应数据库 content_modules 表，封装内容模块属性，包括模块 ID、所属章节
ID、模态类型、结构化内容 JSON、静态资源文件路径。

**2）GenerateScheduler 调度类**

内容生成任务调度器，采用串行队列模式管理生成任务，按章节顺序与场景编排结果执行模态生成。

**3）BaseModalGenerator 抽象生成类**

所有模态生成器的基类，定义统一的 generate()
接口，遵循策略模式实现多模态能力扩展。

**4）ContentService 业务服务类**

负责内容模块的增删改查、生成任务触发与内容数据组装。

**（2）类与类之间关系**

![](media/image13.png){width="5.768055555555556in"
height="3.4368055555555554in"}

GenerateScheduler 基于 BaseModalGenerator
抽象接口调度各具体生成器实现类；

ContentService 依赖 GenerateScheduler 与
ContentRepository，分别完成任务调度与数据持久化；

Chapter 与 ContentModule
为一对多聚合关系，一个章节包含多个不同模态的内容模块。

**（3）文件列表**

  ----------------------- ------------ --------------------------------------------- ------------------------------------
  名称                    类型         存放位置                                      说明
  content_model.py        Python       backend/app/models/content_model.py           内容模块实体类定义
  content_service.py      Python       backend/app/service/content_service.py        内容管理业务逻辑实现
  generate_scheduler.py   Python       backend/app/generator/generate_scheduler.py   生成任务调度器实现
  base_generator.py       Python       backend/app/generator/base_generator.py       模态生成器抽象基类
  CoursePlayer.vue        Vue          frontend/src/views/course/CoursePlayer.vue    前端课程播放器组件，展示多模态内容
  content.ts              TypeScript   frontend/src/api/content.ts                   前端内容接口请求封装
  ----------------------- ------------ --------------------------------------------- ------------------------------------

**2 功能实现**

课程大纲生成完成后，ContentService 接收生成指令，初始化
GenerateScheduler 调度器；

调度器遍历课程所有章节，根据教学场景编排结果，为每个章节生成对应模态的任务队列；

调度器按顺序调用对应模态的 Generator
实现类，传入章节知识点与大纲上下文数据；

各模态生成器调用 LLM Provider 完成内容生成，返回结构化内容数据；

调度器每完成一个任务，调用 ProgressService 更新生成进度，并通过
WebSocket 推送至前端；

生成完成的内容数据由 ContentService
持久化到数据库，静态资源写入对应课程目录的文件系统；

全部任务执行完成后，调度器更新课程状态为 "已完成"，推送完成通知至前端。

时序图（Sequence Diagram）

![](media/image14.png){width="5.759027777777778in"
height="3.629861111111111in"}

协作图（Collaboration Diagram）

![](media/image15.png){width="5.76875in" height="2.259027777777778in"}

##### 2.2.2.2.2 单模态内容生成功能

**1 功能设计描述**

本功能承接用户的学习主题输入，完成课程实体创建、主题解析与结构化大纲生成，是课程生成全流程的入口。

**（1）类**

**1）TextGenerator 文本生成器**

继承
BaseModalGenerator，实现沉浸式教学文本的生成，自动插入知识点校验问题与知识关联引导。

**2）QuizGenerator 测验生成器**

继承
BaseModalGenerator，实现选择题、判断题、简答题的自动生成，同步产出答案与解析。

**3）PPTGenerator PPT 生成器**

继承 BaseModalGenerator，生成 PPT 结构化数据，支持导出为 .pptx
本地文件。

**4）MindMapGenerator 思维导图生成器**

继承
BaseModalGenerator，基于知识图谱节点关系生成可交互的思维导图结构数据。

（2）类与类之间关系

![](media/image16.png){width="5.768055555555556in"
height="2.3493055555555555in"}

所有模态生成器均继承 BaseModalGenerator，实现统一的生成接口；

各模态生成器均依赖 LLM Provider 完成内容创作；

GenerateScheduler 通过基类接口调用各生成器，无需感知具体模态的实现细节。

**（3）文件列表**

  ---------------------- -------- -------------------------------------------------- ----------------------
  名称                   类型     存放位置                                           说明
  text_generator.py      Python   backend/app/generator/modal/text_generator.py      沉浸式文本生成实现
  quiz_generator.py      Python   backend/app/generator/modal/quiz_generator.py      测验题目生成实现
  ppt_generator.py       Python   backend/app/generator/modal/ppt_generator.py       PPT 课件生成实现
  mindmap_generator.py   Python   backend/app/generator/modal/mindmap_generator.py   思维导图生成实现
  ModalTab.vue           Vue      frontend/src/components/course/ModalTab.vue        前端模态切换展示组件
  ---------------------- -------- -------------------------------------------------- ----------------------

**2 功能实现说明**

调度器调用对应生成器的 generate() 方法，传入章节上下文与知识点数据；

生成器加载对应 Prompt 模板，组装标准化生成请求参数；

生成器调用 LLM Provider 的接口，获取 AI 生成的原始内容；

生成器对返回内容进行格式校验、结构化解析与异常兜底处理；

生成器返回标准化的内容数据给调度器；

若调用失败，生成器执行指数退避重试，最多重试 3
次，仍失败则抛出异常由调度器统一处理。

时序图（Sequence Diagram）

![](media/image17.png){width="5.76875in" height="4.222222222222222in"}

协作图（Collaboration Diagram）

![](media/image18.png){width="5.759027777777778in"
height="1.9256944444444444in"}

#### 2.2.2.3 知识图谱管理模块

**1、简介**

知识图谱管理模块对应需求规格说明书中 F003 课程知识库与知识图谱管理
能力，是平台的知识基础设施模块。负责知识点节点与关系的存储、计算、可视化展示与编辑维护，为课程大纲生成、内容创作提供知识结构约束，保障生成内容的体系性与逻辑性。

2、功能列表

知识图谱构建：支持预置图谱导入与 AI
自动抽取两种构建方式，存储知识点节点与多元关系；

知识图谱可视化：采用力导向布局实现图谱图形化展示，支持缩放、拖拽、节点高亮与路径追踪；

知识图谱编辑：支持手动增删知识点节点、修改关系类型、调整节点属性；

图计算能力：基于 NetworkX
实现知识点拓扑排序、前驱后继路径查询、关联知识点推荐

##### 2.2.2.3.1知识图谱存储与计算功能

**1 功能设计描述**

本功能负责知识图谱数据的持久化存储与内存图计算，为上层业务模块提供标准化的知识数据查询接口。

**（1）类**

**1）KnowledgeNode 实体类**

对应数据库 knowledge_nodes 表，封装知识点节点属性，包括节点 ID、所属课程
ID、知识点名称、类型、重要性权重、描述。

**2）KnowledgeEdge 实体类**

对应数据库 knowledge_edges 表，封装知识点关系属性，包括关系 ID、所属课程
ID、起始节点 ID、目标节点 ID、关系类型。

**3）GraphEngine 图计算引擎类**

基于 NetworkX
实现内存图构建，提供拓扑排序、最短路径查询、关联节点挖掘等图计算能力。

**4）KnowledgeService 业务服务类**

封装知识图谱的增删改查与图计算调用逻辑，向上层业务模块提供统一知识服务接口。

**（2）类与类之间关系**

![](media/image19.png){width="5.768055555555556in"
height="3.063888888888889in"}

KnowledgeService 依赖 KnowledgeRepository 与
GraphEngine，分别完成数据持久化与图计算操作；

KnowledgeNode 与 KnowledgeEdge 为多对多关联关系，共同构成图结构数据；

CourseService、ContentService 均依赖 KnowledgeService 获取知识结构数据。

**（3）文件列表**

  ------------------------- -------- ------------------------------------------------ ----------------------------
  名称                      类型     存放位置                                         说明
  knowledge_model.py        Python   backend/app/models/knowledge_model.py            知识点节点与关系实体类定义
  knowledge_service.py      Python   backend/app/service/knowledge_service.py         知识图谱业务逻辑实现
  graph_engine.py           Python   backend/app/utils/graph_engine.py                图计算引擎封装
  knowledge_repository.py   Python   backend/app/repository/knowledge_repository.py   知识图谱数据访问层
  ------------------------- -------- ------------------------------------------------ ----------------------------

**2 功能实现**

CourseService 调用 KnowledgeService 的课程图谱构建接口，传入课程主题；

KnowledgeService 从预置图谱库中匹配对应领域的核心知识点与基础关系；

KnowledgeService 调用 GraphEngine
构建内存图结构，执行拓扑排序确定知识点讲授顺序；

KnowledgeService 将排序后的知识点列表与关系数据返回给 CourseService；

CourseService 结合知识点顺序调用 LLM
生成课程大纲，保障大纲符合认知规律；

课程生成完成后，KnowledgeService 将课程专属图谱数据持久化到数据库。

时序图（Sequence Diagram）

![](media/image20.png){width="5.768055555555556in"
height="4.332638888888889in"}

协作图（Collaboration Diagram）

![](media/image21.png){width="5.76875in" height="1.3701388888888888in"}

##### 2.2.2.3.2 知识图谱可视化与编辑功能

**1 功能设计描述**

本功能负责知识图谱的前端可视化渲染与用户编辑交互，实现知识结构的直观展示与手动修正。

**（1）类**

**1）KnowledgeController 控制类**

提供知识图谱查询、编辑的 RESTful 接口，负责参数校验与响应封装。

**2）GraphVisualProcessor 可视化处理类**

将数据库中的图数据转换为前端可视化组件兼容的格式，处理节点样式、布局参数与标签配置。

**（2）类与类之间关系**

![](media/image22.png){width="5.768055555555556in"
height="4.872222222222222in"}

KnowledgeController 依赖 KnowledgeService，接收前端请求并返回处理结果；

KnowledgeService 依赖 GraphVisualProcessor 完成可视化数据格式转换。

**（3）文件列表**

  -------------------- ------------ ------------------------------------------------------ -------------------------------------------------
  名称                 类型         存放位置                                               说明
  knowledge.py         Python       backend/app/api/knowledge.py                           知识图谱接口控制器
  KnowledgeGraph.vue   Vue          frontend/src/components/knowledge/KnowledgeGraph.vue   前端知识图谱可视化组件（基于 ECharts 力导向图）
  knowledge.ts         TypeScript   frontend/src/api/knowledge.ts                          前端知识图谱接口请求封装
  -------------------- ------------ ------------------------------------------------------ -------------------------------------------------

**2 功能实现说明**

用户进入课程知识图谱页面，前端调用图谱查询接口；

KnowledgeController 接收请求，调用 KnowledgeService
获取课程对应的节点与关系数据；

GraphVisualProcessor
对原始图数据进行格式转换，补充节点样式、标签、布局参数；

处理后的可视化数据返回前端，ECharts 组件渲染为力导向交互图；

用户执行编辑操作（新增节点、修改关系），前端提交编辑请求；

KnowledgeService
校验操作合法性，更新数据库数据后返回最新图谱数据，前端重新渲染。

时序图（Sequence Diagram）

![](media/image23.png){width="5.768055555555556in"
height="4.591666666666667in"}

协作图（Collaboration Diagram）

![](media/image24.png){width="5.759027777777778in"
height="1.2222222222222223in"}

#### 2.2.2.4 语音服务模块

**1、简介**

语音服务模块对应需求规格说明书中 F-Voice 语音功能集成
能力，负责平台全链路语音交互能力。集成多厂商 TTS 语音合成与 ASR
语音识别服务，实现 AI 教师语音授课、学生语音提问、PPT
旁白同步播放三大核心场景，支持流式传输与缓存优化。

2、功能列表

语音合成（TTS）：支持段落级流式语音合成，多音色可选，实现 AI 教师授课与
PPT 旁白生成；

语音识别（ASR）：支持实时流式语音识别，中英文混合识别，承接学生语音提问输入；

语音播放控制：支持暂停、继续、语速调节、重播等播放控制能力；

语音缓存管理：对高频使用的语音片段进行本地缓存，降低接口调用成本与响应延迟。

##### 2.2.2.4.1语音合成（TTS）服务功能

**1 功能设计描述**

本功能封装多厂商 TTS
服务能力，通过适配器模式实现供应商无缝切换，为课程旁白、AI
对话提供语音合成能力。

**（1）类**

**1）BaseTTSProvider 抽象 TTS 提供商类**

定义统一的 synthesize() 合成接口，所有 TTS 厂商实现类均继承该基类。

**2）EdgeTTSProvider、AliyunTTSProvider 具体实现类**

分别对应 Edge TTS、阿里云 TTS 等厂商的接口适配实现。

**3）TTSService 语音合成服务类**

根据系统配置选择对应 TTS 提供商，封装合成逻辑，支持流式输出与缓存管理。

**4）VoiceController 控制类**

提供语音合成、语音文件查询等接口，支持流式语音响应。

**（2）类与类之间关系**

![](media/image25.png){width="5.768055555555556in" height="2.725in"}

各 TTS 厂商实现类均继承 BaseTTSProvider，实现统一合成接口；

TTSService 依赖
BaseTTSProvider，通过配置动态选择具体实现类，遵循适配器模式；

ContentService、对话服务均依赖 TTSService 获取语音合成能力。

**（3） 文件列表**

  ---------------------- -------- ------------------------------------------------ -----------------------
  名称                   类型     存放位置                                         说明
  base_tts_provider.py   Python   backend/app/provider/tts/base_tts_provider.py    TTS 提供商抽象基类
  edge_tts_provider.py   Python   backend/app/provider/tts/edge_tts_provider.py    Edge TTS 厂商适配实现
  tts_service.py         Python   backend/app/service/tts_service.py               语音合成业务逻辑实现
  voice.py               Python   backend/app/api/voice.py                         语音接口控制器
  AudioPlayer.vue        Vue      frontend/src/components/common/AudioPlayer.vue   前端通用音频播放组件
  ---------------------- -------- ------------------------------------------------ -----------------------

**2 功能实现**

PPT 内容生成完成后，ContentService 调用 TTSService 生成对应旁白语音；

TTSService 根据系统配置选择对应 TTS 提供商，传入旁白文本与音色参数；

TTS 提供商实现类调用第三方接口，获取语音数据流；

TTSService 将语音文件写入本地文件系统，记录文件路径到对应内容模块中；

用户播放 PPT 旁白时，前端直接请求静态语音文件进行播放；

若主 TTS 服务商调用失败，TTSService
自动切换至备选提供商，保障服务可用性。

时序图（Sequence Diagram）

![](media/image26.png){width="5.759027777777778in" height="3.25in"}

协作图（Collaboration Diagram）

![](media/image27.png){width="5.75in" height="1.9076388888888889in"}

##### 2.2.2.4.2语音识别（ASR）与实时交互功能

**1 功能设计描述**

本功能封装实时语音识别能力，基于 WebSocket
实现全双工语音交互，支持学生语音提问与 AI 实时应答。

**（1）类**

**1）BaseASRProvider 抽象 ASR 提供商类**

定义统一的 recognize() 识别接口，所有 ASR 厂商实现类均继承该基类。

**2）AliyunASRProvider 具体实现类**

阿里云语音识别服务的接口适配实现，支持流式实时识别。

**3）ASRService 语音识别服务类**

管理 WebSocket 语音连接，处理音频流，返回识别文本结果。

**4）ChatService 对话服务类**

接收识别后的文本，调用 LLM 生成回答，同步调用 TTS 生成语音回答。

（2）类与类之间关系

![](media/image28.png){width="5.768055555555556in"
height="1.7479166666666666in"}

ASRService 依赖 BaseASRProvider 完成语音识别；

ChatService 同时依赖 ASRService 与 TTSService，实现语音对话全链路闭环；

前端通过 WebSocket 与后端 ASR 服务建立长连接，传输音频流。

**（3）文件列表**

  ------------------------ -------- ------------------------------------------------- -------------------------
  名称                     类型     存放位置                                          说明
  base_asr_provider.py     Python   backend/app/provider/asr/base_asr_provider.py     ASR 提供商抽象基类
  aliyun_asr_provider.py   Python   backend/app/provider/asr/aliyun_asr_provider.py   阿里云 ASR 厂商适配实现
  asr_service.py           Python   backend/app/service/asr_service.py                语音识别业务逻辑实现
  chat_service.py          Python   backend/app/service/chat_service.py               智能对话业务逻辑实现
  VoiceInput.vue           Vue      frontend/src/components/common/VoiceInput.vue     前端语音输入组件
  ------------------------ -------- ------------------------------------------------- -------------------------

**2 功能实现说明**

用户点击前端语音输入按钮，前端与后端建立 WebSocket 语音连接；

用户麦克风采集音频流，通过 WebSocket 实时发送至后端；

ASRService 接收音频流，调用 ASR
提供商接口进行实时识别，逐段返回识别文本；

用户结束语音输入，ASRService 返回完整识别文本给 ChatService；

ChatService 调用 LLM Provider 生成回答文本，同时调用 TTSService
生成语音回答；

ChatService 通过 WebSocket 将文本回答与语音流推送至前端；

前端展示回答文本，播放语音回答，完成一次语音问答交互。

时序图（Sequence Diagram）

![](media/image29.png){width="5.759027777777778in"
height="3.7777777777777777in"}

协作图（Collaboration Diagram）

![](media/image30.png){width="5.759027777777778in"
height="1.2965277777777777in"}

### 2.2.3 接口描述

本节描述智能互动教学平台各设计实体间的接口规范，覆盖前端与后端的业务交互接口、模块间内部服务接口、实时通信接口，以及系统与外部第三方服务的对接接口。所有接口遵循统一的错误码规范与
JSON 数据格式标准，保障跨模块、跨系统交互的一致性。

#### 2.2.3.1前端业务 REST 接口

本类接口为系统对前端 Web 应用暴露的业务功能接口，采用 HTTPS
协议、RESTful 架构风格，统一路由前缀为/api/v1，由 FastAPI
网关层统一路由与参数校验。

（1）课程创建与大纲生成接口

Name 名称：课程创建与大纲生成接口

Description 说明：接收用户输入的学习主题，创建课程实体并调用 LLM
生成结构化课程大纲，返回课程基础信息与章节大纲数据。

Definition 定义:

-   接口类型：RESTful API

-   请求方式：POST

-   请求路径：/api/v1/courses

-   请求参数：

  ------------- ---------- ---------- ---------------------------------
  **参数名**    **类型**   **必填**   **说明**
  title         String     是         学习主题 / 课程标题
  description   String     否         课程补充描述与学习要求
  preset_id     Integer    否         预置课程 ID，选择预置课程时传入
  ------------- ---------- ---------- ---------------------------------

-   返回参数：

  ------------ ---------- ---------------------------------------------
  **参数名**   **类型**   **说明**
  course_id    Integer    课程唯一标识
  title        String     课程标题
  status       String     课程状态（draft/generating）
  chapters     Array      课程大纲章节列表，含章节 ID、标题、排序序号
  created_at   DateTime   课程创建时间
  ------------ ---------- ---------------------------------------------

（2）课程列表分页查询接口

Name 名称：课程列表分页查询接口

Description
说明：分页查询全量课程列表，支持按状态、创建时间筛选与标题关键词搜索，用于课程管理页面展示。

Definition 定义:

-   接口类型：RESTful API

-   请求方式：GET

-   请求路径：/api/v1/courses

-   请求参数：

  --------------- ---------- ---------- ----------------------------------------------
  **参数名**      **类型**   **必填**   **说明**
  **page**        Integer    否         页码，默认值为 1
  **page_size**   Integer    否         每页条数，默认值为 10
  **status**      String     否         课程状态筛选（draft/generating/done/failed）
  **keyword**     String     否         课程标题模糊搜索关键词
  --------------- ---------- ---------- ----------------------------------------------

-   返回参数：

  ------------ ---------- -----------------------------------------------
  **参数名**   **类型**   **说明**
  total        Integer    课程总条数
  list         Array      课程列表数据，含课程 ID、标题、状态、创建时间
  page         Integer    当前页码
  page_size    Integer    每页条数
  ------------ ---------- -----------------------------------------------

（3）课程详情查询接口

Name 名称：课程详情与大纲查询接口

Description 说明：根据课程 ID
查询课程完整基础信息、章节大纲与生成进度元数据，用于课程详情页与播放器初始化。

Definition 定义:

-   接口类型：RESTful API

-   请求方式：GET

-   请求路径：/api/v1/courses/{course_id}

-   请求参数：路径参数 course_id（课程唯一标识）

-   返回参数：

  --------------------- ---------- -------------------------------------------------------------
  **参数名**            **类型**   **说明**
  course_info           Object     课程基础信息（标题、描述、状态、创建更新时间）
  chapters              Array      章节详情列表，含章节 ID、标题、排序序号、关联知识点 ID 列表
  generation_progress   Object     生成进度信息（当前步骤、总步骤、状态、错误信息）
  --------------------- ---------- -------------------------------------------------------------

（4）多模态内容生成触发接口

Name 名称：多模态内容生成触发接口

Description
说明：触发指定课程的全量多模态内容生成任务，任务异步执行，生成进度通过
WebSocket 实时推送至前端。

Definition 定义:

-   接口类型：RESTful API

-   请求方式：POST

-   请求路径：/api/v1/courses/{course_id}/generate

-   请求参数：

    -   路径参数：course_id（课程唯一标识）

    -   Body 参数：

  ------------- ---------- ---------- -------------------------------------------------
  **参数名**    **类型**   **必填**   **说明**
  modal_types   Array      否         指定生成的模态类型列表，不传则生成全部 6 种模态
  regenerate    Boolean    否         是否强制重新生成已完成内容，默认值为 false
  ------------- ---------- ---------- -------------------------------------------------

-   返回参数：

  ---------------- ---------- ---------------------------------
  **参数名**       **类型**   **说明**
  task_id          Integer    生成任务唯一标识
  status           String     任务初始状态（pending/running）
  estimated_time   Integer    预计总耗时（单位：秒）
  ---------------- ---------- ---------------------------------

（5）章节内容模块查询接口

Name 名称：章节内容模块查询接口

Description
说明：查询指定章节下的所有多模态内容数据，用于课程播放器加载对应模态的学习内容。

Definition 定义:

-   接口类型：RESTful API

-   请求方式：GET

-   请求路径：/api/v1/chapters/{chapter_id}/contents

-   请求参数：路径参数 chapter_id（章节唯一标识）

-   返回参数：

  ----------------- ---------- ------------------------------------------------------------------
  **参数名**        **类型**   **说明**
  chapter_id        Integer    章节 ID
  content_modules   Array      内容模块列表，含模块 ID、模态类型、结构化内容 JSON、静态资源路径
  ----------------- ---------- ------------------------------------------------------------------

（6）知识图谱数据查询接口

Name 名称：课程知识图谱查询接口

Description
说明：查询指定课程对应的知识图谱节点与关系数据，转换为前端可视化兼容格式，用于图谱页面渲染。

Definition 定义:

-   接口类型：RESTful API

-   请求方式：GET

-   请求路径：/api/v1/courses/{course_id}/knowledge-graph

-   请求参数：路径参数 course_id（课程唯一标识）

-   返回参数：

  --------------- ---------- ---------------------------------------------------------------
  **参数名**      **类型**   **说明**
  nodes           Array      知识点节点列表，含节点 ID、名称、类型、重要性权重、描述
  edges           Array      知识点关系列表，含关系 ID、起始节点 ID、目标节点 ID、关系类型
  layout_config   Object     力导向图布局配置参数
  --------------- ---------- ---------------------------------------------------------------

（7）语音合成接口

Name 名称：文本转语音合成接口

Description
说明：将输入文本转换为语音音频，支持指定音色、语速，返回音频文件访问地址，用于自定义内容的语音播放。

Definition 定义:

-   接口类型：RESTful API

-   请求方式：POST

-   请求路径：/api/v1/voice/tts

-   请求参数：

  ------------ ---------- ---------- ----------------------------
  **参数名**   **类型**   **必填**   **说明**
  text         String     是         待合成的文本内容
  voice_type   String     否         音色类型，默认 AI 教师音色
  speed        Float      否         语速系数，默认值为 1.0
  ------------ ---------- ---------- ----------------------------

-   返回参数：

  ------------ ---------- --------------------------
  **参数名**   **类型**   **说明**
  audio_url    String     合成后的音频文件访问地址
  duration     Float      音频总时长（单位：秒）
  ------------ ---------- --------------------------

#### 2.2.3.2 WebSocket 实时通信接口

本类接口用于低延迟双向实时交互场景，基于 WebSocket
协议实现，统一连接前缀为/ws/v1，支持心跳保活与自动重连。

（1）生成进度实时推送接口

Name 名称：课程生成进度推送接口

Description
说明：课程内容生成过程中，服务端实时向前端推送生成进度、步骤状态与异常信息，前端同步更新进度
UI。

Definition 定义:

-   接口类型：WebSocket 服务端单向推送

-   连接路径：/ws/v1/generation/{course_id}

-   触发时机：生成任务每完成一个步骤、状态变更或出现异常时主动推送

-   推送消息格式：

  --------------- ---------- -----------------------------------
  **字段名**      **类型**   **说明**
  type            String     消息类型（progress/status/error）
  current_step    Integer    当前已完成步骤编号
  total_steps     Integer    任务总步骤数
  step_name       String     当前执行的步骤名称
  status          String     任务整体状态
  error_message   String     错误详情（仅 error 类型消息返回）
  --------------- ---------- -----------------------------------

-   客户端上行：每 30 秒发送心跳包，维持连接存活。

（2）实时语音问答交互接口

Name 名称：实时语音问答交互接口

Description 说明：承载学生语音输入的分片传输、识别结果逐段回传与 AI
回答的流式推送，实现全双工语音对话交互。

Definition 定义:

-   接口类型：WebSocket 双向通信

-   连接路径：/ws/v1/voice/chat

-   客户端上行消息格式：

  ------------ ---------- ----------------------------------------------------
  **字段名**   **类型**   **说明**
  type         String     消息类型（audio_start/audio_chunk/audio_end/text）
  audio_data   Binary     PCM 格式音频分片数据
  text         String     纯文本提问内容（text 类型消息携带）
  course_id    Integer    当前课程 ID，用于关联学习上下文
  ------------ ---------- ----------------------------------------------------

-   服务端下行消息格式：

  ------------- ---------- ------------------------------------------------------------
  **字段名**    **类型**   **说明**
  type          String     消息类型（asr_partial/asr_final/answer_text/answer_audio）
  text          String     语音识别中间 / 最终结果、AI 回答文本
  audio_chunk   Binary     AI 回答的语音分片数据
  is_final      Boolean    是否为最终结果
  ------------- ---------- ------------------------------------------------------------

#### 2.2.3.3 内部服务调用接口

本类接口为系统内部各业务服务层之间的函数调用接口，通过标准化方法签名定义，实现模块间解耦与能力复用，仅允许服务层内部调用。

（1）知识图谱拓扑排序接口

Name 名称：知识点拓扑排序接口

Description 说明：课程服务调用该接口，根据课程 ID
获取按认知前驱关系拓扑排序后的知识点列表，为大纲生成提供知识顺序约束。

Definition 定义:

-   接口类型：内部函数调用

-   方法签名：KnowledgeService.get_sorted_nodes(course_id: int) -\>
    List\[KnowledgeNode\]

-   入参：course_id（课程唯一标识）

-   返回值：按前驱后继关系拓扑排序后的知识点节点对象列表

-   异常处理：图谱存在循环依赖时抛出GraphCycleError异常，携带循环路径信息。

（2）单模态内容生成接口

Name 名称：单模态内容生成接口

Description
说明：生成调度器调用该接口，执行指定章节、指定模态的内容生成任务，返回标准化内容模块数据。

Definition 定义:

-   接口类型：内部函数调用

-   方法签名：ContentService.generate_modal_content(chapter_id: int,
    modal_type: str) -\> ContentModule

-   入参：

    -   chapter_id：章节唯一标识

    -   modal_type：模态类型（text/quiz/ppt/narration/mindmap/interactive_html）

-   返回值：生成完成的内容模块持久化对象

-   异常处理：生成失败时抛出ContentGenerateError异常，携带错误类型与详情。

（3）批量旁白生成接口

Name 名称：PPT 批量旁白生成接口

Description 说明：内容生成服务调用该接口，批量生成 PPT
每页对应的语音旁白文件，返回音频文件路径列表。

Definition 定义:

-   接口类型：内部函数调用

-   方法签名：TTSService.batch_generate_narration(text_list:
    List\[str\], voice_config: dict) -\> List\[str\]

-   入参：

    -   text_list：待合成的每页旁白文本列表

    -   voice_config：音色、语速、格式等配置参数

-   返回值：按顺序排列的音频文件本地路径列表

#### 2.2.3.3 外部第三方服务接口

本类接口为系统与外部第三方服务之间的对接接口，通过 Provider
抽象层统一封装，遵循适配器模式，实现多供应商的可配置切换与业务层无感知替换。

（1）LLM 服务统一接口

Name 名称：大语言模型生成统一接口

Description 说明：LLM Provider
抽象层定义的标准接口，所有大语言模型供应商均需实现该接口，为上层业务提供一致的内容生成能力。

Definition 定义:

-   接口类型：外部 REST API 适配接口

-   方法签名：BaseLLMProvider.chat_completion(prompt: str,
    response_format: str = \"text\") -\> str

-   入参：

    -   prompt：结构化提示词文本

    -   response_format：返回格式约束（text/json）

-   返回值：LLM 生成的纯文本结果

-   实现类：DeepSeekProvider、QwenProvider、KimiProvider，分别对应不同厂商的
    API 签名适配。

（2）TTS 服务统一接口

Name 名称：语音合成服务统一接口

Description 说明：TTS Provider
抽象层定义的标准接口，所有语音合成供应商均需实现该接口，支持文本到音频的转换能力。

Definition 定义:

-   接口类型：外部 REST API/WebSocket 适配接口

-   方法签名：BaseTTSProvider.synthesize(text: str, config: dict) -\>
    bytes

-   入参：

    -   text：待合成的文本内容

    -   config：音色、语速、音频格式等配置

-   返回值：合成后的音频二进制数据

-   实现类：EdgeTTSProvider、AliyunTTSProvider、TencentTTSProvider。

（3）ASR 服务统一接口

Name 名称：实时语音识别统一接口

Description 说明：ASR Provider
抽象层定义的标准接口，所有语音识别供应商均需实现该接口，支持流式音频的实时识别。

Definition 定义:

-   接口类型：外部 WebSocket 适配接口

-   方法签名：BaseASRProvider.stream_recognize(audio_stream: Generator,
    config: dict) -\> Generator\[str\]

-   入参：

    -   audio_stream：音频分片流生成器

    -   config：语言、采样率、编码格式等配置

-   返回值：识别文本结果生成器，支持逐段返回中间与最终结果

-   实现类：AliyunASRProvider、TencentASRProvider。

# 3 数据结构/数据库设计

## 3.1 概念模型

本系统采用MySQL（生产环境）/
SQLite（开发环境）双模式数据库方案，通过SQLAlchemy
ORM实现数据库无关的代码编写。开发阶段使用SQLite零配置启动，交付阶段切换MySQL仅需修改配置文件中的连接字符串。

知识图谱的图结构数据通过两张关系表（knowledge_nodes、knowledge_edges）存储在数据库中，内存图计算使用NetworkX库。

系统核心实体及其关系如下：

**课程（Course）** → 包含多个章节（Chapter） →
每个章节关联多个内容模块（ContentModule）

**课程（Course）** → 拥有知识图谱 →
知识图谱包含知识点节点（KnowledgeNode）和知识点关系（KnowledgeEdge）

**课程（Course）** → 关联生成进度记录（GenerationProgress）

![b47a4e613a523b51848b22f7b9846d01](media/image31.png){width="5.767361111111111in"
height="3.075in"}

## 3.2 数据库表设计

系统核心数据表设计如下（以MySQL语法为准，SQLite通过SQLAlchemy自动适配）：

**（1）courses（课程表）**

  ------------- -------------- ---------- ---------------------------- ----------------------------------------
  **字段名**    **类型**       **必填**   **约束**                     **说明**
  id            INTEGER        是         PRIMARY KEY AUTO_INCREMENT   课程唯一标识
  title         VARCHAR(200)   是         NOT NULL                     课程标题
  description   TEXT           否                                      课程描述
  status        VARCHAR(20)    是         NOT NULL                     课程状态：draft/generating/done/failed
  created_at    DATETIME       是         NOT NULL                     创建时间
  updated_at    DATETIME       是         NOT NULL                     更新时间
  ------------- -------------- ---------- ---------------------------- ----------------------------------------

**（2）chapters（章节表）**

  -------------------- -------------- ---------- ---------------------------- --------------------
  **字段名**           **类型**       **必填**   **约束**                     **说明**
  id                   INTEGER        是         PRIMARY KEY AUTO_INCREMENT   章节唯一标识
  course_id            INTEGER        是         FOREIGN KEY → courses.id     所属课程ID
  title                VARCHAR(200)   是         NOT NULL                     章节标题
  order                INTEGER        是         NOT NULL                     章节排序序号
  knowledge_node_ids   TEXT           否         JSON格式                     关联的知识点ID列表
  -------------------- -------------- ---------- ---------------------------- --------------------

**（3）knowledge_nodes（知识点节点表）**

  ------------- -------------- ---------- ---------------------------- ----------------------------
  **字段名**    **类型**       **必填**   **约束**                     **说明**
  id            INTEGER        是         PRIMARY KEY AUTO_INCREMENT   节点唯一标识
  course_id     INTEGER        是         FOREIGN KEY → courses.id     所属课程ID
  name          VARCHAR(200)   是         NOT NULL                     知识点名称
  type          VARCHAR(20)    是         NOT NULL                     类型：concept/skill/memory
  importance    FLOAT          是         DEFAULT 0.5                  重要性权重（0-1）
  description   TEXT           否                                      知识点描述
  ------------- -------------- ---------- ---------------------------- ----------------------------

**（4）knowledge_edges（知识点关系表）**

  ---------------- ------------- ---------- ---------------------------------- --------------------------------
  **字段名**       **类型**      **必填**   **约束**                           **说明**
  id               INTEGER       是         PRIMARY KEY AUTO_INCREMENT         关系唯一标识
  course_id        INTEGER       是         FOREIGN KEY → courses.id           所属课程ID
  source_node_id   INTEGER       是         FOREIGN KEY → knowledge_nodes.id   起始知识点ID
  target_node_id   INTEGER       是         FOREIGN KEY → knowledge_nodes.id   目标知识点ID
  relation_type    VARCHAR(20)   是         NOT NULL                           关系类型：prerequisite/related
  ---------------- ------------- ---------- ---------------------------------- --------------------------------

**（5）content_modules（内容模块表）**

  -------------- -------------- ---------- ---------------------------- ------------------------------------------------------------
  **字段名**     **类型**       **必填**   **约束**                     **说明**
  id             INTEGER        是         PRIMARY KEY AUTO_INCREMENT   模块唯一标识
  chapter_id     INTEGER        是         FOREIGN KEY → chapters.id    所属章节ID
  modal_type     VARCHAR(30)    是         NOT NULL                     模态类型：text/quiz/ppt/narration/mindmap/interactive_html
  content_json   TEXT           否         JSON格式                     结构化内容数据
  file_path      VARCHAR(500)   否                                      静态资源文件路径
  -------------- -------------- ---------- ---------------------------- ------------------------------------------------------------

**（6）generation_progress（生成进度表）**

  --------------- ------------- ---------- --------------------------------- -----------------------------------------------------------------
  **字段名**      **类型**      **必填**   **约束**                          **说明**
  id              INTEGER       是         PRIMARY KEY AUTO_INCREMENT        进度记录唯一标识
  course_id       INTEGER       是         FOREIGN KEY UNIQUE → courses.id   所属课程ID
  status          VARCHAR(30)   是         NOT NULL                          状态：pending/outline_generating/content_generating/done/failed
  current_step    INTEGER       是         NOT NULL                          当前步骤编号
  total_steps     INTEGER       是         NOT NULL                          总步骤数
  error_message   TEXT          否                                           错误信息
  updated_at      DATETIME      是         NOT NULL                          更新时间
  --------------- ------------- ---------- --------------------------------- -----------------------------------------------------------------

## 3.3 基础数据配置

系统基础数据配置通过config.yaml文件管理，关键配置项包括：

  ---------------------- ---------------- --------------------------------------
  **配置项**             **说明**         **可选值/示例**
  database.driver        数据库类型       mysql / sqlite
  database.mysql.\*      MySQL连接参数    host, port, user, password, database
  database.sqlite.path   SQLite文件路径   ./data/smart_teaching.db
  llm.provider           当前LLM提供商    deepseek / qwen
  llm.deepseek.\*        DeepSeek配置     api_key, base_url, model
  llm.qwen.\*            通义千问配置     api_key, base_url, model
  tts.provider           TTS提供商        edge / aliyun / tencent
  asr.provider           ASR提供商        aliyun / tencent
  server.host            服务器地址       localhost
  server.port            服务器端口       8000
  ---------------------- ---------------- --------------------------------------

# 4 界面设计

本平台采用轻量化、极简风的 Web
端界面设计，以浅灰白色为基底、品牌紫色为强调色，遵循 "少干扰、强聚焦"
的学习产品设计原则，核心操作路径不超过 3 步。MVP
阶段覆盖三大核心业务界面，完整承载从课程创建到互动学习的全流程用户体验。

## 4.1 平台首页与课程创建界面

1 界面原图

![](media/image32.png){width="5.759027777777778in"
height="3.435416666666667in"}

2 界面说明

本界面为平台入口首屏，对应F001
智能课堂生成模块的主题输入与课程创建能力，采用居中聚焦式布局，弱化冗余导航，引导用户快速发起学习。

界面自上而下分为两个功能区块：

-   课程创建交互区：页面核心区域，以对话式卡片承载输入能力：

    -   顶部为 AI 教师问候语与引导文案，附带 3
        组学习主题示例，降低用户输入门槛；

    -   中部为主题输入框，支持用户输入自然语言描述的学习需求；

    -   底部为参数控制栏与操作按钮，包含模型创造力等级调节、清空、语音开关等辅助功能，以及「深度交互」「进入课堂」核心操作按钮。

-   最近学习区：页面底部，以卡片形式展示用户的历史学习课程，卡片包含课程缩略预览、课程标题、学习进度与更新时间，支持一键续学。

## 4.2 智能课堂播放器界面

1 界面原图

![](media/image33.png){width="5.759027777777778in"
height="3.435416666666667in"}

2 界面说明

本界面是核心学习场景的主载体，对应F002 多模态内容生成引擎与F-Voice
语音功能集成模块的前端消费端，采用 "主内容区 + 侧边功能栏 + 底部对话栏"
的三段式布局，兼顾内容沉浸感与互动便捷性。

界面布局与核心能力如下：

-   顶部导航栏：左侧展示当前章节 /
    场景标题与返回按钮，右侧提供语言切换、视图模式切换、系统设置、内容导出等全局操作入口。

-   左侧主课件区：占页面约 70% 宽度，为核心内容展示区域，支持 PPT
    课件、思维导图、互动教材等多模态内容的渲染播放；底部内置播放控制栏，包含页码显示、倍速调节、翻页控制、全屏切换、内容编辑等功能。

-   右侧功能侧边栏：支持「笔记」「对话」双 Tab 切换：

    -   笔记
        Tab：按课件页码同步展示对应知识点的详细讲解文本，自动高亮当前页对应内容；

    -   对话 Tab：沉淀师生互动问答记录，支持 Q&A 筛选与历史回溯。

-   底部 AI 授课栏：常驻页面底部，展示 AI
    教师头像与实时授课文本，支持语音播放控制；右侧提供学生语音 /
    文字提问入口，实现边学边问的互动体验。

## 4.3 知识测验与答题报告界面

1 界面原图

![](media/image34.png){width="5.759027777777778in"
height="3.435416666666667in"}

2 界面说明

本界面承载课程分段知识点检验能力，对应F002
多模态内容生成引擎中的测验题目生成能力，整体布局延续课堂播放器的框架体系，保证学习体验的一致性。

界面核心设计如下：

-   整体沿用课堂播放器的 "顶部栏 + 主内容区 + 右侧栏 + 底部对话栏"
    布局框架，仅替换主内容区为测验答题内容，降低用户学习成本。

-   主内容区（答题报告区）：

    -   顶部为得分概览卡片，醒目展示总得分、题目总数、正确率环形进度，以及正确
        / 错误题数统计，同时提供「重新答题」操作入口；

    -   下方为逐题详情列表，展示题干、题型分值、选项列表，自动标注正确选项与错误选项，每道题下方附带详细的知识点解析。

-   右侧对话栏与底部 AI 授课栏保持常驻，用户答题过程中可随时向 AI
    教师发起知识点追问，错题可直接获取针对性讲解，实现 "测验 - 反馈 -
    补学" 的学习闭环。

# 5 出错处理设计

本系统在设计阶段充分考虑了各种可能的错误场景，制定了相应的处理策略。

**（1）LLM API调用失败**

错误场景：LLM API不可用、超时或返回异常响应。

处理策略：

a\) 自动重试机制：API调用失败时自动重试最多3次，采用指数退避策略。

b\)
备选提供商切换：主选Provider（DeepSeek）不可用时，自动切换至备选Provider（通义千问）。

c\) 预生成缓存保障：已生成的课程内容存储在数据库和文件系统中，不受LLM
API状态影响。

d\)
用户友好提示：生成失败时通过WebSocket向前端推送错误信息，前端展示明确的错误提示和重试按钮。

**（2）内容生成质量不达标**

错误场景：LLM生成的课程内容质量不符合预期（内容不完整、逻辑不连贯、知识点覆盖不足等）。

处理策略：

a\)
结构化Prompt工程：通过精心设计的Prompt模板和输出格式约束，提高生成内容的一致性和质量。

b\)
输出校验机制：对生成内容进行基本的结构校验（JSON格式验证、必填字段检查等）。

c\)
人工可编辑：知识图谱和课程大纲支持手动编辑，用户可对LLM生成结果进行审核和修正。

d\) 课程重建功能：支持对不满意课程的全部或部分内容进行重新生成。

**（3）数据库操作异常**

错误场景：数据库连接失败、写入超时、数据完整性约束违反等。

处理策略：

a\)
SQLAlchemy连接池管理：使用连接池自动管理数据库连接，支持连接超时和重连。

b\) 事务回滚：关键写操作使用数据库事务，失败时自动回滚保证数据一致性。

c\) 数据备份：定期备份SQLite数据库文件（或MySQL数据库），防止数据丢失。

d\) 错误日志：所有数据库异常记录详细日志，便于问题排查。

**（4）文件系统操作异常**

错误场景：磁盘空间不足、文件权限错误、路径不存在等。

处理策略：

a\) 预检查：写入文件前检查磁盘剩余空间和目录权限。

b\) 自动创建目录：写入前自动创建所需的目录结构。

c\)
清理策略：提供课程删除功能，同步清理关联的静态资源文件，防止磁盘空间浪费。

d\)
优雅降级：静态资源写入失败时，系统仍可通过数据库中的结构化数据提供基本的文本内容展示。

**（5）前端运行时异常**

错误场景：浏览器兼容性问题、JavaScript运行时错误、网络请求失败等。

处理策略：

a\) 浏览器兼容性：目标支持Chrome 90+、Edge 90+、Firefox 88+，使用Vue
3和Element Plus的内置兼容性处理。

b\) 全局错误捕获：使用Vue
3的errorHandler全局捕获未处理的组件错误，显示友好的错误提示页面。

c\)
网络请求重试：Axios拦截器中实现请求失败自动重试（最多2次）和超时处理。

d\) Loading状态：所有异步操作显示Loading状态，避免用户重复操作。

e\) 离线提示：网络断开时显示离线提示信息，网络恢复后自动重连WebSocket。

**（6）WebSocket连接异常**

错误场景：WebSocket连接断开、消息丢失等。

处理策略：

a\)
自动重连：WebSocket断开后自动尝试重连，采用指数退避策略（初始1秒，最大30秒）。

b\) 心跳机制：客户端定期发送心跳包，服务端响应确认连接状态。

c\) 状态同步：重连成功后，客户端请求最新的生成进度状态，确保UI显示正确。

d\)
降级方案：WebSocket不可用时，前端定时轮询HTTP接口获取进度（降级策略）。
