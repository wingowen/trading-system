"""
涨停客（zhangtingke.com）数据采集器
无需CDP，curl直取
"""
import subprocess, re, json, datetime, logging
from typing import Optional, List, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def _fetch(url: str) -> str:
    """
    通过 curl 获取 URL 内容
    
    Args:
        url: 要访问的网址
        
    Returns:
        HTML 字符串
    """
    try:
        r = subprocess.run(
            ["curl", "-s", url, "-H", "User-Agent: Mozilla/5.0", "--max-time", "15"],
            capture_output=True, text=True, timeout=20
        )
        logger.debug(f"获取 {url} 完成")
        return r.stdout
    except Exception as e:
        logger.error(f"获取 {url} 失败: {e}")
        return ""


def _extract_table(html: str) -> List[List[str]]:
    """
    从 HTML 中提取表格数据
    
    Args:
        html: HTML 字符串
        
    Returns:
        表格数据，格式: [[cell1, cell2, ...], ...]
    """
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
    data = []
    for row in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
        if cells:
            cleaned = [
                re.sub(r"<[^>]+>", "", c).strip().replace("\n", "").replace("&nbsp;", "")
                for c in cells
            ]
            data.append(cleaned)
    return data


def fetch_highest_board() -> Dict[str, Any]:
    """
    最高连板高度（zt_lbgd_line）
    
    Returns:
        包含最高连板信息的字典
    """
    url = "https://zhangtingke.com/zt_lbgd_line"
    html = _fetch(url)

    result = {
        "highest_board": None,
        "highest_board_stock": None,
        "highest_board_date": None,
        "total_lbgd_count": 0,
        "source": "zhangtingke:zt_lbgd_line",
    }

    match = re.search(r"lbgd_dict\s*=\s*(\{.*?\});", html, re.DOTALL)
    if not match:
        logger.warning("lbgd_dict not found in page")
        return {**result, "status": "failed", "error": "lbgd_dict not found in page"}

    try:
        text = match.group(1).encode().decode("unicode_escape")
        lbgd = json.loads(text)

        # line_lst: [日期, 最高连板天数, 股票名] — 历史每日最高记录（排序：最高连板次数）
        # lbgd_lst: [交易日期, 股票代码, 股票名称, 连板天数, ...] — 连板个股明细，按日期降序
        line_lst = lbgd.get("line_lst", [])
        lbgd_lst = lbgd.get("lbgd_lst", [])
        result["total_lbgd_count"] = len(lbgd_lst)

        # 今日最高连板：lbgd_lst[0] 就是今日最新
        if lbgd_lst:
            today_row = lbgd_lst[0]
            result["highest_board"] = today_row[3]  # 第4列=连板天数
            result["highest_board_stock"] = today_row[2]  # 第3列=股票名称
            result["highest_board_date"] = today_row[0]  # 第1列=交易日期

        # 历史最高连板：line_lst[0]
        if line_lst:
            top_hist = line_lst[0]
            result["hist_highest_board"] = top_hist[1]
            result["hist_highest_board_stock"] = top_hist[2] if len(top_hist) > 2 else None
            result["hist_highest_board_date"] = top_hist[0]

        logger.info(f"获取最高连板成功: {result['highest_board']}")
        return {**result, "status": "success"}
    except Exception as e:
        logger.error(f"解析最高连板数据失败: {e}")
        return {**result, "status": "failed", "error": str(e)}


def fetch_break_board_rate() -> Dict[str, Any]:
    """
    今炸板率（vip_today_lbtd）
    
    Returns:
        包含炸板率信息的字典
    """
    url = "https://zhangtingke.com/vip_today_lbtd"
    html = _fetch(url)
    tables = _extract_table(html)

    result = {
        "break_board_rate_all": None,
        "break_board_rate_non_st": None,
        "break_board_rate_10cm": None,
        "break_board_rate_st": None,
        "break_board_rate_chuangk": None,
        "limit_up_total": None,
        "break_board_count": None,
        "source": "zhangtingke:vip_today_lbtd",
    }

    for row in tables:
        if not row:
            continue
        label = row[0]
        if label == "全部" and len(row) >= 5:
            result["break_board_rate_all"] = _pct(row[3])
            result["limit_up_total"] = int(row[1]) if row[1].isdigit() else None
            result["break_board_count"] = int(row[2]) if row[2].isdigit() else None
        elif label == "非ST" and len(row) >= 4:
            result["break_board_rate_non_st"] = _pct(row[3])
        elif label == "10CM" and len(row) >= 4:
            result["break_board_rate_10cm"] = _pct(row[3])
        elif label == "仅ST" and len(row) >= 4:
            result["break_board_rate_st"] = _pct(row[4]) if len(row) > 4 else None
        elif label == "仅创科" and len(row) >= 4:
            result["break_board_rate_chuangk"] = _pct(row[3])

    if result["break_board_rate_all"] is not None:
        logger.info(f"获取炸板率成功: {result['break_board_rate_all']}%")
        return {**result, "status": "success"}
    logger.warning("炸板率数据未找到")
    return {**result, "status": "failed", "error": "炸板率数据未找到"}


def fetch_board_promotion() -> Dict[str, Any]:
    """
    昨连板晋级率（lbtd_yesterday_jinji）
    
    Returns:
        包含晋级率信息的字典
    """
    url = "https://zhangtingke.com/lbtd_yesterday_jinji"
    html = _fetch(url)
    tables = _extract_table(html)

    result = {
        "level_1_to_2": None,
        "level_2_to_3": None,
        "level_3_to_4": None,
        "level_1_to_2_cnt": None,
        "level_2_to_3_cnt": None,
        "level_3_to_4_cnt": None,
        "source": "zhangtingke:lbtd_yesterday_jinji",
    }

    # 晋级明细行格式：["3进4", "2", "1", "1", "50.0%", ...]
    for row in tables:
        if not row:
            continue
        label = row[0]
        if len(row) < 5:
            continue
        try:
            total = int(row[1])
            promoted = int(row[3])
            rate = float(row[4].replace("%", ""))
        except (ValueError, IndexError):
            continue

        if "1进2" in label:
            result["level_1_to_2"] = rate
            result["level_1_to_2_cnt"] = total
        elif "2进3" in label:
            result["level_2_to_3"] = rate
            result["level_2_to_3_cnt"] = total
        elif "3进4" in label:
            result["level_3_to_4"] = rate
            result["level_3_to_4_cnt"] = total

    if result["level_1_to_2"] is not None:
        logger.info("获取晋级率成功")
        return {**result, "status": "success"}
    logger.warning("晋级率数据未找到")
    return {**result, "status": "failed", "error": "晋级率数据未找到"}


def _pct(s: str) -> Optional[float]:
    """
    解析百分比字符串
    
    Args:
        s: 百分比字符串，例如 "50.0%"
        
    Returns:
        解析后的浮点数，例如 50.0
    """
    try:
        return float(s.replace("%", ""))
    except (ValueError, AttributeError):
        return None


def fetch_all() -> Dict[str, Any]:
    """
    一次性采集涨停客所有数据
    
    Returns:
        包含所有涨停客数据的字典
    """
    logger.info("开始采集涨停客数据")
    board = fetch_highest_board()
    break_rate = fetch_break_board_rate()
    promotion = fetch_board_promotion()

    # 判断整体状态：至少2/3子采集器成功
    sub_ok = sum(1 for s in [board, break_rate, promotion]
                 if s.get("status") == "success")
    overall_status = "success" if sub_ok >= 2 else "failed"

    # 合并所有字段到顶层
    result = {
        "status": overall_status,
        "source": "zhangtingke.com",
    }
    for sub in (board, break_rate, promotion):
        for k, v in sub.items():
            if k == "status":
                continue
            # 标准化字段名
            if k == "break_board_rate_all":
                k = "break_board_rate"
            elif k == "continue_board_count":
                pass  # already correct
            result[k] = v
            
    logger.info(f"涨停客数据采集完成: {overall_status}")
    return result