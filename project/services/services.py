import requests
import pandas as pd
from datetime import datetime
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import io
import re
from pathlib import Path
import subprocess

def tv():
    url = "https://scanner.tradingview.com/japan/scan"

    payload = {
        "columns": [
            "ticker-view",#株コード等
            "close",#終値
            "change",#前日比
            "price_earnings_ttm",#PER
            "price_book_fq",#PBR
            "market_cap_basic",#時価総額
            "dividends_yield_current",#配当利回り
            "return_on_equity_fq",#ROE
            "return_on_assets_fq",#ROA
            "shrhldrs_equity_to_total_assets_fy",#自己資本比率
            "sector.tr",#セクター
            "industry.tr",#業種
            "earnings_release_next_trading_date_fq"#次回決算発表日
        ],
        "filter": [
            {
                "left": "shrhldrs_equity_to_total_assets_fy",
                "operation": "greater",
                "right": 0.35
            },
            {
                "left": "return_on_assets_fq",
                "operation": "greater",
                "right": 3
            },
            {
                "left": "market_cap_basic",
                "operation": "egreater",
                "right": 10000000000
            },
            {
                "left": "return_on_equity_fq",
                "operation": "greater",
                "right": 7
            },
            {
                "left": "price_book_fq",
                "operation": "eless",
                "right": 1.3
            },
            {
                "left": "price_earnings_ttm",
                "operation": "eless",
                "right": 12
            },
            {
                "left": "dividends_yield_current",
                "operation": "greater",
                "right": 3
            },
            {
                "left": "is_primary",
                "operation": "equal",
                "right": True
            }
        ],
        "ignore_unknown_fields": False,
        "options": {
            "lang": "ja"
        },
        "range": [
            0,
            1000
        ],
        "sort": {
            "sortBy": "ticker-view-sort",
            "sortOrder": "asc"
        },
        "markets": [
            "japan"
        ],
        "filter2": {
            "operator": "and",
            "operands": [
                {
                    "operation": {
                        "operator": "or",
                        "operands": [
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "stock"
                                            }
                                        },
                                        {
                                            "expression": {
                                                "left": "typespecs",
                                                "operation": "has",
                                                "right": [
                                                    "common"
                                                ]
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "stock"
                                            }
                                        },
                                        {
                                            "expression": {
                                                "left": "typespecs",
                                                "operation": "has",
                                                "right": [
                                                    "preferred"
                                                ]
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "dr"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "operation": {
                                    "operator": "and",
                                    "operands": [
                                        {
                                            "expression": {
                                                "left": "type",
                                                "operation": "equal",
                                                "right": "fund"
                                            }
                                        },
                                        {
                                            "expression": {
                                                "left": "typespecs",
                                                "operation": "has_none_of",
                                                "right": [
                                                    "etf",
                                                    "mutual"
                                                ]
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                {
                    "expression": {
                        "left": "typespecs",
                        "operation": "has_none_of",
                        "right": [
                            "pre-ipo"
                        ]
                    }
                }
            ]
        }
    }

    r = requests.post(url, json=payload)

    data = r.json()

    #print(data)

    columns = [
        "symbol",
        "価格",
        "前日比",
        "PER",
        "PBR",
        "時価総額",
        "配当利回り",
        "ROE",
        "ROA",
        "自己資本比率",
        "セクター",
        "業種",
        "次回決算発表日"
    ]

    rows = []

    for item in data["data"]:
        record = dict(zip(columns, item["d"]))

        record["コード"] = record["symbol"]["name"]
        record["会社名"] = record["symbol"]["description"]
        record["市場"] = record["symbol"]["exchange"]
        record["価格"]
        record["前日比"]
        record["PER"]
        record["PBR"]
        record["時価総額"]
        record["配当利回り"]
        record["ROE"]
        record["ROA"]
        record["自己資本比率"]
        record["次回決算発表日"] = datetime.fromtimestamp(record["次回決算発表日"]).strftime("%Y-%m-%d") if record["次回決算発表日"] else None

        del record["symbol"]

        rows.append(record)

    df = pd.DataFrame(rows)

    cols = [
        "コード",
        "会社名",
        "市場",
        *[c for c in df.columns if c not in ("コード", "会社名", "市場")]
    ]

    df = df[cols]

    #print(df)

    return df

def human_number(x):
        if x is None:
            return ""
        
        if abs(x) >= 1e12:
            return f"{x/1e12:.2f}T"
        elif abs(x) >= 1e9:
            return f"{x/1e9:.2f}B"
        elif abs(x) >= 1e6:
            return f"{x/1e6:.2f}M"
        elif abs(x) >= 1e3:
            return f"{x/1e3:.2f}K"
        else:
            return f"{x:g}"

def irbank(row):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    index = row.name
    code = row.iloc[0]

    EPSBPS = False
    haitou = False

    #html取得
    session = requests.Session()
    session.headers.update(headers)
    res = session.get(f"https://irbank.net/{code}/valuation")
    soupv = BeautifulSoup(res.text, "html.parser")

    #EPSBPS取得
    caption = soupv.find("caption", string="EPS及びBPS")
    if caption:
        target_table = caption.find_parent("table")

    #データフレーム化
    if target_table:
        data = pd.read_html(io.StringIO(str(target_table)))[0]
    
    #EPSとBPSの数値化
    data10 = data[-11:-1]
    data10 = pd.DataFrame(data10)

    try:
        data10["EPS"] = data10["EPS"].str.strip("円")
        data10["BPS"] = data10["BPS"].str.strip("円")
        data10["EPS"] = data10["EPS"].astype(float)
        data10["BPS"] = data10["BPS"].astype(float)

    except ValueError:
        EPSBPS = False

    #print(data10)
        
    if len(data10) == 10:
        EPSBPS = all(
            data10.iloc[i]["EPS"] > 0 and
            data10.iloc[i]["BPS"] > data10.iloc[i-1]["BPS"]
            for i in range(1, 10)
        )
        #print(EPSBPS)

        dividend = session.get(f"https://irbank.net/{code}/dividend",headers=headers)
        soupd = BeautifulSoup(dividend.text, "html.parser")

        target_tabled = soupd.find("tbody")
        cells = target_tabled.find_all("td")
        retsus = []
        current_year = None
        current_row = None
        kinds = {"予想", "実績", "修正"}

        for td in  cells:
            text = td.get_text(" ", strip=True)

            if re.search(r"^\d{4}年", text):
                current_year = text
                continue

            if text in kinds:
                if current_row:
                    retsus.append(current_row)
                current_row = [current_year, text]

            else:
                if current_row is not None:
                    current_row.append(text)

        if current_row:
            retsus.append(current_row)

        normalized = []

        for retsu in retsus:

            year = retsu[0]
            kind = retsu[1]

            data = retsu[2:]

            dividend_yield = None

            if data and "%" in data[-1]:
                dividend_yield = data.pop()
                
            split_adj = data.pop() if data else None
            total = data.pop() if data else None
            year_end = data.pop() if data else None
            interim = data.pop() if data else None

            normalized.append([
                year,
                kind,
                interim,
                year_end,
                total,
                split_adj,
                dividend_yield
            ]
            )

        columns = ["年度", "区分", "中間", "期末", "合計", "分割調整", "配当利回り"]

        divi = pd.DataFrame(normalized, columns=columns)
        
        jisseki = divi[divi["区分"] == "実績"]
        jisseki = jisseki[-10:]
        
        haitou = True
        count = 0

        for i in range(1, 10):
            retsu1 = jisseki.iloc[i]

            if retsu1["分割調整"] is not None:
                if retsu1["分割調整"] < jisseki.iloc[i-1]["分割調整"]:
                    count += 1
                    if count >= 2:
                        haitou = False
                    break
                elif retsu1["分割調整"] == 0:
                    haitou = False
                    break

            else:
                if retsu1["合計"] < jisseki.iloc[i-1]["合計"]:
                    count += 1
                    if count >= 2:
                        haitou = False
                    break

    return index, code, EPSBPS, haitou

def screenstock(df, progress_callback=None):

    #証券コード取得
    codes = df.iloc[:, 0].tolist()
    #print("-----------------------------------------------------------------------------------------------------------------------")
    #print(codes)

    rows = [row for _, row in df.iterrows()]
    total = len(rows)
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        for i, result in enumerate(executor.map(irbank, rows), start = 1):
            results.append(result)

            if progress_callback is not None:
                progress_callback(i, total)

            print("データ取得中")
            print(f"\rprocessed: {i}/{total} ({i/total:.1%})", end="", flush=True)
            print("データ取得完了")
    print()

    drop_index =[]

    for index, code, EPSBPS, haitou in results:
        #print(f"{code}: EPSBPS = {EPSBPS}, haitou = {haitou}")
        
        if not (EPSBPS and haitou):
            drop_index.append(index)
    result = df.drop(drop_index)

    return result

def outputcsv(result):

    dt = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_dir / f"{dt}.csv" , index=False, encoding="utf-8-sig")

def search(progress_callback=None):
    df = tv()
    result = screenstock(df, progress_callback)
    return result

def opendir():
    output = Path("output").resolve()
    subprocess.Popen(["explorer", str(output)])