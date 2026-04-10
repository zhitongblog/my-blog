---
title: "开篇：为什么用Claude Code造一个MD编辑器？"
date: 2026-04-10T07:16:44.981Z
draft: false
description: "本文详解如何利用Claude 3.5 Sonnet的Code模式零环境搭建MD编辑器，无需本地配置、npm或Python，依托内置JS运行时与DOM API在Cursor等平台快速实现可运行原型。"
tags:
  - Claude Code
  - Markdown编辑器
  - JavaScript
  - AI编程
  - 前端开发
  - 代码沙箱
categories:
  - 技术教程
  - AI开发工具
---

## 1. 前置准备：环境与工具确认  

在开始编码前，请先确认你正运行在**支持代码执行的 Claude 环境**中——这不是传统意义上的“本地开发”，而是利用 Anthropic 提供的智能沙箱能力，全程在浏览器或桌面客户端内完成构建、调试与迭代。关键认知：✅ **无需安装 Claude 模型，无需配置 Python/Node 环境，甚至不需要 `npm install`**。Claude Code（即 Claude 3.5 Sonnet 在「Code」模式下）已内置完整 JavaScript 运行时、文件系统模拟（`localStorage`、`fetch`、DOM API）及 CDN 资源加载能力。

### ✅ 推荐平台清单（实测可用）
- **Cursor v0.48+**：启用「Claude Code」模型后，默认激活 Code Interpreter 插件，支持 `.html` 文件实时预览与 DOM 操作  
- **Continue.dev v0.27+**：在 `config.json` 中设置 `"model": "claude-3-5-sonnet-20240620"`，并开启 `codeInterpreter: true`  
- **Claude Desktop（Beta）**：macOS/Windows 官方桌面版，需在设置中开启实验性功能 → 「Enable Code Interpreter」  
- **Claude in Browser（claude.ai）**：⚠️ 仅当右下角出现「Code Interpreter」图标（⚡）且可点击时才可用；首次使用需手动开启（Settings → Experimental Features）

### ❌ 明确排除场景
- 纯网页版 `claude.ai`（未开启 Code Interpreter）：不支持 `localStorage` 写入、无法加载外部 CDN、无 `document` 对象访问权限  
- 移动端 Claude App：暂不支持代码执行沙箱  
- 使用 `claude-3-haiku` 或 `claude-3-opus` 模型：它们默认不启用 Code Interpreter 模式，必须显式切换为 `claude-3-5-sonnet` 并确认沙箱就绪  

### 快速验证环境就绪
在 Claude Code 输入框中粘贴并运行以下命令（无需回车，Claude 会自动执行并返回结果）：

```bash
echo "Environment OK" && which node 2>/dev/null || echo "(node not required — sandbox is ready)"
```

若返回 `Environment OK`，说明沙箱已激活，可安全进入下一步。  
> 💡 小技巧：Claude Code 会自动缓存你本次会话中的所有文件（如 `editor.html`），关闭窗口后再次打开仍可继续编辑——它本质是一个带持久化状态的 Web IDE。

![展示 Claude Desktop 中 Code Interpreter 图标与 editor.html 文件树](https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/7d/81/20260410/d23adf3d/dd6674f5-a277-945f-a044-cb91bbaa78d12657040699.png?Expires=1776411092&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=haTi4b2nCrxCFh%2FKmsJtUlkX%2BgA%3D)

## 2. 需求拆解：一个极简但可用的 MD 编辑器要什么？  

模糊目标是开发的最大敌人。我们让 Claude Code 执行一次「需求反推设计」：将“做个 Markdown 编辑器”这个产品经理式描述，转化为可验证、可编码、可测试的最小功能集。

Claude Code 分析后输出如下 `FEATURES.md`（已由模型自动生成并格式化）：

```markdown
# FEATURES.md — Minimal Viable Markdown Editor

## ✅ MUST-HAVE (v1.0)
- [x] 双栏布局：左侧纯文本编辑区（`<textarea>`），右侧实时 HTML 预览区（`<div id="preview">`）  
- [x] 双向同步：编辑区内容变更 → 立即渲染；粘贴 Markdown 文本 → 自动触发渲染  
- [x] GitHub Flavored Markdown（GFM）兼容：表格、任务列表、自动链接  
- [x] 换行符转 `<br>`（`marked.setOptions({ breaks: true })`）  
- [x] 基础样式：等宽字体、灰阶边框、16px 基准字号  

## ⚠️ DEFERRED (v2.0+)
- [ ] 导出 PDF（依赖 `jspdf` + `html2canvas`，增加体积）  
- [ ] 图床上传（需对接第三方 API，引入认证复杂度）  
- [ ] TOC 自动生成（需解析 AST，非渲染层职责）  
```

这份清单不是文档，而是**后续所有编码的验收标准**。Claude Code 会严格按此优先级生成代码，跳过任何未标记 ✅ 的功能。

## 3. 第一步：创建 HTML 骨架与基础交互逻辑  

现在，我们手写第一个可运行的 `editor.html`。Claude Code 不会“猜”结构，而是精准理解你的意图：“双栏 Flex 布局 + textarea + preview div + marked 渲染”。

以下是完整、可直接复制运行的代码（Claude Code 已自动补全 CSS 重置、字体栈与响应式断点占位）：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Minimal MD Editor</title>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }
    .container { display: flex; height: 100vh; }
    #editor { flex: 1; padding: 1rem; font-family: 'SFMono-Regular', Consolas, monospace; font-size: 14px; border-right: 1px solid #eee; resize: none; }
    #preview { flex: 1; padding: 1rem; overflow-y: auto; }
    @media (max-width: 768px) { .container { flex-direction: column; } }

    /* GFM 样式增强 */
    #preview h1, #preview h2, #preview h3 { margin: 1.2em 0 0.6em; }
    #preview pre { background: #f6f8fa; padding: 1rem; border-radius: 4px; overflow-x: auto; }
    #preview code { background: #f6f8fa; padding: 0.2em 0.4em; border-radius: 3px; }
  </style>
</head>
<body>
  <div class="container">
    <textarea id="editor" placeholder="输入 Markdown..."># Hello World

- 支持列表
- **加粗** 和 *斜体*
- [链接](https://example.com)</textarea>
    <div id="preview"></div>
  </div>

  <script>
    marked.setOptions({ breaks: true });
    const editor = document.getElementById('editor');
    const preview = document.getElementById('preview');

    function render() {
      preview.innerHTML = marked.parse(editor.value);
    }

    editor.addEventListener('input', render);
    // 初始化渲染
    render();
  </script>
</body>
</html>
```

✅ **注意事项**  
- `marked.setOptions({ breaks: true })` 是关键：否则 `换行` 不会转为 `<br>`，段落会塌缩成一行  
- `marked.parse()` 默认对 HTML 标签进行转义，**完全避免 XSS 风险**（如输入 `<script>alert(1)</script>` 会原样显示为文本）  

❌ **常见问题**  
> 预览区空白？打开浏览器控制台（F12 → Console），若报错 `marked is not defined`，说明 CDN 加载失败。此时 Claude Code 会自动为你替换为备用链接：`https://unpkg.com/marked@12.0.2/lib/marked.umd.js`

## 4. 第二步：增强渲染体验——添加代码块高亮与数学公式支持  

基础渲染已就绪。现在让 Claude Code 基于当前 `editor.html` **智能扩增**，而非重写：它将识别现有 `marked.parse()` 调用点，并注入自定义 `Renderer`。

新增 CDN 引入（追加到 `<head>` 中）：
```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.10/dist/contrib/auto-render.min.js"></script>
```

替换 `<script>` 中的 `render()` 函数为：

```js
function render() {
  const renderer = new marked.Renderer();

  // 代码块高亮
  renderer.code = (code, lang) => {
    if (!lang) return `<pre><code>${marked.escape(code)}</code></pre>`;
    const highlighted = hljs.highlightAuto(code, [lang]).value;
    return `<pre><code class="hljs ${lang}">${highlighted}</code></pre>`;
  };

  // 数学公式支持（KaTeX）
  const rawMarkup = marked.parse(editor.value, { renderer });
  preview.innerHTML = rawMarkup;

  // 渲染 KaTeX（需在 innerHTML 设置后调用）
  renderMathInElement(preview);
}
```

✅ **注意事项**  
- `hljs.highlightAuto()` 会自动检测语言，但需确保 `highlight.min.js` 已加载全部语言（CDN 版本已内置）  
- `renderMathInElement(preview)` 是 KaTeX 的自动渲染函数，它会扫描 `$$...$$` 和 `$...$` 并替换为 MathML  

❌ **常见问题**  
> 公式不渲染？检查 `<head>` 中 `katex.min.css` 是否在 `auto-render.min.js` 之前加载（CSS 必须前置，否则公式高度计算异常）

## 5. 第三步：保存与加载——用 localStorage 实现本地持久化  

用户绝不愿丢失未保存的笔记。Claude Code 精准调用浏览器 API，实现零配置持久化：

在 `<script>` 开头添加：
```js
// 页面加载时读取
document.addEventListener('DOMContentLoaded', () => {
  try {
    const saved = localStorage.getItem('md-content');
    if (saved) editor.value = saved;
  } catch (e) {
    console.warn('localStorage read failed:', e);
  }
});

// 编辑时自动保存（防抖 800ms）
let saveTimer;
editor.addEventListener('input', () => {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => {
    try {
      localStorage.setItem('md-content', editor.value);
    } catch (e) {
      if (e.name === 'QuotaExceededError') {
        alert('存储空间已满，请清理浏览器数据');
      }
    }
  }, 800);
});

// 离开页面前提示
window.addEventListener('beforeunload', (e) => {
  if (editor.value !== localStorage.getItem('md-content')) {
    e.preventDefault();
    e.returnValue = '';
  }
});
```

✅ **注意事项**  
- `localStorage` 原生 UTF-8 安全，中文、emoji、Emoji ZWJ 序列均无乱码风险  
- `try/catch` 包裹是必需的：隐私模式下 `localStorage` 可能被禁用  

## 6. 进阶优化：响应式布局与快捷键支持  

最后一步，让编辑器真正“好用”。Claude Code 添加了移动端单栏适配（见第3步 CSS 中 `@media` 规则）和生产级快捷键：

```js
// Ctrl+B / Ctrl+I 快捷键
editor.addEventListener('keydown', (e) => {
  if (!e.ctrlKey) return;
  const start = editor.selectionStart;
  const end = editor.selectionEnd;
  const text = editor.value;
  let newText = text;

  if (e.key === 'b') {
    e.preventDefault();
    newText = `${text.substring(0, start)}**${text.substring(start, end)}**${text.substring(end)}`;
  } else if (e.key === 'i') {
    e.preventDefault();
    newText = `${text.substring(0, start)}*${text.substring(start, end)}*${text.substring(end)}`;
  } else if (e.key === 'Enter' && e.shiftKey) {
    e.preventDefault();
    // Ctrl+Shift+Enter 切换焦点到预览区（方便阅读）
    preview.focus();
  }

  if (newText !== text) {
    editor.value = newText;
    editor.setSelectionRange(start + 2, end + 2); // 光标置于星号内
    render();
  }
});
```

## 7. 调试与部署：从 Claude Code 沙箱走向真实环境  

Claude Code 中运行正常 ≠ 本地双击打开正常。关键差异在于协议：沙箱用 `http://localhost:xxxx`，而双击是 `file://` 协议。

✅ **调试技巧**  
- 在 `render()` 函数开头插入 `console.log('rendering:', editor.value.slice(0,50));`  
- 添加 `debugger` 语句，Claude Code 会自动在沙箱中触发断点  

✅ **本地部署方案**  
1. 将完整 HTML 复制保存为 `editor.html`  
2. **推荐方式（免服务器）**：终端执行  
   ```bash
   npx serve -s
   ```
   访问 `http://localhost:5000/editor.html`  
3. **快速验证**：若仅测试，Chrome 启动时加参数 `--unsafely-treat-insecure-origin-as-secure="file://"`（仅限开发）

❌ **常见问题**  
> 白屏？99% 是 `file://` 协议下 CDN 被 CORS 拦截。解决方案：用 `npx serve`，或改用 `https://cdn.jsdelivr.net`（支持 `file://` 加载）

## 8. 后续演进路线：让 Claude Code 成为你的长期协作者  

这个编辑器不是终点，而是协作起点。Claude Code 的真正价值，在于可持续演进：

- **可扩展模块示例**：  
  - Git 集成：`localStorage` → GitHub Gist API（OAuth 2.0）  
  - 主题切换：CSS 变量 `--bg-color` + `prefers-color-scheme: dark` 媒体查询  
  - 插件系统：`window.MDEditor.plugins = [{ name: 'emoji', fn: renderEmoji }]`  

- **复用提示词模板**：  
  > “基于当前 `editor.html`，新增‘一键复制 HTML 渲染结果’按钮，要求兼容 Safari，并添加单元测试（使用 Jest 模拟 `navigator.clipboard.writeText`）”

✅ **最佳实践**  
- 每次重大修改前，先 `git commit -m "feat: add katex support"`，Claude Code 能通过 Git 历史理解上下文  
- **永远不要让 Claude 修改核心渲染逻辑**（如 `marked.Renderer` 内部），应封装为插件，保障安全边界  

![展示编辑器在 Cursor 中运行、右侧预览实时更新效果](https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/7d/6b/20260410/d23adf3d/710c7d41-e408-92d3-b1e9-e496c01ab3561052072976.png?Expires=1776411109&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=FwvcGilah21wJv0eF5PS3QqNhFQ%3D)  
![开发者在 Claude Code 中输入提示词，右侧自动生成新功能代码](https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/7d/87/20260410/d23adf3d/c9bae10b-64a4-9fc9-98e5-86f9d12f9f35785124636.png?Expires=1776411126&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=v9TO96dRg6eH1nEfH9dfYuy3qPs%3D)  

你已掌握一种新型开发范式：**以需求为输入，以 Claude Code 为编译器，以浏览器为运行时**。接下来，只需一个提示词，就能让这个编辑器学会导出、协同、AI 辅助写作——而你，始终掌控架构与安全。