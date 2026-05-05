"""
数据源测试报告生成器
运行所有测试并生成 Markdown 报告
"""
import subprocess
import json
import sys
import os
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 动态确定项目根目录
BASE_DIR = Path(__file__).parent.resolve()
REPORT_DIR = BASE_DIR
logger.info(f"测试根目录: {BASE_DIR}")

DATA_SOURCES = {
    "akshare": {
        "script": "datasource/test_akshare.py",
        "version_cmd": "python3 -c \"import akshare; print(akshare.__version__)\"",
        "install_cmd": "pip install akshare",
        "description": "A 股数据全能接口，东方财富/新浪/腾讯等多源聚合",
        "docs": "https://akshare.akfamily.xyz",
        "token": "无需",
        "note": "akshare 1.18.60",
    },
    "baostock": {
        "script": "datasource/test_baostock.py",
        "version_cmd": "python3 -c \"import baostock; print(baostock.__version__)\"",
        "install_cmd": "pip install baostock",
        "description": "免费 A 股历史数据 + 财务报表接口，无需注册",
        "docs": "http://www.baostock.com",
        "token": "无需",
        "note": "baostock 0.9.10",
    },
    "efinance": {
        "script": "datasource/test_efinance.py",
        "version_cmd": "python3 -c \"import efinance; print('installed')\"",
        "install_cmd": "pip install efinance",
        "description": "东方财富数据封装，实时行情 + 历史 K 线",
        "docs": "https://github.com/MicroCSV/efinance",
        "token": "无需",
        "note": "efinance 0.5.8，jsonpath 冲突导致部分接口不可用",
    },
    "pytdx": {
        "script": "datasource/test_pytdx.py",
        "version_cmd": "python3 -c \"import pytdx; print('installed')\"",
        "install_cmd": "pip install pytdx",
        "description": "通达信行情接口，速度快，实时性好",
        "docs": "https://github.com/peerfinance/pytdx",
        "token": "无需",
        "note": "连接免费行情服务器 118.244.123.178:7709",
    },
    "tushare": {
        "script": "datasource/test_tushare.py",
        "version_cmd": "python3 -c \"import tushare; print(tushare.__version__)\"",
        "install_cmd": "pip install tushare",
        "description": "国内最全 A 股数据平台，免费用户有基础权限",
        "docs": "https://tushare.pro",
        "token": "必需（免费注册获取）",
        "note": "免费注册 https://tushare.pro/register?reg=3159",
    },
}


def run_test(source_name, config):
    """运行单个数据源测试，返回 (success, output)"""
    script_path = os.path.join(BASE_DIR, config["script"])
    if not os.path.exists(script_path):
        return False, f"脚本不存在: {script_path}"

    logger.info(f"\n{'='*60}")
    logger.info(f"Running {source_name}...")
    logger.info(f"{'='*60}")

    result = subprocess.run(
        ["python3", script_path],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=BASE_DIR
    )

    output = result.stdout + "\n" + result.stderr
    success = result.returncode == 0
    return success, output


def parse_results(output):
    """从测试输出中解析结果"""
    results = {}
    lines = output.split("\n")
    in_summary = False
    for line in lines:
        if "测试结果汇总:" in line:
            in_summary = True
            continue
        if in_summary and ("✅" in line or "❌" in line):
            line = line.strip()
            if "✅" in line:
                name = line.replace("✅", "").strip()
                results[name] = True
            elif "❌" in line:
                name = line.replace("❌", "").strip()
                results[name] = False
    return results


def generate_report(source_name, config, output, results):
    """生成 Markdown 报告"""
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    pass_rate = f"{passed}/{total} ({100*passed//total}%)" if total > 0 else "N/A"

    report = f"""# {source_name} 数据源测试报告

## 基本信息

| 项目 | 内容 |
|------|------|
| 数据源 | {source_name} |
| 安装命令 | `{config['install_cmd']}` |
| 文档 | {config['docs']} |
| Token | {config['token']} |
| 备注 | {config.get('note', '')} |

## 测试概况

- **测试时间**: {start_time}
- **通过率**: {pass_rate}
- **数据描述**: {config['description']}

## 测试结果

| 序号 | 测试项 | 结果 |
|------|--------|------|
"""

    for i, (name, ok) in enumerate(results.items(), 1):
        # 从测试名提取中文描述
        test_name = name.replace("test_", "").replace("_", " ")
        status = "✅ 通过" if ok else "❌ 失败"
        report += f"| {i} | {test_name} | {status} |\n"

    report += f"""
## 详细输出

<details>
<summary>点击展开完整测试输出</summary>

```
{output}
```

</details>

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return report


def main():
    logger.info(f"开始数据源测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    all_reports = {}

    for source_name, config in DATA_SOURCES.items():
        success, output = run_test(source_name, config)
        results = parse_results(output)

        if results:
            report = generate_report(source_name, config, output, results)
            all_reports[source_name] = {
                "config": config,
                "output": output,
                "results": results,
                "report": report,
                "passed": sum(1 for v in results.values() if v),
                "total": len(results),
            }

            # 保存单个报告
            report_path = os.path.join(REPORT_DIR, source_name, "reports", f"test_report_{datetime.now().strftime('%Y%m%d')}.md")
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            logger.info(f"  报告已保存: {report_path}")

    # 生成汇总报告
    summary_report = generate_summary(all_reports)
    summary_path = os.path.join(REPORT_DIR, "DATA_SOURCES_SUMMARY.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_report)
    logger.info(f"\n汇总报告: {summary_path}")

    # 打印汇总
    logger.info(f"\n{'='*60}")
    logger.info("数据源测试汇总:")
    logger.info(f"{'='*60}")
    for name, data in all_reports.items():
        p = data['passed']
        t = data['total']
        rate = f"{100*p//t}%" if t > 0 else "N/A"
        logger.info(f"  {name}: {p}/{t} ✅ ({rate})")

    return all_reports


def generate_summary(all_reports):
    """生成汇总报告"""
    start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    summary = f"""# A 股免费数据源测试汇总报告

## 测试概览

- **测试时间**: {start_time}
- **数据源数量**: {len(all_reports)} 个

## 数据源对比

| 数据源 | 测试项数 | 通过数 | 通过率 | Token | 主要用途 |
|--------|---------|-------|--------|-------|---------|
"""

    for name, data in all_reports.items():
        cfg = data['config']
        p = data['passed']
        t = data['total']
        rate = f"{100*p//t}%" if t > 0 else "0%"
        token = cfg.get('token', '未知')
        desc = cfg.get('description', '')
        summary += f"| **{name}** | {t} | {p} | {rate} | {token} | {desc} |\n"

    # 汇总所有可用数据类型
    all_data_types = {}
    for name, data in all_reports.items():
        all_data_types[name] = {
            "passed": [],
            "failed": [],
        }
        for test_name, ok in data['results'].items():
            if ok:
                all_data_types[name]["passed"].append(test_name)
            else:
                all_data_types[name]["failed"].append(test_name)

    summary += f"""

## 数据类型覆盖矩阵

"""

    # 收集所有数据类型
    all_types = set()
    for info in all_data_types.values():
        all_types.update(info["passed"])
        all_types.update(info["failed"])
    all_types = sorted(all_types)

    summary += f"| 数据类型 | " + " | ".join(f"`{s}`" for s in all_reports.keys()) + " |\n"
    summary += "|" + "---|" * (len(all_reports) + 1) + "\n"

    for dtype in all_types:
        row = f"| `{dtype}` |"
        for name in all_reports.keys():
            info = all_data_types.get(name, {})
            if dtype in info.get("passed", []):
                row += " ✅ |"
            elif dtype in info.get("failed", []):
                row += " ❌ |"
            else:
                row += " - |"
        summary += row + "\n"

    summary += f"""

## 关键发现

"""

    # 统计哪些数据类型覆盖最多
    type_coverage = {}
    for dtype in all_types:
        covered_by = [name for name in all_reports.keys() if dtype in all_data_types.get(name, {}).get("passed", [])]
        type_coverage[dtype] = covered_by

    # 找出最佳数据源组合
    summary += "### 推荐数据源组合\n\n"
    summary += "- **行情数据（实时）**: `efinance` + `pytdx` + `akshare` 三选一，efinance 板块数据最全\n"
    summary += "- **历史K线（日线）**: `baostock`（免费无限制）或 `akshare`\n"
    summary += "- **财务报表**: `baostock`（免费最全）或 `akshare`\n"
    summary += "- **板块数据**: `akshare`（东方财富接口）或 `efinance`\n"
    summary += "- **分钟K线**: `akshare` 或 `pytdx`\n"
    summary += "- **基本面/估值**: `baostock`（杜邦/成长/盈利指标）\n"
    summary += "- **Tushare**: 需要注册获取 token，数据最全面（含期货/期权/基金等），适合生产环境\n\n"

    summary += "### 已知问题\n\n"
    for name, data in all_reports.items():
        failed = [t for t, ok in data['results'].items() if not ok]
        if failed:
            summary += f"- **{name}**: {', '.join(failed)}\n"

    summary += f"""
---

*汇总报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return summary


if __name__ == "__main__":
    main()
