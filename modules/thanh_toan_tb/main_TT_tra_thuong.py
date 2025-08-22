# modules/thanh_toan_tb/main_TT_tra_thuong.py
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Callable
import pandas as pd
import pandas

def run(
    input_file: str | Path = "data/raw/output-tra-thuong.xlsx",
    output_file: str | Path = "output.xlsx",
    alert_file: str | Path = "alert.xlsx",
):
    input_file = Path(input_file).resolve()
    output_file = Path(output_file).resolve()
    alert_file = Path(alert_file).resolve()

    output_file.parent.mkdir(parents=True, exist_ok=True)
    alert_file.parent.mkdir(parents=True, exist_ok=True)

    required_cols = [
        "Mã NPP","Tên NPP","Mức đăng ký","Số suất đăng kí",
        "Số tiền trả thưởng","Mã khách hàng","Tên khách hàng","Số tiền đã trả thưởng"
    ]
    try:
        dfs = pandas.read_excel(input_file, sheet_name="Số tiền đã trả thưởng")
    except Exception as e:
        raise RuntimeError(f"Lỗi đọc sheet 'Số tiền đã trả thưởng' từ {input_file}: {e}")

    missing = [c for c in required_cols if c not in dfs.columns]
    if missing:
        relax = [c for c in required_cols if c != "Số tiền đã trả thưởng"]
        if any(c not in dfs.columns for c in relax):
            raise RuntimeError(f"Thiếu cột bắt buộc: {missing}. Các cột cần có: {required_cols}")
    for col in required_cols:
        if col not in dfs.columns:
            dfs[col] = pd.NA

    # ===== Logic gốc (không đổi) =====
    alert_list: list[dict] = []

    def alert(msg: str, code=None, name=None, customer_code=None, customer_name=None):
        alert_list.append({
            "Mã NPP": code or "",
            "Tên NPP": name or "",
            "Mã khách hàng": customer_code or "",
            "Tên khách hàng": customer_name or "",
            "Cảnh Báo": msg
        })

    kh_mdk = Counter(
        (row.get("Mã khách hàng","") if pd.notna(row.get("Mã khách hàng")) else "",
         row.get("Mức đăng ký","") if pd.notna(row.get("Mức đăng ký")) else "")
        for _, row in dfs.iterrows()
    )
    for (ma_kh, muc_dk), cnt in kh_mdk.items():
        if ma_kh and muc_dk and cnt > 1:
            alert(f"CẢNH BÁO: Mã khách hàng [{ma_kh}] được trả thưởng {cnt} lần ở mức đăng ký [{muc_dk}]", customer_code=ma_kh)

    d = defaultdict(lambda: {"name":"", "program": defaultdict(lambda: defaultdict(int))})
    def append(tag: str, type: str, price: int, amount: int):
        d[tag]["program"][type][price] += amount

    for _, row in dfs.iterrows():
        D = row["Mã NPP"]; E = row["Tên NPP"]; R = row["Mức đăng ký"]
        S = row["Số suất đăng kí"]; W = row["Số tiền trả thưởng"]
        X = row.get("Số tiền đã trả thưởng", W)
        ma_kh = row.get("Mã khách hàng","") or ""; ten_kh = row.get("Tên khách hàng","") or ""
        if pd.notna(X) and W != X:
            alert(f"Số tiền trả thưởng không khớp: W={W}, X={X}",
                  code=D, name=E, customer_code=ma_kh, customer_name=ten_kh)
            W = X
        if D not in d: d[D]["name"] = E

        if R in ["NDKK_KBS","NDKK_KC"]:
            if S == 0 or W // S not in [90_000]:
                alert(f"SHEET1: {D} - Tên NPP: {E} - NDKK: {W} không hợp lệ",
                      code=D, name=E, customer_code=ma_kh, customer_name=ten_kh)
            else:
                append(D,"NDKK", W//S, S)
        elif R == "KDLINE_MB":
            append(D,"KDLINE", W//S, S)
        elif R in ["2VI","2VT"]:
            append(D,"2VT", 20_000, W//20_000)
        elif R in ["KGVMB","KGV"]:
            append(D,"KGV", 20_000, W//20_000)
        elif R in ["3VI","3VT"]:
            append(D,"3VT", 30_000, W//30_000)
        elif R in ["4VI","4VT"]:
            append(D,"4VT", 40_000, W//40_000)
        elif R == "RO":
            if W == 20_000: append(D,"1RO", 20_000, 1)
            elif W == 40_000: append(D,"2RO", 40_000, 1)
        elif R == "WF":
            price = W//S
            if price in [50_000,120_000,170_000]:
                append(D,"GVCS", price, S)
            elif price in [180_000]:
                append(D,"GVCS", 120_000, S); append(D,"WF", 60_000, S)
            else:
                append(D,"WF", price, S)
        elif R == "NMCD":
            append(D,"NMCD", W, 1)
        else:
            append(D, R, W//S, S)

    count = defaultdict(lambda: {'name':'','count':{
        'KDLINE':{420:0,300:0,120:0}, 'K4T':{420:0,300:0,120:0},
        'K3T':{260:0,180:0,80:0}, 'WF':{220:0,160:0,60:0},
        'GVCS':{170:0,120:0,50:0}, 'NDKK':{90:0}, 'RO_2VI':{40:0},
        '1RO':{20:0}, '2RO':{40:0}, 'KGV':{20:0}, '2VT':{20:0},
        '3VT':{30:0}, '4VT':{40:0}, 'LTLKC':{30:0}
    }})
    count2 = defaultdict(lambda: {'name':'','count':{'DHLM':{50:0},'NMCD':{}}})

    for tag, data in d.items():
        count[tag]['name'] = data['name']
        for typ, prices in data["program"].items():
            for price, amount in prices.items():
                if typ in count[tag]['count']:
                    if (price // 1_000) not in count[tag]['count'][typ]:
                        alert(f"SHEET1: {tag} - Tên NPP: {data['name']} - {typ}: {price} không hợp lệ",
                              code=tag, name=data['name'])
                        continue
                    count[tag]['count'][typ][price // 1_000] += amount

    for tag, data in d.items():
        count2[tag]['name'] = data['name']
        for typ, prices in data["program"].items():
            for price, amount in prices.items():
                if typ == "DHLM":
                    if price not in [50_000,100_000]:
                        alert(f"SHEET2: {tag} - Tên NPP: {data['name']} - DHLM: {price} không hợp lệ",
                              code=tag, name=data['name'])
                        continue
                    count2[tag]['count'][typ][50] += amount

    out_df = {
        "CODE NPP":["","",""], "TÊN NPP":["","",""],
        "C":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ ĐẬU LINE","Đạt mức 420"],
        "D":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ ĐẬU LINE","Đạt mức 300"],
        "E":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ ĐẬU LINE","Đạt mức 120"],
        "F":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ 4 TẦNG","Đạt mức 420"],
        "G":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ 4 TẦNG","Đạt mức 300"],
        "H":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ 4 TẦNG","Đạt mức 120"],
        "I":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ 3 TẦNG","Đạt mức 260"],
        "J":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ 3 TẦNG","Đạt mức 180"],
        "K":["CHƯƠNG TRÌNH CHƯNG BÀY","KỆ 3 TẦNG","Đạt mức 80"],
        "L":["CHƯƠNG TRÌNH CHƯNG BÀY","WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG","Đạt mức 220"],
        "M":["CHƯƠNG TRÌNH CHƯNG BÀY","WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG","Đạt mức 160"],
        "N":["CHƯƠNG TRÌNH CHƯNG BÀY","WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG","Đạt mức 60"],
        "O":["CHƯƠNG TRÌNH CHƯNG BÀY","WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG","Đạt mức 170"],
        "P":["CHƯƠNG TRÌNH CHƯNG BÀY","WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG","Đạt mức 120"],
        "Q":["CHƯƠNG TRÌNH CHƯNG BÀY","WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG","Đạt mức 50"],
        "R":["CHƯƠNG TRÌNH CHƯNG BÀY","NGON ĐẾN KHÁT KHAO","Đạt mức 90"],
        "S":["CHƯƠNG TRÌNH CHƯNG BÀY","RỖ + 2 VĨ TREO","Đạt mức 40"],
        "T":["CHƯƠNG TRÌNH CHƯNG BÀY","RỖ DÀI HẠN","Đạt mức 20"],
        "U":["CHƯƠNG TRÌNH CHƯNG BÀY","RỖ DÀI HẠN","Đạt mức 40"],
        "V":["CHƯƠNG TRÌNH CHƯNG BÀY","KHAY GIA VỊ","Đạt mức 20"],
        "W":["CHƯƠNG TRÌNH CHƯNG BÀY","VĨ TREO DÀI HẠN","Đạt mức 20"],
        "X":["CHƯƠNG TRÌNH CHƯNG BÀY","VĨ TREO DÀI HẠN","Đạt mức 30"],
        "Y":["CHƯƠNG TRÌNH CHƯNG BÀY","VĨ TREO DÀI HẠN","Đạt mức 40"],
        "Z":["CHƯƠNG TRÌNH CHƯNG BÀY","XỐT LẨU THÁI & XỐT LẨU KIM CHI","Đạt mức 30"],
        "AA":["CHƯƠNG TRÌNH CHƯNG BÀY","TỔNG SỐ SUẤT TRẢ THƯỞNG","TỔNG SỐ SUẤT TRẢ THƯỞNG"],
        "AB":["CHƯƠNG TRÌNH CHƯNG BÀY","TỔNG TIỀN TRẢ THƯỞNG","TỔNG TIỀN TRẢ THƯỞNG"],
    }

    for tag, data in count.items():
        out_df["CODE NPP"].append(tag)
        out_df["TÊN NPP"].append(data["name"])
        _sum = 0; total_price = 0
        for typ, prices in data["count"].items():
            if typ == "KDLINE":
                out_df["C"].append(prices[420]); out_df["D"].append(prices[300]); out_df["E"].append(prices[120])
            elif typ == "K4T":
                out_df["F"].append(prices[420]); out_df["G"].append(prices[300]); out_df["H"].append(prices[120])
            elif typ == "K3T":
                out_df["I"].append(prices[260]); out_df["J"].append(prices[180]); out_df["K"].append(prices[80])
            elif typ == "WF":
                out_df["L"].append(prices[220]); out_df["M"].append(prices[160]); out_df["N"].append(prices[60])
            elif typ == "GVCS":
                out_df["O"].append(prices[170]); out_df["P"].append(prices[120]); out_df["Q"].append(prices[50])
            elif typ == "NDKK": out_df["R"].append(prices[90])
            elif typ == "RO_2VI": out_df["S"].append(prices[40])
            elif typ == "1RO": out_df["T"].append(prices[20])
            elif typ == "2RO": out_df["U"].append(prices[40])
            elif typ == "KGV": out_df["V"].append(prices[20])
            elif typ == "2VT": out_df["W"].append(prices[20])
            elif typ == "3VT": out_df["X"].append(prices[30])
            elif typ == "4VT": out_df["Y"].append(prices[40])
            elif typ == "LTLKC": out_df["Z"].append(prices[30])

            _sum += sum(prices.values())
            for price, amount in prices.items():
                total_price += price * amount

        out_df["AA"].append(_sum)
        out_df["AB"].append(total_price * 1_000)

    filename_df = dfs
    nmcd_money_list = sorted(filename_df.loc[filename_df["Mức đăng ký"]=="NMCD","Số tiền đã trả thưởng"].dropna().unique())
    nmcd_money_list = [int(x) for x in nmcd_money_list]

    out_df2 = {"CODE NPP": [], "TÊN NPP": [], "DHLM 50": []}
    for val in nmcd_money_list:
        out_df2[f"NMCD {int(val/1000)}"] = []
    out_df2["TỔNG SỐ SUẤT"] = []; out_df2["TỔNG TIỀN"] = []

    npp_set = set(zip(filename_df["Mã NPP"], filename_df["Tên NPP"]))
    for code, name in sorted(npp_set):
        out_df2["CODE NPP"].append(code); out_df2["TÊN NPP"].append(name)
        dhlm_rows = filename_df[(filename_df["Mã NPP"]==code)&(filename_df["Tên NPP"]==name)&(filename_df["Mức đăng ký"]=="DHLM")]
        cnt_dhlm = 0
        for _, r in dhlm_rows.iterrows():
            w = r["Số tiền trả thưởng"]; so_suat = int(round((w or 0)/50_000)) if pd.notna(w) else 0
            cnt_dhlm += so_suat
            if so_suat not in [1,2] and so_suat>0:
                alert(f"DHLM số suất bất thường: Số tiền {w}, số suất = {so_suat} (khác 1,2)", code=code, name=name)
        out_df2["DHLM 50"].append(cnt_dhlm)

        _sum = cnt_dhlm; _money = dhlm_rows["Số tiền trả thưởng"].sum()
        for val in nmcd_money_list:
            cnt = filename_df[(filename_df["Mã NPP"]==code)&(filename_df["Tên NPP"]==name)
                              &(filename_df["Mức đăng ký"]=="NMCD")&(filename_df["Số tiền đã trả thưởng"]==val)].shape[0]
            out_df2[f"NMCD {int(val/1000)}"].append(cnt)
            _sum += cnt; _money += cnt * val
        out_df2["TỔNG SỐ SUẤT"].append(_sum); out_df2["TỔNG TIỀN"].append(_money)

    # Sheet3 tổng hợp
    sheet3 = {}
    for _, row in dfs.iterrows():
        code_npp = row["Mã NPP"]; ten_npp = row["Tên NPP"]; R = row["Mức đăng ký"]
        S = row["Số suất đăng kí"]; W = row["Số tiền trả thưởng"]; X = row.get("Số tiền đã trả thưởng", W)
        if pd.notna(X) and W != X:
            W = X
        if code_npp not in sheet3:
            sheet3[code_npp] = {
                "CODE NPP": code_npp, "NHÀ PHÂN PHỐI": ten_npp,
                "CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50": 0, "GIA VỊ GÓI 50": 0, "GIA VỊ GÓI 80": 0,
                "SẢN PHẨM ĐÔNG LẠNH 50": 0, "SẢN PHẨM ĐÔNG LẠNH 100": 0,
                "TỔNG SỐ SUẤT TRẢ THƯỞNG": 0, "TỔNG TIỀN": 0
            }
        e = sheet3[code_npp]
        if R == "KOS_XXTG_BS":
            if S>0 and W//S==50_000: e["CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50"] += S
        if str(R).strip().upper().startswith("GVI"):
            if S>0 and W//S==50_000: e["GIA VỊ GÓI 50"] += S
            elif S>0 and W//S==80_000: e["GIA VỊ GÓI 80"] += S
        if R in ["M1_POSTER","M2_DECAL"]:
            if S>0 and W//S==50_000: e["SẢN PHẨM ĐÔNG LẠNH 50"] += S
            elif S>0 and W//S==100_000: e["SẢN PHẨM ĐÔNG LẠNH 100"] += S

        e["TỔNG SỐ SUẤT TRẢ THƯỞNG"] = (
            e["CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50"] + e["GIA VỊ GÓI 50"] + e["GIA VỊ GÓI 80"]
            + e["SẢN PHẨM ĐÔNG LẠNH 50"] + e["SẢN PHẨM ĐÔNG LẠNH 100"]
        )
        e["TỔNG TIỀN"] = (
            e["CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50"] * 50_000
            + e["GIA VỊ GÓI 50"] * 50_000
            + e["GIA VỊ GÓI 80"] * 80_000
            + e["SẢN PHẨM ĐÔNG LẠNH 50"] * 50_000
            + e["SẢN PHẨM ĐÔNG LẠNH 100"] * 100_000
        )

    sheet3_df = pd.DataFrame(sheet3.values())
    sheet3_df.index += 1
    if "STT" in sheet3_df.columns:
        sheet3_df = sheet3_df.drop(columns=["STT"])
    sheet3_df.insert(0, "STT", sheet3_df.index)

    # Chuẩn bị DF cho 3 sheet
    df1_raw = pandas.DataFrame(out_df)
    df2 = pandas.DataFrame(out_df2)
    df3 = sheet3_df.copy()

    df1 = df1_raw.iloc[2:].reset_index(drop=True).rename(columns={
        "CODE NPP":"CODE NPP","TÊN NPP":"TÊN NPP",
        "C":"Đạt mức 420","D":"Đạt mức 300","E":"Đạt mức 120",
        "F":"Đạt mức 420","G":"Đạt mức 300","H":"Đạt mức 120",
        "I":"Đạt mức 260","J":"Đạt mức 180","K":"Đạt mức 80",
        "L":"Đạt mức 220","M":"Đạt mức 160","N":"Đạt mức 60",
        "O":"Đạt mức 170","P":"Đạt mức 120","Q":"Đạt mức 50",
        "R":"Đạt mức 90","S":"Đạt mức 40",
        "T":"Đạt mức 20","U":"Đạt mức 40",
        "V":"Đạt mức 20","W":"Đạt mức 20","X":"Đạt mức 30","Y":"Đạt mức 40",
        "Z":"Đạt mức 30",
        "AA":"TỔNG SỐ SUẤT TRẢ THƯỞNG",
        "AB":"TỔNG TIỀN TRẢ THƯỞNG",
    })

    with pandas.ExcelWriter(str(output_file), engine="xlsxwriter") as writer:
        wb = writer.book

        # =============== SHEET 1 ===============
        df1.to_excel(writer, sheet_name="Sheet1", index=False, startrow=2)
        ws1 = writer.sheets["Sheet1"]

        title_fmt = wb.add_format({"bold":True,"align":"center","valign":"vcenter","bg_color":"#F6C69E","border":1,"font_size":12})
        grp_fmt   = wb.add_format({"bold":True,"align":"center","valign":"vcenter","bg_color":"#CDE4C2","border":1})
        sub_fmt   = wb.add_format({"bold":True,"align":"center","valign":"vcenter","bg_color":"#E8F4DF","border":1})
        left_hdr  = wb.add_format({"bold":True,"align":"center","valign":"vcenter","bg_color":"#E8F4DF","border":1})

        # banner + nhóm
        ws1.merge_range(0,2,0,16,"CHƯƠNG TRÌNH CHƯNG BÀY",title_fmt)
        ws1.merge_range(1,2,1,4,"KỆ ĐẬU LINE",grp_fmt)
        ws1.merge_range(1,5,1,7,"KỆ 4 TẦNG",grp_fmt)
        ws1.merge_range(1,8,1,10,"KỆ 3 TẦNG",grp_fmt)
        ws1.merge_range(1,11,1,13,"WINDOW FRAME",grp_fmt)
        ws1.merge_range(1,14,1,16,"GIA VỊ CUỘC SỐNG",grp_fmt)
        ws1.write(1,17,"NGON ĐẾN KHÁT KHAO",grp_fmt)
        ws1.write(1,18,"RỖ + 2 VĨ TREO",grp_fmt)
        ws1.merge_range(1,19,1,20,"RỖ DÀI HẠN",grp_fmt)
        ws1.write(1,21,"KHAY GIA VỊ",grp_fmt)
        ws1.merge_range(1,22,1,24,"VĨ TREO DÀI HẠN",grp_fmt)
        ws1.write(1,25,"XỐT LẨU THÁI & XỐT LẨU KIM CHI",grp_fmt)
        ws1.merge_range(0,26,1,26,"TỔNG SỐ SUẤT TRẢ THƯỞNG",title_fmt)
        ws1.merge_range(0,27,1,27,"TỔNG TIỀN TRẢ THƯỞNG",title_fmt)

        def sub(start_col, labels):
            for i, t in enumerate(labels): ws1.write(2, start_col+i, t, sub_fmt)
        sub(2, ["Đạt mức 420","Đạt mức 300","Đạt mức 120"])
        sub(5, ["Đạt mức 420","Đạt mức 300","Đạt mức 120"])
        sub(8, ["Đạt mức 260","Đạt mức 180","Đạt mức 80"])
        sub(11,["Đạt mức 220","Đạt mức 160","Đạt mức 60"])
        sub(14,["Đạt mức 170","Đạt mức 120","Đạt mức 50"])
        ws1.write(2,17,"Đạt mức 90",sub_fmt); ws1.write(2,18,"Đạt mức 40",sub_fmt)
        ws1.write(2,19,"Đạt mức 20",sub_fmt); ws1.write(2,20,"Đạt mức 40",sub_fmt)
        ws1.write(2,21,"Đạt mức 20",sub_fmt)
        ws1.write(2,22,"Đạt mức 20",sub_fmt); ws1.write(2,23,"Đạt mức 30",sub_fmt); ws1.write(2,24,"Đạt mức 40",sub_fmt)
        ws1.write(2,25,"Đạt mức 30",sub_fmt)

        ws1.write(2,0,"CODE NPP",left_hdr); ws1.write(2,1,"TÊN NPP",left_hdr)

        ws1.set_column(0,1,26); ws1.set_column(2,25,12); ws1.set_column(26,26,18)
        # cột AB định dạng tiền (KHÔNG border)
        fmt_money1_no_border = wb.add_format({"align":"right","num_format":"#,##0"})
        ws1.set_column(27,27,20, fmt_money1_no_border)

        ws1.freeze_panes(3,2)

        # kẻ viền trong vùng dữ liệu
        data_start_row = 3
        data_end_row = 2 + len(df1)
        fmt_border_only = wb.add_format({"border":1})
        fmt_left = wb.add_format({"align":"left","border":1})
        fmt_center_num0 = wb.add_format({"align":"center","border":1,"num_format":"0"})

        # A:B
        ws1.conditional_format(data_start_row,0,data_end_row,1,{"type":"no_blanks","format":fmt_left})
        ws1.conditional_format(data_start_row,0,data_end_row,1,{"type":"blanks","format":fmt_border_only})
        # C:Y
        ws1.conditional_format(data_start_row,2,data_end_row,24,{"type":"no_blanks","format":fmt_center_num0})
        ws1.conditional_format(data_start_row,2,data_end_row,24,{"type":"blanks","format":fmt_border_only})
        # Z
        ws1.conditional_format(data_start_row,25,data_end_row,25,{"type":"no_blanks","format":fmt_center_num0})
        ws1.conditional_format(data_start_row,25,data_end_row,25,{"type":"blanks","format":fmt_border_only})
        # AA
        ws1.conditional_format(data_start_row,26,data_end_row,26,{"type":"no_blanks","format":fmt_center_num0})
        ws1.conditional_format(data_start_row,26,data_end_row,26,{"type":"blanks","format":fmt_border_only})
        # AB (chỉ border)
        ws1.conditional_format(data_start_row,27,data_end_row,27,{"type":"no_blanks","format":fmt_border_only})
        ws1.conditional_format(data_start_row,27,data_end_row,27,{"type":"blanks","format":fmt_border_only})

        # =============== SHEET 2 ===============
        df2_stt = df2.copy(); df2_stt.index += 1
        if "STT" in df2_stt.columns: df2_stt = df2_stt.drop(columns=["STT"])
        df2_stt.insert(0,"STT", df2_stt.index)
        df2_stt.to_excel(writer, sheet_name="Sheet2", index=False, startrow=1)
        ws2 = writer.sheets["Sheet2"]

        hdr2 = wb.add_format({"bold":True,"align":"center","valign":"vcenter","bg_color":"#F6C69E","border":1})
        for c, name in enumerate(df2_stt.columns.tolist()): ws2.write(1,c,name,hdr2)
        ws2.set_row(1,20)
        ws2.set_column(0,0,6); ws2.set_column(1,1,16); ws2.set_column(2,2,30)

        # định dạng tiền cho cột "TỔNG TIỀN" (KHÔNG border)
        money_idx = None
        fmt_money2_no_border = wb.add_format({"align":"right","num_format":"#,##0"})
        try:
            money_idx = df2_stt.columns.tolist().index("TỔNG TIỀN")
            ws2.set_column(money_idx, money_idx, 18, fmt_money2_no_border)
        except ValueError:
            pass
        last_col2 = len(df2_stt.columns)-1
        if last_col2 >= 3: ws2.set_column(3, last_col2, 14)

        ws2.freeze_panes(2,1)

        # border vùng dữ liệu
        s2_start = 2; s2_end = 1 + len(df2_stt)
        fmt_border_only = wb.add_format({"border":1})
        fmt_center_no_num = wb.add_format({"align":"center","border":1})

        # STT/CODE/TÊN
        ws2.conditional_format(s2_start,0,s2_end,0,{"type":"no_blanks","format":fmt_center_no_num})
        ws2.conditional_format(s2_start,0,s2_end,0,{"type":"blanks","format":fmt_border_only})
        ws2.conditional_format(s2_start,1,s2_end,1,{"type":"no_blanks","format":fmt_center_no_num})
        ws2.conditional_format(s2_start,1,s2_end,1,{"type":"blanks","format":fmt_border_only})
        ws2.conditional_format(s2_start,2,s2_end,2,{"type":"no_blanks","format":fmt_border_only})
        ws2.conditional_format(s2_start,2,s2_end,2,{"type":"blanks","format":fmt_border_only})

        def cond_center(c1,c2):
            if c1 <= c2:
                ws2.conditional_format(s2_start,c1,s2_end,c2,{"type":"no_blanks","format":fmt_center_no_num})
                ws2.conditional_format(s2_start,c1,s2_end,c2,{"type":"blanks","format":fmt_border_only})

        if last_col2 >= 3:
            if money_idx is None:
                cond_center(3,last_col2)
            else:
                cond_center(3, money_idx-1)
                cond_center(money_idx+1, last_col2)
                ws2.conditional_format(s2_start, money_idx, s2_end, money_idx, {"type":"no_blanks","format":fmt_border_only})
                ws2.conditional_format(s2_start, money_idx, s2_end, money_idx, {"type":"blanks","format":fmt_border_only})

        # =============== SHEET 3 ===============
        df3.to_excel(writer, sheet_name="Sheet3", index=False, startrow=1)
        ws3 = writer.sheets["Sheet3"]

        hdr3 = wb.add_format({"bold":True,"align":"center","valign":"vcenter","bg_color":"#F6C69E","border":1})
        for c, name in enumerate(df3.columns.tolist()): ws3.write(1,c,name,hdr3)
        ws3.set_row(1,20)
        ws3.set_column(0,0,6); ws3.set_column(1,1,16); ws3.set_column(2,2,30)

        money_col3 = None
        fmt_money3_no_border = wb.add_format({"align":"right","num_format":"#,##0"})
        try:
            money_col3 = df3.columns.tolist().index("TỔNG TIỀN")
            ws3.set_column(money_col3, money_col3, 18, fmt_money3_no_border)
        except ValueError:
            pass
        last_col3 = len(df3.columns)-1
        if last_col3 >= 3: ws3.set_column(3, last_col3, 16)

        s3_start = 2; s3_end = 1 + len(df3)
        fmt_center_no_num = wb.add_format({"align":"center","border":1})
        fmt_border_only = wb.add_format({"border":1})

        ws3.conditional_format(s3_start,0,s3_end,0,{"type":"no_blanks","format":fmt_center_no_num})
        ws3.conditional_format(s3_start,0,s3_end,0,{"type":"blanks","format":fmt_border_only})
        ws3.conditional_format(s3_start,1,s3_end,1,{"type":"no_blanks","format":fmt_center_no_num})
        ws3.conditional_format(s3_start,1,s3_end,1,{"type":"blanks","format":fmt_border_only})
        ws3.conditional_format(s3_start,2,s3_end,2,{"type":"no_blanks","format":fmt_border_only})
        ws3.conditional_format(s3_start,2,s3_end,2,{"type":"blanks","format":fmt_border_only})

        def cond_center3(c1,c2):
            if c1 <= c2:
                ws3.conditional_format(s3_start,c1,s3_end,c2,{"type":"no_blanks","format":fmt_center_no_num})
                ws3.conditional_format(s3_start,c1,s3_end,c2,{"type":"blanks","format":fmt_border_only})

        if last_col3 >= 3:
            if money_col3 is None:
                cond_center3(3,last_col3)
            else:
                cond_center3(3, money_col3-1)
                cond_center3(money_col3+1, last_col3)
                ws3.conditional_format(s3_start, money_col3, s3_end, money_col3, {"type":"no_blanks","format":fmt_border_only})
                ws3.conditional_format(s3_start, money_col3, s3_end, money_col3, {"type":"blanks","format":fmt_border_only})

    if alert_list:
        pd.DataFrame(alert_list).to_excel(str(alert_file), index=False)

if __name__ == "__main__":
    run()
