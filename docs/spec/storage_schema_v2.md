# Storage Schema v2.0

PKIA 数据存储格式规范。每条记录为 JSONL 中的一行 JSON 对象。

## 完整结构

```json
{
  "schema_version": "2.0",
  "batch_id": "BATCH-...",
  "project_data": { ... },
  "analysis": { ... },
  "pipeline_status": "ANALYZED",
  "pipeline": {
    "workflow_id": "uuid",
    "workflow_version": "1.0",
    "stages": {
      "collected_at": "ISO 8601",
      "analyzed_at": "ISO 8601"
    }
  },
  "metadata": {
    "created_at": "ISO 8601",
    "updated_at": "ISO 8601"
  }
}
```

## 字段说明

| 字段 | 类型 | 必填 | 描述 |
|------|------|------|------|
| schema_version | string | ✅ | 固定 "2.0"，用于区分格式版本。v1 记录无此字段 |
| batch_id | string | ✅ | 采集批次标识 |
| project_data | object | ✅ | 原始项目数据（字段名不变，与 v1 兼容） |
| analysis | object | ❌ | AI 分析结果，未分析时字段缺失 |
| pipeline_status | string | ✅ | 管道状态：COLLECTED / ANALYZED / COMPLETED |
| pipeline | object | ✅ | 管道运行时信息 |
| pipeline.workflow_id | string | ✅ | Dify Workflow 运行 ID |
| pipeline.workflow_version | string | ✅ | Workflow 版本号，来自 PKIA_WORKFLOW_VERSION 环境变量 |
| pipeline.stages.collected_at | string | ✅ | 采集完成时间（复用 project_data.collection_time） |
| pipeline.stages.analyzed_at | string | ✅ | 分析完成时间 |
| metadata | object | ✅ | 记录级元数据 |
| metadata.created_at | string | ✅ | 记录首次写入时间 |
| metadata.updated_at | string | ✅ | 记录最后更新时间 |

## 与 v1 的区别

- 新增 schema_version 字段用于格式识别
- 新增 pipeline 对象，集中管理管道运行时信息
- 新增 metadata 对象，记录时间戳
- project_data 和 analysis 字段名及结构保持不变，确保 Reporter 无需修改即可兼容
- 旧记录 (v1) 不存在 schema_version，Reporter 通过字段存在性自动区分
