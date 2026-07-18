# PKIA — Personal Knowledge Intelligence Agent

> PKIA automatically collects, evaluates, organizes and generates daily AI technology reports in Markdown with one command.

PKIA 是一个基于开源平台 [Dify](https://dify.ai) 构建的个人知识智能体系统，能自动从 GitHub Trending 采集项目，通过 AI Workflow 进行分析评分，最终输出一份可读的 Markdown 技术日报。

## 快速开始
```bash
python run.py
```
一条命令完成采集、AI 分析、日报生成并自动打开。

## 版本
当前版本：v0.1.0 (MVP)

## 架构
三层记忆系统（L1 宪法 → L2 Governor → L3 进度文件）+ Fat Object Pipeline

## 链接
- 项目状态：[CURRENT_STATUS.md](CURRENT_STATUS.md)
- 变更日志：[CHANGELOG.md](CHANGELOG.md)
- 设计基线：[docs/pkia_v0.1_baseline.md](docs/pkia_v0.1_baseline.md)
