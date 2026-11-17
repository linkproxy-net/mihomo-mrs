import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
import os
import re
import urllib.request
import subprocess
import ipaddress
import time

# 确保脚本工作目录始终为当前脚本所在文件夹
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR:
    os.chdir(BASE_DIR)

# ==================== 1. 数据源配置 ====================
# 去广告源：GOODBYEADS + anti-AD + AWAvenue
AD_SOURCES = {
    "GOODBYEADS": "https://raw.githubusercontent.com/8680/GOODBYEADS/master/data/rules/dns.txt",
    "anti-AD": "https://raw.githubusercontent.com/privacy-protection-tools/anti-AD/master/anti-ad-domains.txt",
    "AWAvenue": "https://raw.githubusercontent.com/TG-Twilight/AWAvenue-Ads-Rule/main/Filters/AWAvenue-Ads-Rule-Clash.yaml"
}

# AI 分流源
V2FLY_BASE_URL = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"
VPSDANCE_URL = "https://raw.githubusercontent.com/VPSDance/ai-proxy-rules/main/rules/clash/global.yaml"

AI_CLASH_LISTS = {
    "ACL4SSR_AI": "https://raw.githubusercontent.com/ACL4SSR/ACL4SSR/master/Clash/Ruleset/AI.list",
    "BM7_OpenAI": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/OpenAI/OpenAI.list",
    "BM7_Claude": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Claude/Claude.list",
    "BM7_Anthropic": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Anthropic/Anthropic.list",
    "BM7_Gemini": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/BardAI/BardAI.list",
    "BM7_Copilot": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Copilot/Copilot.list"
}

AI_METACUBEX_LISTS = {
    "MetaCubeX_Perplexity": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/perplexity.list",
    "MetaCubeX_xAI": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/xai.list",
    "MetaCubeX_Groq": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/groq.list",
    "MetaCubeX_Anthropic": "https://raw.githubusercontent.com/MetaCubeX/meta-rules-dat/meta/geo/geosite/anthropic.list"
}

def fetch(url, retries=3):
    urls_to_try = [url]
    if "raw.githubusercontent.com" in url:
        urls_to_try.append(url.replace("raw.githubusercontent.com", "raw.gitmirror.com"))
        urls_to_try.append(f"https://ghproxy.net/{url}")

    for target_url in urls_to_try:
        for attempt in range(retries):
            try:
                req = urllib.request.Request(target_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    return resp.read().decode('utf-8', errors='ignore')
            except Exception:
                time.sleep(1)

    print(f"[-] 拉取失败: {url}")
    return ""

def is_ip(addr):
    try:
        ipaddress.ip_address(addr)
        return True
    except ValueError:
        return False

def clean_ad_domain(d):
    d = d.split('#')[0].split('!')[0].split('@')[0].strip().lower()
    d = d.replace("'", "").replace('"', "").rstrip('.')
    if d.startswith('*.'):
        d = d[2:]
    elif d.startswith('.'):
        d = d[1:]
    if not d or ' ' in d or ':' in d or '/' in d:
        return None
    # 过滤掉非法的 label 通配符，如 a*.com，避免 Mihomo 编译报错
    for part in d.split('.'):
        if '*' in part and part != '*':
            return None
    if '.' not in d or is_ip(d) or d.startswith('*'):
        return None
    return d

# ==================== 2. 生成去广告规则 (ads.txt) ====================
def build_ads():
    print("\n[+] 开始处理去广告规则 (GOODBYEADS + anti-AD + AWAvenue)...")
    domains = set()

    # 1. GOODBYEADS (ABP 格式)
    print(" -> 抓取 GOODBYEADS...")
    c1 = fetch(AD_SOURCES["GOODBYEADS"])
    pat = re.compile(r"^\|\|([a-zA-Z0-9_\-\.\*]+)\^")
    for line in c1.splitlines():
        line = line.strip()
        if not line or line.startswith(('!', '[', '#', '@@')):
            continue
        m = pat.match(line)
        if m:
            cd = clean_ad_domain(m.group(1))
            if cd:
                domains.add(cd)

    # 2. anti-AD (纯域名列表)
    print(" -> 抓取 anti-AD...")
    c2 = fetch(AD_SOURCES["anti-AD"])
    for line in c2.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        cd = clean_ad_domain(line)
        if cd:
            domains.add(cd)

    # 3. AWAvenue (Clash 列表)
    print(" -> 抓取 AWAvenue...")
    c3 = fetch(AD_SOURCES["AWAvenue"])
    for line in c3.splitlines():
        line = line.strip()
        if line.startswith('- '):
            cd = clean_ad_domain(line[2:])
            if cd:
                domains.add(cd)

    sorted_domains = sorted(list(domains))
    with open("ads.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted_domains) + "\n")
    print(f"[OK] 去广告规则提取完成: {len(sorted_domains)} 条 -> ads.txt")

# ==================== 3. 生成 AI 分流规则 (ai.txt) ====================
ai_domains = set()
ai_exact_domains = set()

def add_ai_domain(d, exact=False):
    d = d.split('#')[0].split('@')[0].strip().lower()
    d = d.replace("'", "").replace('"', "").rstrip('.')
    if d.startswith('+.'):
        d = d[2:]
    if not d or ' ' in d or ':' in d or '/' in d:
        return
    if exact:
        ai_exact_domains.add(d)
    else:
        ai_domains.add(d)

def parse_v2fly(name, visited=None):
    if visited is None: visited = set()
    if name in visited: return
    visited.add(name)
    content = fetch(V2FLY_BASE_URL + name)
    for line in content.splitlines():
        line = line.split('#')[0].strip()
        if not line: continue
        if line.startswith('include:'):
            parse_v2fly(line.split(':')[1].split('@')[0].strip(), visited)
        elif line.startswith('full:'):
            add_ai_domain(line.split(':')[1], exact=True)
        elif ':' not in line:
            add_ai_domain(line)

def build_ai():
    print("\n[+] 开始处理 AI 分流规则 (v2fly + Clash Lists + MetaCubeX + VPSDance)...")
    # 1. v2fly 递归
    print(" -> 抓取 v2fly category-ai-!cn...")
    parse_v2fly('category-ai-!cn')

    # 2. Clash Lists (OpenAI, Claude, Anthropic, Gemini, Copilot, ACL4SSR)
    for name, url in AI_CLASH_LISTS.items():
        print(f" -> 抓取 {name}...")
        content = fetch(url)
        for line in content.splitlines():
            line = line.split('#')[0].strip()
            if not line: continue
            parts = line.split(',')
            if len(parts) >= 2:
                t, val = parts[0].strip().upper(), parts[1].strip()
                if t == 'DOMAIN-SUFFIX':
                    add_ai_domain(val)
                elif t == 'DOMAIN':
                    add_ai_domain(val, exact=True)

    # 3. MetaCubeX 扩展 (Perplexity, xAI/Grok, Groq, Anthropic/Claude Code)
    for name, url in AI_METACUBEX_LISTS.items():
        print(f" -> 抓取 {name}...")
        content = fetch(url)
        for line in content.splitlines():
            line = line.split('#')[0].strip()
            if not line: continue
            if line.startswith('+.'):
                add_ai_domain(line[2:], exact=False)
            else:
                add_ai_domain(line, exact=True)

    # 4. VPSDance
    print(" -> 抓取 VPSDance...")
    content = fetch(VPSDANCE_URL)
    for line in content.splitlines():
        line = line.strip()
        if line.startswith('- '):
            parts = line[2:].strip().split(',')
            if len(parts) >= 2:
                t, val = parts[0].strip().upper(), parts[1].strip()
                if t == 'DOMAIN-SUFFIX':
                    add_ai_domain(val)
                elif t == 'DOMAIN':
                    add_ai_domain(val, exact=True)

    # 上下级智能包含去重
    sorted_d = sorted(list(ai_domains), key=lambda x: len(x.split('.')))
    optimized = set()
    for d in sorted_d:
        parts = d.split('.')
        covered = any('.'.join(parts[i:]) in optimized for i in range(1, len(parts)))
        if not covered:
            optimized.add(d)

    final_rules = {f"+.{d}" for d in optimized}
    for d in ai_exact_domains:
        parts = d.split('.')
        if not any('.'.join(parts[i:]) in optimized for i in range(len(parts))):
            final_rules.add(d)

    with open("ai.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(list(final_rules))) + "\n")
    print(f"[OK] AI 规则合并去重完成: {len(final_rules)} 条 -> ai.txt")

# ==================== 4. 调用 Mihomo 编译为 .mrs ====================
def compile_mrs(txt_file, mrs_file):
    mihomo_bin = "mihomo.exe" if os.name == 'nt' else "mihomo"
    if not os.path.exists(mihomo_bin):
        mihomo_bin = "mihomo"

    cmd = [mihomo_bin, "convert-ruleset", "domain", "text", txt_file, mrs_file]
    try:
        subprocess.run(cmd, check=True)
        size_kb = os.path.getsize(mrs_file) / 1024
        print(f"[OK] 成功编译 {mrs_file} ({size_kb:.2f} KB)")
    except Exception as e:
        print(f"[-] 编译 {mrs_file} 失败: 请确保目录下存在 mihomo.exe。详情: {e}")

# ==================== 5. 自动提交并推送到 Git ====================
def auto_push():
    cwd = os.path.dirname(os.path.abspath(__file__))
    print("\n[+] 正在检查变动并推送到 Git 远程仓库...")
    try:
        res = subprocess.run(["git", "status"], cwd=cwd, capture_output=True, text=True)
        if res.returncode != 0:
            print("[-] 当前目录尚未关联 Git 仓库，跳过推送。")
            return

        subprocess.run(["git", "add", "ads.mrs", "ads.txt", "ai.mrs", "ai.txt", "README.md", "update_all.py"], cwd=cwd, check=True)
        diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=cwd)
        if diff.returncode == 0:
            print("[OK] 规则文件没有变动，无需重复推送。")
            return

        subprocess.run(["git", "commit", "-m", "chore: auto update rules"], cwd=cwd, check=True)
        subprocess.run(["git", "push"], cwd=cwd, check=True)
        print("[OK] 成功推送到 Git 远程仓库！")
    except Exception as e:
        print(f"[-] Git 自动推送失败: {e}")

if __name__ == "__main__":
    build_ads()
    build_ai()
    print("\n[+] 正在编译为二进制 MRS 规则集...")
    compile_mrs("ads.txt", "ads.mrs")
    compile_mrs("ai.txt", "ai.mrs")
    auto_push()
    print("\n 全部处理完毕！")
