# Mihomo Ruleset (MRS)

用于在 **Mihomo (Clash.Meta)** 中维护二进制规则集 (`.mrs`) 与明文规则列表 (`.txt`)，用于构建广告拦截、AI 代理路由等自定义分流规则。

---

## 路由列表构建与数据源

### 1. 广告拦截 (`ads.mrs` / `ads.txt`)

主要用于屏蔽常见广告域名、开屏广告、追踪统计与第三方广告 SDK。

* **上游数据源**：
1. [GOODBYEADS](https://github.com/8680/GOODBYEADS) (`data/rules/dns.txt`)
2. [anti-AD](https://github.com/privacy-protection-tools/anti-AD) (`anti-ad-domains.txt`)
3. [AWAvenue-Ads-Rule](https://github.com/TG-Twilight/AWAvenue-Ads-Rule) (`AWAvenue-Ads-Rule-Clash.yaml`)


* **构建过滤原则**：
* 剔除浏览器 ABP 规则语法行、注释、空行及纯 IP（视构建目标而定，通常纯域名规则集保留域名条目）。



---

### 2. AI 专用分流 (`ai.mrs` / `ai.txt`)

用于将主流大模型、代码助手及 AI 推理接口统一导向指定代理策略组，避免地区限制或延迟波动。

* **涵盖服务商**：
* **Anthropic / Claude / Claude Code** (`claude.ai`, `anthropic.com`, `claude.com`, `claude.site` 等相关域名与子域)
* **OpenAI** (ChatGPT、Sora、OpenAI API)
* **Google Gemini / DeepMind** (Gemini、AI Studio、Bard、NotebookLM)
* **Microsoft Copilot** (GitHub Copilot、Windows Copilot)
* **xAI (Grok)** (`grok.com`, `x.ai`, `grokipedia.com`)
* **Perplexity AI** (`perplexity.ai`, `pplx.ai`)
* **Groq / Midjourney / Poe / Windsurf / Cursor / MiniMax** 等


* **上游数据源**：
1. [v2fly/domain-list-community](https://github.com/v2fly/domain-list-community)（提取 `category-ai-!cn`）
2. [ACL4SSR](https://github.com/ACL4SSR/ACL4SSR) (`Clash/Ruleset/AI.list`)
3. [VPSDance/ai-proxy-rules](https://github.com/VPSDance/ai-proxy-rules) (`rules/clash/global.yaml`)
4. [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) (OpenAI / Claude / Anthropic / Gemini / Copilot)
5. [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat) (Perplexity / xAI / Groq / Anthropic)


* **构建过滤原则**：
* **去重合并**：对多源域名进行规范化与去重。
* **避免过度泛化**：慎用过于宽泛的根域名或第三方 CDN 域名（除非明确仅用于相关服务），防止误伤其他正常流量。



---

## Mihomo 配置示例

在 Mihomo (Clash.Meta) 的 `config.yaml` 中添加以下配置：

```yaml
rule-providers:
  ads:
    type: http
    behavior: domain
    format: mrs
    path: ./ruleset/ads.mrs
    url: "https://raw.githubusercontent.com/linkproxy-net/mihomo-mrs/main/ads.mrs"
    interval: 86400

  ai:
    type: http
    behavior: domain
    format: mrs
    path: ./ruleset/ai.mrs
    url: "https://raw.githubusercontent.com/linkproxy-net/mihomo-mrs/main/ai.mrs"
    interval: 86400

rules:
  - RULE-SET,ads,REJECT
  - RULE-SET,ai,AI 专用
  # 其他分流规则...
  - MATCH,最终出口

```

> **提示**：如果你在本地用 `mihomo convert-ruleset domain text/yaml input.txt output.mrs` 生成 `.mrs` 文件，请确保源文件为纯 UTF-8 编码，且每条规则格式符合 `behavior: domain` 规范（如 `+.example.com` 或 `example.com`）。
