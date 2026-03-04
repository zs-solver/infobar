# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

InfoBar 是一个基于 PyQt5 的桌面工具，显示可自定义的置顶信息条，支持可编辑的多列显示。用于持久显示项目状态信息（如项目名称、状态、分支）。

## 运行程序

```bash
pip install -r requirements.txt
python main.py
```

## 架构设计

代码采用模块化架构，职责分离清晰：

- **main.py**: 程序入口，初始化 QApplication 和 InfoBar
- **info_bar.py**: 主窗口类 (InfoBar)，协调所有组件
- **widgets.py**: EditableField 组件 - 默认只读的 QLineEdit，双击进入编辑模式
- **storage.py**: Storage 类处理 JSON 配置持久化（列数据、窗口位置、主题）
- **theme.py**: ThemeManager 将主题配置转换为支持 RGBA 的 CSS 样式表

## 配置系统

程序使用 `config.json` 持久化配置（自动生成，已加入 gitignore）：
- 列数据（名称和内容）
- 窗口位置和大小
- 主题设置（背景色、背景透明度、文字色、文字透明度）

配置在启动时通过 Storage.load() 加载，自动保存时机：
- 窗口关闭时 (closeEvent)
- 字段内容变化时 (contentChanged 信号)

## 关键交互模式

EditableField 实现了双模式交互：
- **只读模式**: 鼠标事件被忽略 (event.ignore())，允许父窗口拖动
- **编辑模式**: 双击触发，启用文本编辑
- 失去焦点时 (focusOut) 自动切换回只读模式

这个模式解决了窗口拖动和文本编辑的冲突问题。

## 主题自定义

修改 `config.json` 的 theme 部分：
```json
"theme": {
  "bg_color": "#2b2b2b",
  "bg_opacity": 1.0,
  "text_color": "#ffffff",
  "text_opacity": 1.0
}
```

ThemeManager.get_stylesheet() 将十六进制颜色转换为 Qt 样式表的 RGBA 格式。
