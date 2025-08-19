# modules/thanh_toan_tb/main_TT_tra_thuong.py
from pathlib import Path
from collections import defaultdict, Counter
from typing import List, Callable
import os

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

    # đảm bảo thư mục cha tồn tại nếu đường dẫn có folder
    output_file.parent.mkdir(parents=True, exist_ok=True)
    alert_file.parent.mkdir(parents=True, exist_ok=True)

    required_cols = [
        'Mã NPP','Tên NPP','Mức đăng ký','Số suất đăng kí',
        'Số tiền trả thưởng','Mã khách hàng','Tên khách hàng','Số tiền đã trả thưởng'
    ]
    try:
        dfs = pandas.read_excel(input_file, sheet_name='Số tiền đã trả thưởng')
    except Exception as e:
        raise RuntimeError(f"Lỗi đọc sheet 'Số tiền đã trả thưởng' từ {input_file}: {e}")

    missing = [c for c in required_cols if c not in dfs.columns]
    if missing:
        relax_cols = [c for c in required_cols if c != 'Số tiền đã trả thưởng']
        if any(c not in dfs.columns for c in relax_cols):
            raise RuntimeError(f"Thiếu cột bắt buộc: {missing}. Các cột cần có: {required_cols}")
    for col in required_cols:
        if col not in dfs.columns:
            dfs[col] = pd.NA

    # ===== GIỮ NGUYÊN LOGIC GỐC (đoạn dưới giữ như bạn gửi) =====
    alert_list: list[dict] = []

    def alert(msg: str, code=None, name=None, customer_code=None, customer_name=None):
        alert_list.append({
            'Mã NPP': code or "",
            'Tên NPP': name or "",
            'Mã khách hàng': customer_code or "",
            'Tên khách hàng': customer_name or "",
            'Cảnh Báo': msg
        })

    kh_mdk_tuples = []
    for _, row in dfs.iterrows():
        ma_kh = row.get('Mã khách hàng', "")
        muc_dk = row.get('Mức đăng ký', "")
        if pd.isna(ma_kh): ma_kh = ""
        if pd.isna(muc_dk): muc_dk = ""
        kh_mdk_tuples.append((ma_kh, muc_dk))

    counter = Counter(kh_mdk_tuples)
    for (ma_kh, muc_dk), count_val in counter.items():
        if ma_kh and muc_dk and count_val > 1:
            alert(f"CẢNH BÁO: Mã khách hàng [{ma_kh}] được trả thưởng {count_val} lần ở mức đăng ký [{muc_dk}]",
                  customer_code=ma_kh)

    d = defaultdict(lambda: {'name': '', 'program': defaultdict(lambda: defaultdict(lambda: 0))})
    def append(tag: str, type: str, price: int, amount: int):
        d[tag]['program'][type][price] += amount

    for _, row in dfs.iterrows():
        D = row['Mã NPP']; E = row['Tên NPP']; R = row['Mức đăng ký']
        S = row['Số suất đăng kí']; W = row['Số tiền trả thưởng']
        X = row.get('Số tiền đã trả thưởng', W)
        ma_kh = row.get('Mã khách hàng', ""); ten_kh = row.get('Tên khách hàng', "")
        if pd.isna(ma_kh): ma_kh = ""
        if pd.isna(ten_kh): ten_kh = ""
        if not pd.isna(X) and W != X:
            alert(f"Số tiền trả thưởng không khớp: W={W}, X={X}",
                  code=D, name=E, customer_code=ma_kh, customer_name=ten_kh)
            W = X
        if D not in d: d[D]['name'] = E

        if R in ['NDKK_KBS','NDKK_KC']:
            if S == 0 or W // S not in [90_000]:
                alert(f"SHEET1: {D} - Tên NPP: {E} - NDKK: {W} không hợp lệ",
                      code=D, name=E, customer_code=ma_kh, customer_name=ten_kh)
            else:
                append(D, 'NDKK', W // S, S)
        elif R == 'KDLINE_MB':
            append(D, 'KDLINE', W // S, S)
        elif R in ['2VI','2VT']:
            append(D, '2VT', 20_000, W // 20_000)
        elif R in ['KGVMB','KGV']:
            append(D, 'KGV', 20_000, W // 20_000)
        elif R in ['3VI','3VT']:
            append(D, '3VT', 30_000, W // 30_000)
        elif R in ['4VI','4VT']:
            append(D, '4VT', 40_000, W // 40_000)
        elif R == 'RO':
            if W == 20_000: append(D, '1RO', 20_000, 1)
            elif W == 40_000: append(D, '2RO', 40_000, 1)
        elif R == 'WF':
            price = W // S
            if price in [50_000,120_000,170_000]:
                append(D, 'GVCS', price, S)
            elif price in [180_000]:
                append(D, 'GVCS', 120_000, S); append(D, 'WF', 60_000, S)
            else:
                append(D, 'WF', price, S)
        elif R == 'NMCD':
            append(D, 'NMCD', W, 1)
        else:
            append(D, R, W // S, S)

    count = defaultdict(lambda: {'name': '', 'count': {
        'KDLINE': {420:0,300:0,120:0}, 'K4T': {420:0,300:0,120:0},
        'K3T': {260:0,180:0,80:0}, 'WF': {220:0,160:0,60:0},
        'GVCS': {170:0,120:0,50:0}, 'NDKK': {90:0}, 'RO_2VI': {40:0},
        '1RO': {20:0}, '2RO': {40:0}, 'KGV': {20:0}, '2VT': {20:0},
        '3VT': {30:0}, '4VT': {40:0}, 'LTLKC': {30:0}
    }})
    count2 = defaultdict(lambda: {'name':'','count':{'DHLM':{50:0},'NMCD':{}}})

    for tag, data in d.items():
        count[tag]['name'] = data['name']
        for type, prices in data['program'].items():
            for price, amount in prices.items():
                if type in count[tag]['count']:
                    if (price // 1_000) not in count[tag]['count'][type]:
                        alert(f"SHEET1: {tag} - Tên NPP: {data['name']} - {type}: {price} không hợp lệ",
                              code=tag, name=data['name'], customer_code="", customer_name="")
                        continue
                    count[tag]['count'][type][price // 1_000] += amount

    for tag, data in d.items():
        count2[tag]['name'] = data['name']
        for type, prices in data['program'].items():
            for price, amount in prices.items():
                if type == 'DHLM':
                    if price not in [50_000, 100_000]:
                        alert(f"SHEET2: {tag} - Tên NPP: {data['name']} - DHLM: {price} không hợp lệ",
                              code=tag, name=data['name'], customer_code="", customer_name="")
                        continue
                    count2[tag]['count'][type][50] += amount

    out_df = {
        'CODE NPP':['','',''], 'TÊN NPP':['','',''],
        'C':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ ĐẬU LINE','Đạt mức 420'],
        'D':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ ĐẬU LINE','Đạt mức 300'],
        'E':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ ĐẬU LINE','Đạt mức 120'],
        'F':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ 4 TẦNG','Đạt mức 420'],
        'G':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ 4 TẦNG','Đạt mức 300'],
        'H':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ 4 TẦNG','Đạt mức 120'],
        'I':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ 3 TẦNG','Đạt mức 260'],
        'J':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ 3 TẦNG','Đạt mức 180'],
        'K':['CHƯƠNG TRÌNH CHƯNG BÀY','KỆ 3 TẦNG','Đạt mức 80'],
        'L':['CHƯƠNG TRÌNH CHƯNG BÀY','WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG','Đạt mức 220'],
        'M':['CHƯƠNG TRÌNH CHƯNG BÀY','WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG','Đạt mức 160'],
        'N':['CHƯƠNG TRÌNH CHƯNG BÀY','WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG','Đạt mức 60'],
        'O':['CHƯƠNG TRÌNH CHƯNG BÀY','WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG','Đạt mức 170'],
        'P':['CHƯƠNG TRÌNH CHƯNG BÀY','WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG','Đạt mức 120'],
        'Q':['CHƯƠNG TRÌNH CHƯNG BÀY','WINDOW FRAME VÀ GIA VỊ CUỘC SỐNG','Đạt mức 50'],
        'R':['CHƯƠNG TRÌNH CHƯNG BÀY','NGON ĐẾN KHÁT KHAO','Đạt mức 90'],
        'S':['CHƯƠNG TRÌNH CHƯNG BÀY','RỖ + 2VĨ TREO','Đạt mức 40'],
        'T':['CHƯƠNG TRÌNH CHƯNG BÀY','RỖ DÀI HẠN','Đạt mức 20'],
        'U':['CHƯƠNG TRÌNH CHƯNG BÀY','RỖ DÀI HẠN','Đạt mức 40'],
        'V':['CHƯƠNG TRÌNH CHƯNG BÀY','KHAY GIA VỊ','Đạt mức 20'],
        'W':['CHƯƠNG TRÌNH CHƯNG BÀY','VĨ TREO DÀI HẠN','Đạt mức 20'],
        'X':['CHƯƠNG TRÌNH CHƯNG BÀY','VĨ TREO DÀI HẠN','Đạt mức 30'],
        'Y':['CHƯƠNG TRÌNH CHƯNG BÀY','VĨ TREO DÀI HẠN','Đạt mức 40'],
        'Z':['CHƯƠNG TRÌNH CHƯNG BÀY','XỐT LẨU THÁI & XỐT LẨU KIM CHI','Đạt mức 30'],
        'AA':['CHƯƠNG TRÌNH CHƯNG BÀY','TỔNG SỐ SUẤT TRẢ THƯỞNG','TỔNG SỐ SUẤT TRẢ THƯỞNG'],
        'AB':['CHƯƠNG TRÌNH CHƯNG BÀY','TỔNG TIỀN TRẢ THƯỞNG','TỔNG TIỀN TRẢ THƯỞNG']
    }

    for tag, data in count.items():
        out_df['CODE NPP'].append(tag)
        out_df['TÊN NPP'].append(data['name'])
        _sum = total_price = 0
        for type, prices in data['count'].items():
            if type == 'KDLINE':
                out_df['C'].append(prices[420]); out_df['D'].append(prices[300]); out_df['E'].append(prices[120])
            elif type == 'K4T':
                out_df['F'].append(prices[420]); out_df['G'].append(prices[300]); out_df['H'].append(prices[120])
            elif type == 'K3T':
                out_df['I'].append(prices[260]); out_df['J'].append(prices[180]); out_df['K'].append(prices[80])
            elif type == 'WF':
                out_df['L'].append(prices[220]); out_df['M'].append(prices[160]); out_df['N'].append(prices[60])
            elif type == 'GVCS':
                out_df['O'].append(prices[170]); out_df['P'].append(prices[120]); out_df['Q'].append(prices[50])
            elif type == 'NDKK':
                out_df['R'].append(prices[90])
            elif type == 'RO_2VI':
                out_df['S'].append(prices[40])
            elif type == '1RO':
                out_df['T'].append(prices[20])
            elif type == '2RO':
                out_df['U'].append(prices[40])
            elif type == 'KGV':
                out_df['V'].append(prices[20])
            elif type == '2VT':
                out_df['W'].append(prices[20])
            elif type == '3VT':
                out_df['X'].append(prices[30])
            elif type == '4VT':
                out_df['Y'].append(prices[40])
            elif type == 'LTLKC':
                out_df['Z'].append(prices[30])

            _sum += sum(prices.values())
            for price, amount in prices.items():
                total_price += price * amount

        out_df['AA'].append(_sum)
        out_df['AB'].append(total_price * 1_000)

    filename_df = dfs
    nmcd_money_list = sorted(filename_df.loc[filename_df['Mức đăng ký']=='NMCD', 'Số tiền đã trả thưởng'].dropna().unique())
    nmcd_money_list = [int(x) for x in nmcd_money_list]

    out_df2 = {'CODE NPP': [], 'TÊN NPP': [], 'DHLM 50': []}
    for val in nmcd_money_list:
        out_df2[f'NMCD {int(val/1000)}'] = []
    out_df2['TỔNG SỐ SUẤT'] = []; out_df2['TỔNG TIỀN'] = []

    npp_set = set(zip(filename_df['Mã NPP'], filename_df['Tên NPP']))
    for code, name in sorted(npp_set):
        out_df2['CODE NPP'].append(code); out_df2['TÊN NPP'].append(name)
        dhlm_rows = filename_df[(filename_df['Mã NPP']==code) & (filename_df['Tên NPP']==name) & (filename_df['Mức đăng ký']=='DHLM')]
        cnt_dhlm = 0
        for _, r in dhlm_rows.iterrows():
            w = r['Số tiền trả thưởng']
            ma_kh = r.get('Mã khách hàng',""); ten_kh = r.get('Tên khách hàng',"")
            if pd.isna(ma_kh): ma_kh = ""
            if pd.isna(ten_kh): ten_kh = ""
            so_suat = int(round(w/50000)) if not pd.isna(w) else 0
            cnt_dhlm += so_suat
            if so_suat not in [1,2] and so_suat>0:
                alert(f"DHLM số suất bất thường: Số tiền {w}, số suất = {so_suat} (khác 1,2)",
                      code=code, name=name, customer_code=ma_kh, customer_name=ten_kh)
        out_df2['DHLM 50'].append(cnt_dhlm)

        _sum = cnt_dhlm; _money = dhlm_rows['Số tiền trả thưởng'].sum()
        for val in nmcd_money_list:
            cnt = filename_df[(filename_df['Mã NPP']==code) & (filename_df['Tên NPP']==name)
                              & (filename_df['Mức đăng ký']=='NMCD') & (filename_df['Số tiền đã trả thưởng']==val)].shape[0]
            out_df2[f'NMCD {int(val/1000)}'].append(cnt)
            _sum += cnt; _money += cnt * val
        out_df2['TỔNG SỐ SUẤT'].append(_sum); out_df2['TỔNG TIỀN'].append(_money)

    sheet3 = {}
    for _, row in dfs.iterrows():
        code_npp = row['Mã NPP']; ten_npp = row['Tên NPP']; R = row['Mức đăng ký']
        S = row['Số suất đăng kí']; W = row['Số tiền trả thưởng']; X = row.get('Số tiền đã trả thưởng', W)
        ma_kh = row.get('Mã khách hàng', ""); ten_kh = row.get('Tên khách hàng', "")
        if pd.isna(ma_kh): ma_kh = ""
        if pd.isna(ten_kh): ten_kh = ""
        if not pd.isna(X) and W != X:
            alert(f"Số tiền trả thưởng không khớp: W={W}, X={X}",
                  code=code_npp, name=ten_npp, customer_code=ma_kh, customer_name=ten_kh)
            W = X
        if code_npp not in sheet3:
            # BỎ KHÓA 'STT' Ở ĐÂY (tránh trùng khi insert phía dưới)
            sheet3[code_npp] = {
                'CODE NPP': code_npp, 'NHÀ PHÂN PHỐI': ten_npp,
                'CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50': 0,
                'GIA VỊ GÓI 50': 0, 'GIA VỊ GÓI 80': 0,
                'SẢN PHẨM ĐÔNG LẠNH 50': 0, 'SẢN PHẨM ĐÔNG LẠNH 100': 0,
                'TỔNG SỐ SUẤT TRẢ THƯỞNG': 0, 'TỔNG TIỀN': 0
            }
        entry = sheet3[code_npp]
        if R == 'KOS_XXTG_BS':
            if S>0 and W//S==50_000: entry['CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50'] += S
            else: alert(f"Lỗi dòng KOS_XXTG_BS: S={S}, W={W}, W/S={W//S if S else 'NA'}",
                        code=code_npp, name=ten_npp, customer_code=ma_kh, customer_name=ten_kh)
        if str(R).strip().upper().startswith('GVI'):
            if S>0 and W//S==50_000: entry['GIA VỊ GÓI 50'] += S
            elif S>0 and W//S==80_000: entry['GIA VỊ GÓI 80'] += S
            else: alert(f"Lỗi dòng GIA VỊ GÓI: S={S}, W={W}, W/S={W//S if S else 'NA'}",
                        code=code_npp, name=ten_npp, customer_code=ma_kh, customer_name=ten_kh)
        if R in ['M1_POSTER','M2_DECAL']:
            if S>0 and W//S==50_000: entry['SẢN PHẨM ĐÔNG LẠNH 50'] += S
            elif S>0 and W//S==100_000: entry['SẢN PHẨM ĐÔNG LẠNH 100'] += S
            else: alert(f"Lỗi dòng ĐÔNG LẠNH: S={S}, W={W}, W/S={W//S if S else 'NA'}",
                        code=code_npp, name=ten_npp, customer_code=ma_kh, customer_name=ten_kh)

        entry['TỔNG SỐ SUẤT TRẢ THƯỞNG'] = (
            entry['CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50']
            + entry['GIA VỊ GÓI 50'] + entry['GIA VỊ GÓI 80']
            + entry['SẢN PHẨM ĐÔNG LẠNH 50'] + entry['SẢN PHẨM ĐÔNG LẠNH 100']
        )
        entry['TỔNG TIỀN'] = (
            entry['CÁ KOS + XÚC XÍCH THÁNH GIÓNG 50'] * 50_000
            + entry['GIA VỊ GÓI 50'] * 50_000
            + entry['GIA VỊ GÓI 80'] * 80_000
            + entry['SẢN PHẨM ĐÔNG LẠNH 50'] * 50_000
            + entry['SẢN PHẨM ĐÔNG LẠNH 100'] * 100_000
        )

    sheet3_df = pd.DataFrame(sheet3.values())
    sheet3_df.index += 1
    # Nếu vì lý do nào đó STT đã tồn tại, drop trước khi insert để tránh lỗi
    if 'STT' in sheet3_df.columns:
        sheet3_df = sheet3_df.drop(columns=['STT'])
    sheet3_df.insert(0, 'STT', sheet3_df.index)

    dfs_out = {'Sheet1': pandas.DataFrame(out_df),
               'Sheet2': pd.DataFrame(out_df2),
               'Sheet3': sheet3_df}

    print(f"Bắt đầu ghi file {output_file}...")
    with pandas.ExcelWriter(str(output_file), engine='xlsxwriter') as writer:
        for name, df in dfs_out.items():
            df.to_excel(writer, sheet_name=name, index=False)
    print(f"Đã xuất file {output_file} thành công!")

    if alert_list:
        pd.DataFrame(alert_list).to_excel(str(alert_file), index=False)
        print(f"Đã xuất file {alert_file}!")
    else:
        print("Không có cảnh báo nào.")

if __name__ == "__main__":
    run()
