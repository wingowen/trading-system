"""
StockExpert 报告推送脚本
采集数据 → 生成报告 → 推送飞书

用法:
  python send_report.py                          # 今日当前时段
  python send_report.py 2026-05-03 morning    # 指定日期/时段
  python send_report.py --collect-only          # 只采集不推送
  python send_report.py --report-only           # 只推送不采集（用已有DB数据）
"""
import os, sys, datetime, argparse, json, requests

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# ── 凭证 ──────────────────────────────────────────────────
APP_ID     = "cli_a949ee9cecf81cbb"
APP_SECRET = "YQLrXPrir8qwXk3vg0046dCJ1i4GZK4D"
FEISHU_OPEN_ID = "ou_aa2e5c6d89ccff3977bc9c37899f641e"

# ── 内部依赖 ───────────────────────────────────────────────
HERMES_PYTHON = "/home/wingo/.hermes/hermes-agent/venv/bin/python3"
COLLECT_SCRIPT = os.path.join(BASE, "collect_all.py")
REPORT_SCRIPT  = os.path.join(BASE, "report_generator.py")
DATA_DIR       = "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data"
REPORTS_DIR    = os.path.join(DATA_DIR, "reports")


def get_token():
    r = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": APP_ID, "app_secret": APP_SECRET},
        timeout=10
    )
    r.raise_for_status()
    return r.json()["tenant_access_token"]


def upload_image(token: str, file_path: str) -> str:
    """上传图片，返回 image_key"""
    with open(file_path, "rb") as f:
        r = requests.post(
            "https://open.feishu.cn/open-apis/im/v1/images",
            headers={"Authorization": f"Bearer {token}"},
            data={"image_type": "message"},
            files={"image": (os.path.basename(file_path), f, "image/png")},
            timeout=30
        )
    r.raise_for_status()
    return r.json()["data"]["image_key"]


def send_image(token: str, image_key: str, open_id: str) -> str:
    """发送图片消息，返回 message_id"""
    r = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": open_id,
            "msg_type": "image",
            "content": json.dumps({"image_key": image_key})
        },
        params={"receive_id_type": "open_id"},
        timeout=10
    )
    r.raise_for_status()
    return r.json()["data"]["message_id"]


def send_text(token: str, text: str, open_id: str) -> str:
    """发送文本消息，返回 message_id"""
    r = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "receive_id": open_id,
            "msg_type": "text",
            "content": json.dumps({"text": text})
        },
        params={"receive_id_type": "open_id"},
        timeout=10
    )
    r.raise_for_status()
    return r.json()["data"]["message_id"]


def run_collect(report_date: str, session: str) -> bool:
    """运行采集脚本"""
    import subprocess
    cmd = [HERMES_PYTHON, COLLECT_SCRIPT, report_date, session]
    print(f"  🔄 采集数据: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  ❌ 采集失败:\n{result.stderr[-500:]}")
        return False
    # 找关键输出
    for line in result.stdout.splitlines():
        if "✅" in line or "❌" in line or "写入" in line:
            print(f"    {line.strip()}")
    return True


def run_generate(trade_date: str, session: str) -> tuple:
    """运行报告生成，返回 (txt_path, png_path)"""
    import subprocess
    cmd = [HERMES_PYTHON, REPORT_SCRIPT, trade_date, session]
    print(f"  🔄 生成报告: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    txt_path = os.path.join(REPORTS_DIR, f"report_{trade_date}_{session}.txt")
    png_path = os.path.join(REPORTS_DIR, f"report_{trade_date}_{session}.png")
    if result.returncode != 0:
        print(f"  ⚠️ 报告生成stderr:\n{result.stderr[-300:]}")
    return txt_path, png_path


def push_to_feishu(trade_date: str, session: str, txt_path: str, png_path: str):
    """推送文本+图片到飞书"""
    token = get_token()
    session_label = {"morning": "📰 晨报", "noon": "🌤️ 午盘", "close": "🌙 收评"}.get(session, session)

    # 1. 先发图片
    if os.path.exists(png_path):
        print(f"  🖼️  上传图片...")
        image_key = upload_image(token, png_path)
        msg_id = send_image(token, image_key, FEISHU_OPEN_ID)
        print(f"  ✅ 图片已发: {msg_id}")

    # 2. 再发文本摘要（飞书 text 消息）
    if os.path.exists(txt_path):
        text = open(txt_path, encoding="utf-8").read()
        # 飞书 text 有长度限制，截取关键段
        # 前12行 ≈ 晨报核心内容
        lines = text.splitlines()
        # 去掉重复的采集日志行，保留前30行
        summary_lines = []
        skip_log = False
        for line in lines:
            if line.startswith("  ✅ akshare") or line.startswith("  ✅ cdp"):
                if not skip_log:
                    skip_log = True
                    summary_lines.append("  ... (采集日志省略)")
                continue
            skip_log = False
            summary_lines.append(line)
            if len(summary_lines) >= 30:
                break
        summary = "\n".join(summary_lines)

        print(f"  📝 发送文本摘要...")
        msg_id = send_text(token, summary, FEISHU_OPEN_ID)
        print(f"  ✅ 文本已发: {msg_id}")


# ── 主入口 ─────────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("report_date", nargs="?", default=None)
    ap.add_argument("session",     nargs="?", default=None)
    ap.add_argument("--collect-only", action="store_true")
    ap.add_argument("--report-only", action="store_true")
    return ap.parse_args()


def guess_session():
    now = datetime.datetime.now()
    total = now.hour * 60 + now.minute
    if total < 12 * 60 + 30:  return "morning"
    elif total < 15 * 60 + 30: return "noon"
    else: return "close"


def main():
    args = parse_args()
    today = datetime.date.today()

    # 日期
    if args.report_date:
        try:
            report_date = datetime.date.fromisoformat(args.report_date)
        except ValueError:
            print(f"❌ 无效日期: {args.report_date}"); return
    else:
        report_date = today

    # 时段
    if args.session:
        session = args.session
    else:
        session = guess_session()

    rd = report_date.isoformat()
    print(f"\n{'═'*55}")
    print(f"  StockExpert 报告推送  {rd} {session}")
    print(f"{'═'*55}")

    # 1. 采集
    if not args.report_only:
        ok = run_collect(rd, session)
        if not ok:
            print("❌ 采集失败，终止")
            return

    # 2. 生成
    txt_path, png_path = run_generate(rd, session)
    print(f"  📄 文本: {txt_path}")
    print(f"  🖼️  图片: {png_path}")

    # 3. 推送
    if not args.collect_only:
        print(f"\n  📤 推送飞书...")
        push_to_feishu(rd, session, txt_path, png_path)
        print(f"\n✅ 完成!")


if __name__ == "__main__":
    main()
