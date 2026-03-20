# InfoBar - 项目信息条工具

单行多列信息条，置顶显示项目信息。

## 安装

```bash
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

## 功能

- 窗口置顶显示
- 仅在终端窗口激活时自动显示，切到其他窗口时自动隐藏
- 单击拖动移动窗口位置
- 双击列文字进入编辑模式
- 拖动列之间的分隔线调整列宽
- 右键菜单打开主题设置
- 支持窗口透明，可透视背后内容
- 自动保存所有配置到 JSON

## 操作说明

- **单击并拖动**：移动窗口位置
- **双击列文字**：进入编辑模式，修改内容
- **编辑完成后点击其他地方**：退出编辑模式
- **拖动列分隔线**：调整列宽
- **右键**：打开菜单，进入主题设置

## 主题设置

右键点击窗口，选择"主题设置"，可调整：
- 背景颜色
- 背景透明度（支持近全透明）
- 文字颜色
- 文字透明度

## 前台窗口联动

InfoBar 仅在终端窗口处于前台时显示，切到其他窗口时自动隐藏。基于 Windows `SetWinEventHook` 事件驱动，窗口切换时即时响应。

默认识别的终端：Windows Terminal、cmd、PowerShell、Git Bash (mintty)、ConEmu、Alacritty、WezTerm 等。可在 `focus_monitor.py` 的 `DEFAULT_TERMINAL_PROCESSES` 中自定义。

如遇 Alt+Tab 等场景偶尔不触发，可在 `focus_monitor.py` 开头将 `FALLBACK_POLL_INTERVAL_MS` 设为 `3000`（毫秒）启用低频兜底定时器。
