"""
StockExpert 全量数据采集脚本
一次性采集所有数据并写入数据库 + 打印溯源看板

用法:
  python collect_all.py                    # 采集今天 morning
  python collect_all.py 2026-05-03 noon    # 指定日期/时段
  python collect_all.py --dry-run          # 只打印，不写库
"""
import sys, os, datetime, argparse

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

from db_writer import DatabaseWriter
from fetchers.akshare_fetcher import (
    fetch_index_quotes,
    fetch_limit_up_count,
    fetch_limit_down_count,
    fetch_north_flow_summary,
    fetch_north_hist,
)
from fetchers.zhangtingke_fetcher import fetch_all as fetch_zhangtingke
from fetchers.cdp_fetcher import fetch_north_flow_cdp, fetch_market_sentiment_cdp


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("report_date", nargs="?", default=None)
    ap.add_argument("session", nargs="?", default=None)
    ap.add_argument("--dry-run", action="store_true")
    return ap.parse_args()


def main():
    args = parse_args()
    today = datetime.date.today()
    now = datetime.datetime.now()

    if args.report_date:
        try:
            report_date = datetime.date.fromisoformat(args.report_date)
        except ValueError:
            print(f"❌ 无效日期: {args.report_date}"); return
    else:
        report_date = today

    session = args.session or _guess_session(now)

    print(f"📅 {report_date}  {session}  ({now.strftime('%H:%M:%S')})")
    print("=" * 70)

    # ===== 1. akshare =====
    print("\n[1/4] akshare 数据采集...")
    ax = {}

    try:
        ax["index_quotes"] = fetch_index_quotes()
        iq = ax["index_quotes"]
        print(f"  4指数: {'✅' if iq.get('status')=='success' else '❌'} {iq.get('error','')[:60] if iq.get('status')!='success' else ''}")
    except Exception as e:
        print(f"  4指数: ❌ {e}")
        ax["index_quotes"] = {"status": "failed", "error": str(e)}

    try:
        ax["limit_up"] = fetch_limit_up_count()
        lu = ax["limit_up"]
        print(f"  涨停家数: {'✅' if lu.get('status')=='success' else '❌'} {lu.get('limit_up_count','?')}只")
    except Exception as e:
        print(f"  涨停家数: ❌ {e}")
        ax["limit_up"] = {"status": "failed", "error": str(e)}

    try:
        ax["limit_down"] = fetch_limit_down_count()
        ld = ax["limit_down"]
        print(f"  跌停家数: {'✅' if ld.get('status')=='success' else '❌'} {ld.get('limit_down_count','?')}只")
    except Exception as e:
        print(f"  跌停家数: ❌ {e}")
        ax["limit_down"] = {"status": "failed", "error": str(e)}

    try:
        ax["north_summary"] = fetch_north_flow_summary()
        ns = ax["north_summary"]
        print(f"  北向概况: {'✅' if ns.get('status')=='success' else '❌'}")
    except Exception as e:
        print(f"  北向概况: ❌ {e}")
        ax["north_summary"] = {"status": "failed", "error": str(e)}

    try:
        ax["north_hist"] = fetch_north_hist()
        nh = ax["north_hist"]
        s = nh.get("status", "failed")
        note = " ⚠️ 22月缺口" if s == "partial" else ""
        print(f"  北向历史: {'✅' if s=='success' else '⚠️ '+s}{note}")
        if nh.get("last_valid_date"):
            print(f"    最后有效: {nh['last_valid_date']}  NaN起始: {nh.get('first_na_date','?')}")
    except Exception as e:
        print(f"  北向历史: ❌ {e}")
        ax["north_hist"] = {"status": "failed", "error": str(e)}

    # ===== 2. zhangtingke =====
    print("\n[2/4] 涨停客(zhangtingke.com)数据采集...")
    zt = {}
    try:
        zt["today"] = fetch_zhangtingke()
        zd = zt["today"]
        s = zd.get("status", "failed")
        print(f"  连板/炸板: {'✅' if s=='success' else '⚠️ '+s}")
        if s == "success":
            print(f"    最高{zd.get('highest_board')}连板 今炸板率{zd.get('break_board_rate')}% "
                  f"今连板{zd.get('continue_board_count')}只 触板未封{zd.get('touched_not_sealed')}只")
    except Exception as e:
        print(f"  连板/炸板: ❌ {e}")
        zt["today"] = {"status": "failed", "error": str(e)}

    # ===== 3. CDP =====
    print("\n[3/4] Chrome CDP 数据采集...")
    cdp_r = {}
    try:
        cdp_r["north_flow"] = fetch_north_flow_cdp()
        nf = cdp_r["north_flow"]
        s = nf.get("status", "failed")
        print(f"  主力资金流(CDP): {'✅' if s=='success' else '⚠️ '+s}")
        if s == "success":
            print(f"    主力{nf.get('main_net_inflow')}亿 超大{nf.get('super_large_net')}亿 "
                  f"大单{nf.get('large_net')}亿 中单{nf.get('medium_net')}亿 小单{nf.get('small_net')}亿")
        else:
            print(f"    {nf.get('error','')[:80]}")
    except Exception as e:
        print(f"  主力资金流(CDP): ❌ {e}")
        cdp_r["north_flow"] = {"status": "failed", "error": str(e)}

    # ===== 4. 写入数据库 =====
    print("\n[4/4] 写入数据库...")
    if args.dry_run:
        print("  [dry-run] 跳过写入")
    else:
        db = DatabaseWriter()
        ok, msg = db.write_all(report_date.isoformat(), session, ax, zt, cdp_r)
        print(f"  {'✅' if ok else '❌'} {msg}")
        print(f"  记录ID: {db.last_record_id}")
        db.close()

    # ===== 5. 溯源看板 =====
    print("\n" + "=" * 70)
    print(f"📊 数据溯源看板  {report_date}  {session}")
    print("=" * 70)

    # 指数
    iq = ax.get("index_quotes", {})
    if iq.get("status") == "success":
        for code_full, idx in iq.get("indices", {}).items():
            chg = idx.get("change_pct")
            print(f"  {idx['index_name']:<10} {chg:>+7.2f}%  [{idx['source']}]")
    else:
        print(f"  4大指数: ❌ {iq.get('error','')[:50]}")

    # 涨跌停
    lu = ax.get("limit_up", {})
    print(f"  涨停家数:    {lu.get('limit_up_count', '?'):>5}  [{lu.get('source','?')}]")
    ld = ax.get("limit_down", {})
    print(f"  跌停家数:    {ld.get('limit_down_count', '?'):>5}  [{ld.get('source','?')}]")

    # 涨停客
    zd = zt.get("today", {})
    print(f"  最高连板:    {str(zd.get('highest_board','?')):<5}  [{zd.get('source','?')}]")
    print(f"  今炸板率:    {zd.get('break_board_rate','?'):>5}  [{zd.get('source','?')}]")
    print(f"  今连板数:    {zd.get('continue_board_count','?'):>5}  [{zd.get('source','?')}]")
    print(f"  触板未封:    {zd.get('touched_not_sealed','?'):>5}  [{zd.get('source','?')}]")

    # 北向
    nf = cdp_r.get("north_flow", {})
    if nf.get("status") == "success":
        print(f"  主力净流入:  {nf.get('main_net_inflow','?'):>+10.4f}亿  [{nf['source']}]")
        print(f"  超大单净流:  {nf.get('super_large_net','?'):>+10.4f}亿  [{nf['source']}]")
        print(f"  大单净流入:  {nf.get('large_net','?'):>+10.4f}亿  [{nf['source']}]")
        print(f"  中单净流入:  {nf.get('medium_net','?'):>+10.4f}亿  [{nf['source']}]")
        print(f"  小单净流入:  {nf.get('small_net','?'):>+10.4f}亿  [{nf['source']}]")
    else:
        ns = ax.get("north_summary", {})
        print(f"  北向概况:    {'✅' if ns.get('status')=='success' else '❌'}  [{ns.get('source','?')}]")

    # 北向历史
    nh = ax.get("north_hist", {})
    s = nh.get("status", "failed")
    lbl = "✅" if s == "success" else "⚠️ 22月缺口" if s == "partial" else "❌"
    print(f"  北向历史:    {lbl}  [{nh.get('source','?')}]")
    if nh.get("last_valid_date"):
        print(f"    最后有效: {nh['last_valid_date']} | NaN起始: {nh.get('first_na_date','?')}")

    # CDP状态
    cdp_ok = cdp_r.get("north_flow", {}).get("status") == "success"
    print(f"  CDP连接:     {'✅ 可用' if cdp_ok else '❌ 失败'}  [Chrome CDP ws]")


def _guess_session(now: datetime.datetime) -> str:
    total = now.hour * 60 + now.minute
    if total < 12 * 60 + 30:
        return "morning"
    elif total < 15 * 60 + 30:
        return "noon"
    else:
        return "close"


if __name__ == "__main__":
    main()
