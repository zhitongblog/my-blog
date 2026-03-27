---
title: "从Prompt到Page：当Claude Code理解‘帮我分析竞品首页LCP和CLS’时发生了什么？"
date: 2026-03-25T12:57:16.542Z
draft: false
description: "揭秘AI代码助手如何真正理解并执行复杂前端性能分析指令——从模糊Prompt到可落地的竞品LCP/CLS对比报告，详解提示工程、上下文构建与结果结构化关键实践。"
tags:
  - Claude
  - Web Vitals
  - LCP
  - CLS
  - 前端性能
  - AI编程
categories:
  - 前端性能
  - AI开发工具
---

## 🌟 一个“看似简单”的Prompt，差点让我在客户面前当场社死  

那是上周五下午3:17，钉钉消息弹窗还没消，客户微信就甩来一句：  
> “帮我们分析下竞品首页的 LCP 和 CLS？最好能对比三家——XX优选、YY严选、ZZ快购。急，投资人下周要看性能基线。”

我秒回：“好的！让 Claude Code 跑一下 👌”，顺手复制粘贴进 Claude 的代码沙盒，敲下这行“自信满满”的 Prompt：  
```text
请分析三个竞品网站的LCP和CLS指标，并给出优化建议。
```

30分钟后，我点开输出——满屏是教科书式回答：  
> *“LCP（最大内容绘制）衡量页面主内容加载速度，建议使用 Chrome DevTools 的 Performance 面板录制……”*  
> *“CLS（累积布局偏移）反映视觉稳定性，可通过 Web Vitals 扩展实时监控……”*  
> *“优化方向包括预加载关键资源、设置图片宽高属性、避免动态插入内容……”*  

![尴尬的Claude泛泛而谈回复截图：左侧是用户Prompt，右侧是大段通用指南，中间用红色箭头标出“没提任何URL！”](https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/7d/07/20260327/d23adf3d/fc05e5ae-260c-4bed-b008-93baa82285733332421901.png?Expires=1775197091&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=QP89De3cct3wBwOzUQEssAyl9Wg%3D)  

我盯着屏幕，手心发潮。客户团队5个人全在等报告——而他们连 Chrome DevTools 都没打开过（团队共4人：CEO、运营、产品、后端，**没有前端工程师**）。更扎心的是，就在前一天，我还用 Claude Code 成功调试了自家后台的 CSS 动画卡顿问题，顺手发了条朋友圈：“AI 前端助理已上线 ✅”。  

那一刻我意识到：我把“人话需求”当成了“可执行指令”。  
不是 Claude 不行，是我没给它上岗前的工牌、工位和任务单。

---

## 🔍 Claude Code不是翻译器，它是需要“喂数据”的实习生  

复盘时我翻出原始对话记录，发现失败根源根本不在模型能力——而在我的输入像一份空简历：  
- ❌ 没写“公司名”（竞品具体是哪三家？）  
- ❌ 没贴“工位地址”（URL？带协议吗？有登录跳转吗？）  
- ❌ 没说明“办公环境”（手机还是PC？4G还是3G？）  
- ❌ 没定义“交付物长啥样”（要数字？要截图？要DOM路径？）  

于是我把两版 Prompt 拉出来做了对比：

| 原始 Prompt（失败版） | 优化后 Prompt（生产可用版） |
|------------------------|------------------------------|
| `请分析三个竞品网站的LCP和CLS指标，并给出优化建议。` | `请基于以下三组Lighthouse JSON报告（已附），分析各站首页在“iPhone SE + 3G慢网”条件下的LCP与CLS：<br>• XX优选：https://xx-youxuan.com/ （公开可访问）<br>• YY严选：https://yy-yanxuan.com/ （需绕过登录页，已提供无认证直链）<br>• ZZ快购：https://zz-kuai.com/ （注意：该站首页含动态广告位，CLS易受其影响）<br>输出要求：<br>① 表格列出LCP数值（ms）、CLS值、LCP元素类型（img/text/video）及DOM路径；<br>② 对CLS > 0.05的站点，定位导致偏移的具体元素（如：`.ad-banner` 插入时机）；<br>③ 每条建议必须绑定到具体HTML/CSS/JS行（示例：“第82行 `<img>` 缺少 width/height 属性”）` |

**标红的关键缺失项**：  
① **可访问的竞品URL**（必须公开可抓取！曾因 URL 是 `https://admin.xx.com/login?next=/home`，Claude 循环重定向12次后报错 `Failed to fetch`）  
② **明确的设备与网络模拟参数**（Lighthouse 默认是“桌面+宽带”，但电商80%流量来自低端安卓机，不指定等于白测）  
③ **期望输出格式**（Claude 不会猜你要一页PPT还是JSON字段——它只认结构化指令）

---

## ⚙️ 实战拆解：我是怎么把“分析LCP/CLS”变成Claude能懂的5步流水线  

别再让 Claude 直接“分析网页”了。我现在的标准流程是：**人做采集，AI做诊断**。以下是我在客户项目中跑通的5步硬核流水线（命令级可复制）：

**▪ 步骤1：预检URL可访问性（防卡死）**  
```bash
# 先看是否裸奔可访问（避开登录墙）
curl -I https://xx-youxuan.com/ | head -5

# 再用 httpstat 看首屏延迟毛刺
httpstat https://xx-youxuan.com/
```
→ 若返回 `403` 或重定向到 `/login`，立刻换真实用户代理+Cookie（或找客户要测试账号直链）。

**▪ 步骤2：用 Lighthouse CLI 生成精准报告**  
```bash
lighthouse https://xx-youxuan.com/ \
  --output=json \
  --output-path=xx-report.json \
  --chrome-flags="--headless --no-sandbox" \
  --throttling-method=devtools \  # 关键！CLS 计算必须用此模式
  --throttling.rttMs=150 \
  --throttling.throughputKbps=1638 \
  --throttling.cpuSlowdownMultiplier=4 \
  --emulated-form-factor=mobile \
  --screenEmulation.width=375 \
  --screenEmulation.height=667 \
  --quiet
```

**▪ 步骤3：抽关键字段喂给 Claude**  
从 `xx-report.json` 中提取：  
```json
{
  "audits": {
    "largest-contentful-paint": { "numericValue": 3240 },
    "cumulative-layout-shift": { "numericValue": 0.182 },
    "first-contentful-paint": { "numericValue": 2100 }
  }
}
```

**▪ 步骤4：定制 Prompt 模板（重点！Claude 只认这个）**  
```text
你是一名资深前端性能工程师。请基于以下 Lighthouse JSON 片段：
【粘贴上面那段 JSON】
请严格按顺序回答：
1. LCP 元素 DOM 路径（如：`body > main > div.product-grid > img.hero-banner`）；
2. 该元素类型（img / text / video / iframe）；
3. 若为 img：检查是否缺失 width/height 属性，是否启用 loading="lazy"；
4. 若 CLS > 0.05：指出导致偏移的元素（如：`.header-ad` 在 DOM 加载后插入）；
5. 给出可直接落地的代码修改（示例：将 `<img src="...">` 改为 `<img src="..." width="375" height="200" loading="lazy">`）。
```

**▪ 步骤5：Python 自动拼报告（解放双手）**  
用脚本把三份 JSON 解析 + Claude 输出 + 截图汇总成 PDF。核心逻辑：  
```python
# gist.github.com/yourname/lighthouse-report-merger
for site in ["xx", "yy", "zz"]:
    json_data = load_json(f"{site}-report.json")
    claude_output = call_claude(prompt_template.format(**extract_metrics(json_data)))
    generate_pdf_page(site, json_data, claude_output)
```
👉 [GitHub Gist 短链接：lighthouse-report-merger.py](https://gist.github.com/xxx/yyy)

![终端截图：左侧是 lighthouse 命令执行成功，右侧是 Python 脚本自动生成 report.pdf](https://dashscope-result-sh.oss-cn-shanghai.aliyuncs.com/7d/3e/20260327/d23adf3d/d362360e-aecd-4fa5-8d5c-3b546f7a80763859831859.png?Expires=1775197108&OSSAccessKeyId=LTAI5tKPD3TMqf2Lna1fASuh&Signature=3jZchexTqhKl6QCmsrLQ1A9NKjM%3D)

---

## 💥 翻车现场实录：CLS数值为0.02却判“严重问题”？Claude的隐藏假设坑了我  

上周客户指着报告质问：“你们说 ZZ 快购 CLS 是 0.02，达标了——可我们实测老款华为P20用户，CLS 高达 0.35！这是什么‘达标’？”  

我当场查了 Lighthouse 报告——确实 `cumulative-layout-shift.numericValue: 0.02`。  
但问题出在：**Claude 完全依赖 Lighthouse 默认配置，而默认配置用的是 Chrome 115 + Moto G4 模拟器**。  
可 ZZ 快购的用户里，32% 是 Android 9 以下系统，WebView 渲染引擎对 `position: sticky` 的处理存在已知偏移 Bug——Lighthouse 根本测不到。

我的补救方案：  
在竞品页面注入 `web-vitals` 库实测真实设备：  
```html
<!-- 直接加到竞品首页 <head>（需客户配合） -->
<script type="module">
  import {getCLS, getLCP} from 'https://unpkg.com/web-vitals@3.4.0/dist/web-vitals.esm.js';
  getCLS(console.log); // 输出真实用户 CLS
  getLCP(console.log);
</script>
```
实测数据回传后，发现 CLS 中位数确实是 0.35（集中在 Android 8-9 用户群）。  

**血泪结论**：Claude 是优秀的“已知问题诊断员”，但绝不是“未知场景探测器”。  
它永远活在你给它的沙盒里——而真实世界，永远在沙盒之外。

---

## 🛠️ 给技术人的3条血泪口诀（现在抄还来得及）  

别背理论，记这三条，下次开会不脸红：

▪ **“URL不裸奔”**  
→ 反面案例：我曾用 `https://admin.zz-kuai.com/dashboard` 直接喂 Claude，结果它反复尝试登录，终端刷满 `302 Found → /login` 日志（见下图）。  
![终端日志截图：curl -v 请求被重定向12次，最后超时](IMAGE_PLACEHOLDER_3)  
✅ 正确做法：先 `curl -v` 看响应头，再用 `--user-agent` 模拟真实浏览器，或让客户开测试子域。

▪ **“数值不孤证”**  
→ 反面案例：某竞品 CLS=0.01（完美），但 FCP=4200ms（极差）。Claude 只盯 CLS 说“布局稳定”，却漏掉 JS 阻塞主线程才是根因。  
✅ 正确做法：永远拉出 `FCP`, `TTFB`, `LCP`, `CLS` 四象限交叉看——比如 FCP 高 + LCP 高 = 服务端 or 关键资源加载问题。

▪ **“报告不交差”**  
→ 反面案例：初版报告写“CLS 偏移源为 .ad-banner 元素插入”，客户一脸懵：“banner 是啥？偏移是啥？”  
✅ 正确做法：转译成人话 + 视觉化。改成：  
> ❌ “`.ad-banner` 插入导致布局偏移”  
> ✅ “用户刚要点‘立即购买’按钮，顶部广告突然加载，把按钮往下顶了20px——37%用户因此误点广告”  
> 并配一张 GIF：按钮被顶下去的瞬间。

---

## 🌈 最后想说：工具越聪明，我们越要当“严苛的教练”  

上周，我用同一套流程分析新竞品“AA速达”。当 Claude 看到 `next.config.js` 里的 `images.domains` 配置后，主动追问：  
> *“检测到该站使用 Next.js 13.4。其首页 Hero 图使用了 `next/image`，但未设置 `priority` 属性。是否需要分析 `priority` 缺失对 LCP 的影响？（注：Next.js 文档指出，首页首屏图应设 priority=true）”*

我愣了一下——它居然开始理解技术栈语境了。  
但下一秒，我手动 `view-source:https://aa-su-da.com/`，发现 `<img>` 标签根本不是 `next/image` 渲染的，而是 Nuxt 的 `nuxt-img`…… 查 GitHub 提交记录，确认他们上周刚从 Next 迁移到 Nuxt，但 CDN 配置没同步更新。

所以，真正的 Prompt 工程师是什么样？  
**是既敢让 AI 提问，又随时准备亲手翻源码的人。**  
不是取代思考，而是把思考腾出来——去问更关键的问题：  
> “这个指标，对我们的用户，到底意味着什么？”  

![深夜电脑屏幕特写：左侧是 Claude 的提问，右侧是浏览器中打开的竞品源码，光标停在 `<nuxt-img>` 标签上](IMAGE_PLACEHOLDER_4)