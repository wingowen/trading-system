"""
StockExpert 报告生成器
从 data_records 宽表读取数据，生成文本报告和 PNG 图片

用法:
  python report_generator.py                          # 生成今日晨报
  python report_generator.py 2026-05-03 morning    # 指定日期/时段
  python report_generator.py --no-image              # 只生成文本
"""
import os, sys, datetime, argparse
from pathlib import Path

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

DB_PATH   = "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── 工具 ─────────────────────────────────────────────────
def get_fields(trade_date: str, session: str) -> dict:
    """返回 {field_name: (value, source, status)}"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT field_name, field_value, source, status FROM data_records "
        "WHERE trade_date = ? AND session = ?",
        (trade_date, session)
    ).fetchall()
    conn.close()
    return {r["field_name"]: (r["field_value"], r["source"], r["status"]) for r in rows}


def get_fetch_logs(trade_date: str, session: str) -> list:
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT fetcher, status, records_count, error_message FROM fetch_logs "
        "WHERE trade_date = ? AND session = ?",
        (trade_date, session)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fmt(v, suffix="", sign=True):
    if v is None: return "?"
    if sign and v >= 0: return f"+{v:.2f}{suffix}"
    return f"{v:.2f}{suffix}"


def pct(v):
    if v is None: return "?"
    return f"{v:.2f}%"


# ── 文本报告 ─────────────────────────────────────────────
def generate_text(trade_date: str, session: str) -> str:
    fields = get_fields(trade_date, session)
    logs   = get_fetch_logs(trade_date, session)

    label = {"morning": "📰 晨报", "noon": "🌤️ 午盘", "close": "🌙 收评"}.get(session, session)
    ok_cnt = sum(1 for v in fields.values() if v[2] == "success")
    total  = len(fields)

    lines = []
    lines.append(f"{'═' * 52}")
    lines.append(f"  StockExpert {label}  ·  {trade_date}")
    lines.append(f"{'═' * 52}")
    lines.append(f"  数据完整度  {ok_cnt}/{total} 字段成功")

    # ── 大盘指数 ──
    idx_fields = {k: v for k, v in fields.items() if k.startswith("index_")}
    if idx_fields:
        lines.append(f"\n📈 大盘指数")
        # 按 field_name 排序，解析出指数名
        for fname in sorted(idx_fields.keys()):
            val, src, _ = idx_fields[fname]
            # field_name 格式: index_chg_sh000001, index_close_sh000001 等
            parts = fname.split("_", 2)
            if len(parts) >= 3:
                typ, code = parts[1], parts[2]
                name_map = {
                    "sh000001": "上证指数", "399001": "深证成指",
                    "399006": "创业板指", "sh000688": "科创50",
                }
                name = name_map.get(code, code)
                if typ == "chg":
                    arrow = "▲" if (val or 0) >= 0 else "▼"
                    lines.append(f"  {arrow} {name:<10} {fmt(val,'%')}"
                                f"  (收盘 {fields.get(f'index_close_{code}', (None,'',''))[0]})"
                                f"  [{src.split(':')[1] if ':' in src else src}]")
    else:
        lines.append(f"\n📈 大盘指数  (暂无)")

    # ── 涨跌停 ──
    lines.append(f"\n🔥 涨跌停")
    lu = fields.get("limit_up_count", (None, "", ""))[0]
    ld = fields.get("limit_down_count", (None, "", ""))[0]
    lines.append(f"  涨停  {lu if lu is not None else '?'}  家    跌停  {ld if ld is not None else '?'}  家")
    up_count   = fields.get("up_count",   (None, "", ""))[0]
    down_count = fields.get("down_count", (None, "", ""))[0]
    flat_count = fields.get("flat_count", (None, "", ""))[0]
    if up_count is not None:
        lines.append(f"  上涨  {up_count}  下跌  {down_count}  平盘  {flat_count}")
    up_ratio = fields.get("up_ratio", (None, "", ""))[0]
    if up_ratio is not None:
        lines.append(f"  上涨比  {up_ratio:.1%}")

    # ── 连板炸板 ──
    hb  = fields.get("highest_board",       (None, "", ""))[0]
    bbr = fields.get("break_board_rate",     (None, "", ""))[0]
    cbc = fields.get("continue_board_count", (None, "", ""))[0]
    tns = fields.get("touched_not_sealed",   (None, "", ""))[0]
    if any(v is not None for v in [hb, bbr, cbc, tns]):
        lines.append(f"\n🔴 连板炸板")
        if hb  is not None: lines.append(f"  最高连板    {int(hb)}  连板")
        if bbr is not None: lines.append(f"  今炸板率    {pct(bbr)}")
        if cbc is not None: lines.append(f"  今连板数    {int(cbc)}  只")
        if tns is not None: lines.append(f"  触板未封    {int(tns)}  只")

    # ── 晋级率 ──
    l12 = fields.get("level_1_to_2", (None, "", ""))[0]
    l23 = fields.get("level_2_to_3", (None, "", ""))[0]
    l34 = fields.get("level_3_to_4", (None, "", ""))[0]
    c12 = fields.get("level_1_to_2_cnt", (None, "", ""))[0]
    c23 = fields.get("level_2_to_3_cnt", (None, "", ""))[0]
    c34 = fields.get("level_3_to_4_cnt", (None, "", ""))[0]
    if any(v is not None for v in [l12, l23, l34]):
        lines.append(f"\n📊 晋级率")
        lines.append(f"  1进2    {pct(l12) if l12 is not None else '?'}  "
                     f"({'踩' if c12 is None else int(c12)}只)")
        lines.append(f"  2进3    {pct(l23) if l23 is not None else '?'}  "
                     f"({'踩' if c23 is None else int(c23)}只)")
        lines.append(f"  3进4    {pct(l34) if l34 is not None else '?'}  "
                     f"({'踩' if c34 is None else int(c34)}只)")

    # ── 北向资金 ──
    hgt = fields.get("hgt_net_inflow", (None, "", ""))[0]
    sgt = fields.get("sgt_net_inflow", (None, "", ""))[0]
    mnl = fields.get("main_net_inflow", (None, "", ""))[0]
    sln = fields.get("super_large_net",  (None, "", ""))[0]
    lgn = fields.get("large_net",       (None, "", ""))[0]
    mdn = fields.get("medium_net",      (None, "", ""))[0]
    smn = fields.get("small_net",       (None, "", ""))[0]
    if any(v is not None for v in [hgt, sgt, mnl, sln, lgn, mdn, smn]):
        lines.append(f"\n💰 资金流向")
        if hgt is not None: lines.append(f"  沪港通      {fmt(hgt)}  亿")
        if sgt is not None: lines.append(f"  深港通      {fmt(sgt)}  亿")
        if mnl is not None: lines.append(f"  主力净流    {fmt(mnl)}  亿")
        if sln is not None: lines.append(f"  超大单      {fmt(sln)}  亿")
        if lgn is not None: lines.append(f"  大单        {fmt(lgn)}  亿")
        if mdn is not None: lines.append(f"  中单        {fmt(mdn)}  亿")
        if smn is not None: lines.append(f"  小单        {fmt(smn)}  亿")

    # ── 采集日志 ──
    lines.append(f"\n{'─' * 52}")
    if logs:
        for lg in logs:
            icon = "✅" if lg["status"] == "success" else "🔴"
            lines.append(f"  {icon} {lg['fetcher']}")
    else:
        lines.append("  (无采集日志)")

    lines.append(f"\n  数据来源  akshare · CDP · zhangtingke.com")
    lines.append(f"  生成时间  {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return "\n".join(lines)


# ── PNG 图片报告 ─────────────────────────────────────────
def generate_image(trade_date: str, session: str) -> str:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
    except ImportError:
        return ""

    fields = get_fields(trade_date, session)

    # 中文字体：使用 font_manager.addfont 注入，再设 rcParams
    font_path = None
    for fp in [
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/mnt/c/Windows/Fonts/simhei.ttf",
    ]:
        if os.path.exists(fp):
            font_path = fp
            break
    if font_path:
        font_prop = fm.FontProperties(fname=font_path, size=10)
        # 用 addfont 把字体注入 matplotlib，再通过名字引用
        added = fm.fontManager.addfont(font_path)
        # 从注入后的 fontManager 找到实际 family 名
        font_name = next(
            (f.name for f in fm.fontManager.ttflist if f.fname == font_path),
            "WenQuanYi Zen Hei"
        )
        plt.rcParams['font.sans-serif'] = [font_name]
        plt.rcParams['axes.unicode_minus'] = False
    else:
        font_prop = None

    session_label = {"morning": "晨报", "noon": "午盘", "close": "收评"}.get(session, session)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), facecolor="#0d1117")
    fig.patch.set_facecolor("#0d1117")

    # ─ 左图：指数涨跌 ─
    ax1 = axes[0]
    ax1.set_facecolor("#161b22")
    ax1.set_title(f"📈 大盘指数  {session_label}  {trade_date}",
                  color="white", fontproperties=font_prop, fontsize=12, pad=10)

    idx_fields = {k: v for k, v in fields.items() if k.startswith("index_chg_")}
    if idx_fields:
        code_map = {
            "sh000001": "上证指数", "399001": "深证成指",
            "399006": "创业板", "sh000688": "科创50",
        }
        pairs = []
        for fname, (val, src, _) in sorted(idx_fields.items()):
            code = fname.replace("index_chg_", "")
            name = code_map.get(code, code)
            pairs.append((name, val or 0))
        names  = [p[0] for p in pairs]
        values = [p[1] for p in pairs]
        colors = ["#3fb950" if v >= 0 else "#f85149" for v in values]
        bars = ax1.barh(names, values, color=colors, height=0.5)
        ax1.axvline(0, color="white", linewidth=0.5)
        for bar, val in zip(bars, values):
            ax1.text(val, bar.get_y() + bar.get_height() / 2,
                     f" {val:+.2f}%", va="center", color="white",
                     fontproperties=font_prop, fontsize=9)
        ax1.set_xlabel("涨跌幅 (%)", color="#c9d1d9", fontproperties=font_prop)
        ax1.tick_params(colors="#c9d1d9", labelsize=9)
        ax1.spines[:].set_color("#30363d")
    else:
        ax1.text(0.5, 0.5, "(暂无指数数据)", ha="center", va="center",
                 color="#8b949e", transform=ax1.transAxes, fontproperties=font_prop)

    # ─ 右图：资金流 ─
    ax2 = axes[1]
    ax2.set_facecolor("#161b22")
    ax2.set_title(f"💰 资金流向  {session_label}  {trade_date}",
                  color="white", fontproperties=font_prop, fontsize=12, pad=10)

    flow_items = {
        "超大单": fields.get("super_large_net", (None, "", ""))[0],
        "大单":   fields.get("large_net",       (None, "", ""))[0],
        "中单":   fields.get("medium_net",       (None, "", ""))[0],
        "小单":   fields.get("small_net",        (None, "", ""))[0],
    }
    valid = {k: v for k, v in flow_items.items() if v is not None}
    if valid:
        names  = list(valid.keys())
        values = list(valid.values())
        colors2 = ["#3fb950" if v >= 0 else "#f85149" for v in values]
        bars2 = ax2.bar(names, values, color=colors2, width=0.6)
        ax2.axhline(0, color="white", linewidth=0.5)
        for bar, val in zip(bars2, values):
            yoffs = 0.3 if val >= 0 else -0.8
            ax2.text(bar.get_x() + bar.get_width() / 2, val + yoffs,
                     f"{val:+.1f}", ha="center", va="bottom" if val >= 0 else "top",
                     color="white", fontproperties=font_prop, fontsize=8)
        ax2.set_ylabel("净流入 (亿)", color="#c9d1d9", fontproperties=font_prop)
        ax2.tick_params(colors="#c9d1d9", labelsize=9)
        ax2.spines[:].set_color("#30363d")
    else:
        ax2.text(0.5, 0.5, "(暂无资金流数据)", ha="center", va="center",
                 color="#8b949e", transform=ax2.transAxes, fontproperties=font_prop)

    plt.tight_layout(pad=2)
    out_path = OUTPUT_DIR / f"report_{trade_date}_{session}.png"
    plt.savefig(out_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()
    return str(out_path)


# ── 主入口 ───────────────────────────────────────────────
def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("report_date", nargs="?", default=None)
    ap.add_argument("session",     nargs="?", default=None)
    ap.add_argument("--no-image", action="store_true")
    return ap.parse_args()


def main():
    args = parse_args()
    today = datetime.date.today()
    now   = datetime.datetime.now()

    if args.report_date:
        try:
            report_date = datetime.date.fromisoformat(args.report_date)
        except ValueError:
            print(f"❌ 无效日期: {args.report_date}")
            return
    else:
        report_date = today

    if args.session:
        session = args.session
    else:
        total = now.hour * 60 + now.minute
        if total < 12 * 60 + 30:
            session = "morning"
        elif total < 15 * 60 + 30:
            session = "noon"
        else:
            session = "close"

    report_date_str = report_date.isoformat()
    print(f"📝 生成报告: {report_date_str} {session}")

    text = generate_text(report_date_str, session)
    out_txt = OUTPUT_DIR / f"report_{report_date_str}_{session}.txt"
    out_txt.write_text(text, encoding="utf-8")
    print(f"  文本报告 → {out_txt}")

    if not args.no_image:
        img_path = generate_image(report_date_str, session)
        if img_path:
            print(f"  图片报告 → {img_path}")
        else:
            print("  ⚠️ matplotlib 不可用，跳过图片")

    print("\n" + text)


if __name__ == "__main__":
    main()
