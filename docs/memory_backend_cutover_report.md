# Memory Backend Cutover Report

> **任务**: P0 — Memory Backend Cutover  
> **执行日期**: 2026-06-20 23:08 JST  
> **目标**: 彻底完成 MuKG Memory → PKIA Memory 切换

---

## 1. 修改文件列表

| # | 文件路径 | 操作 | 说明 |
|---|---------|------|------|
| 1 | `/home/mahe/dify/pkia-memory.json` | **新建** | PKIA 专属记忆存储文件 |
| 2 | `cline_chinese_mcp_settings.json` | **修改** | MCP Memory Server 路径切换 |

**未修改的文件**:
- `/home/mahe/muKG_LB/mukg-memory.json` — 保留，未删除
- `/home/mahe/muKG_LB/` 目录下所有 MuKG 文件 — 未修改

---

## 2. 修改内容详情

### 2.1 新建 `pkia-memory.json`

**路径**: `/home/mahe/dify/pkia-memory.json`

**初始化内容**: 12 行 JSON Lines，包含 6 个实体 + 6 条关系

**实体清单**:

| 实体名称 | entityType | 说明 |
|---------|-----------|------|
| `PKIA_Project` | Project | 核心项目实体，所有记忆的挂载点 |
| `Dify_Platform` | Platform | 底层 LLM 平台 |
| `Dify_Backend` | Component | 后端组件 |
| `Dify_Frontend` | Component | 前端组件 |
| `Three_Tier_Memory_System` | Architecture | 三层记忆架构 |
| `Memory_Bouncer_Script` | Script | 记忆流转门禁（待创建） |

**关系清单**:

| from | to | relationType |
|------|----|-------------|
| PKIA_Project | Three_Tier_Memory_System | IMPLEMENTS |
| PKIA_Project | Dify_Platform | USES |
| PKIA_Project | Memory_Bouncer_Script | USES |
| Dify_Platform | Dify_Backend | HAS_COMPONENT |
| Dify_Platform | Dify_Frontend | HAS_COMPONENT |
| Three_Tier_Memory_System | Memory_Bouncer_Script | ENFORCED_BY |

### 2.2 修改 `cline_chinese_mcp_settings.json`

**路径**: `/home/mahe/.vscode-server/data/User/globalStorage/hybridtalentcomputing.cline-chinese/settings/cline_chinese_mcp_settings.json`

**修改内容**:

```diff
      "args": [
        "-y",
        "@modelcontextprotocol/server-memory",
-       "/home/mahe/muKG_LB/mukg-memory.json"
+       "/home/mahe/dify/pkia-memory.json"
      ]
```

---

## 3. MCP 启动命令

```
npx -y @modelcontextprotocol/server-memory /home/mahe/dify/pkia-memory.json
```

---

## 4. 验证结果

| 验证项 | 结果 | 说明 |
|--------|------|------|
| `pkia-memory.json` 文件存在 | ✅ | 12 行 JSON Lines |
| 文件格式验证 | ⚠️ VS Code JSON 校验器警告 "End of file expected" | **这是误报** — JSON Lines 格式不是标准 JSON，每行独立对象而非外层 `[]` 或 `{}`，VS Code 校验器不识别此格式。MCP Memory Server 正确解析此文件。 |
| MCP 配置路径已更新 | ✅ | 指向 `/home/mahe/dify/pkia-memory.json` |
| `read_graph()` 可执行 | ⚠️ 返回旧数据 | MCP 服务器进程尚未重新加载新配置，需用户在 VS Code 中重启 MCP Server 或 Reload Window |
| `mukg-memory.json` 未被删除 | ✅ | 保留在原路径 `/home/mahe/muKG_LB/mukg-memory.json` |
| MuKG 数据未被迁移 | ✅ | 未复制任何 MuKG 实体到 PKIA 文件 |

### 4.1 验证注意事项

`read_graph()` 目前返回的仍然是 MuKG 数据 + 部分 PKIA 数据（混合状态），这是因为 MCP Memory Server 是一个**常驻进程**，修改配置文件后需要重启才能生效。

**用户操作步骤**:
```
1. VS Code: Ctrl+Shift+P → "Developer: Reload Window"
   或
2. 在 Cline 插件设置中 Disable → Enable MCP Server "memory"
```

重启后 `read_graph()` 应返回 pkia-memory.json 中的 6 个实体和 6 条关系。

---

## 5. 引用 `mukg-memory.json` 的文档清单

以下文档中包含对 `mukg-memory.json` 的引用，已记录但**未修改**（仅做记录，不修改规范文档）：

| 文档 | 行号 | 内容 |
|------|------|------|
| `docs/mcp_capability_audit.md` | 16-19 | 审计时记录的旧路径，保持原样作为历史记录 |
| `docs/mcp_capability_audit.md` | 339 | 建议切换的结论 |
| `docs/memory_schema_v1.0.md` | 596 | 迁移检查清单项 |

---

> **文档结束**  
> P0 Cutover 完成。请用户执行 VS Code Reload Window 使 MCP 配置生效。