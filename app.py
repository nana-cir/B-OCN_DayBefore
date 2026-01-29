import streamlit as st
import datetime
import jpholiday

# --- 1. 設定 ---
st.set_page_config(page_title="B-OCN申込み逆算ツール", layout="centered")

# --- 2. デザイン調整（最強版） ---
st.markdown("""
    <style>
    /* ヘッダー（上のバー・右上のアイコン・メニュー）を物理的に消す */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* フッター（下のMade with Streamlit）を物理的に消す */
    footer {
        display: none !important;
    }
    
    /* 右下のツールバーや開発者メニューも念のため消す */
    div[data-testid="stStatusWidget"] {
        display: none !important;
    }
    div[data-testid="stToolbar"] {
        display: none !important;
    }
    .stDeployButton {
        display: none !important;
    }
    
    /* スマホで見やすくするための余白調整（ヘッダーを消した分、上を詰める） */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* 結果カードのデザイン（ダークモード対応） */
    .result-card {
        background-color: #262730;
        border-left: 5px solid #ff4b4b;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .result-title {
        font-size: 1.2rem;
        color: #ffffff;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    .result-date {
        font-size: 2.5rem;
        color: #ff4b4b;
        font-weight: bold;
    }
    .sub-info {
        font-size: 1rem;
        color: #cccccc;
    }
    </style>
    """, unsafe_allow_html=True)
# --- 3. ロジック関数 ---

def get_business_day_delta(start_date, days, direction="forward"):
    current_date = start_date
    count = 0
    while count < days:
        if direction == "forward":
            current_date += datetime.timedelta(days=1)
        else:
            current_date -= datetime.timedelta(days=1)
        if current_date.weekday() >= 5 or jpholiday.is_holiday(current_date):
            continue
        count += 1
    return current_date

# --- 4. アプリ本体 ---

st.title("🗓️ B-OCN申込み逆算ツール")

with st.container():
    # 1. 光回線
    line_type = st.selectbox("光回線の種類", ["フレッツ光1ギガ", "フレッツ光10ギガ", "ドコモ光1ギガ", "ドコモ光10ギガ"])
    
    # 2. 契約状況
    contract_status = st.selectbox("契約状況", ["新規および転用", "既存契約あり", "申込済み（工事日確定、工事前）", "申込済み（工事日未確定）"])
    
    # 3. CAF番号
    caf_status = st.radio("CAF番号確認", ["CAF番号あり", "CAF番号不明"], horizontal=True)
    if caf_status == "CAF番号不明":
        st.warning("⚠️ 申込にはCAF番号が必要です。")

    # 4. 工事希望日
    target_construction_date = st.date_input(
        "光工事希望日 (または仮日)",
        min_value=datetime.date.today(),
        value=datetime.date.today() + datetime.timedelta(days=30)
    )

    # 5. ルーター選択
    router_type = st.selectbox("ルーター手配", [
        "レンタルルーター02（オンサイト設置）",
        "レンタルルーター02（お客様設置）",
        "IPoE対応ルーター自営端末"
    ])

    # 6. 申込登録方法
    entry_method = st.selectbox("申込登録方法", [
        "自身でWebエントリー",
        "RM経由"
    ])

# --- 5. 計算実行とエラー判定 ---
if st.button("逆算を実行する", type="primary", use_container_width=True):
    
    # ▼▼▼ エラー判定ロジック（ここを追加しました） ▼▼▼
    # 「10ギガ」という文字が含まれていて、かつ「レンタルルーター02」が選ばれている場合
    if "10ギガ" in line_type and "レンタルルーター02" in router_type:
        st.error("⚠️ 10ギガでは「レンタルルーター02」は選択できません。自営端末を選択してください。")
        st.stop() # ここで処理を強制ストップします
    # ▲▲▲ ここまで ▲▲▲

    # リードタイム定義
    lead_time_router = 0
    if "オンサイト" in router_type:
        lead_time_router = 14
    elif "お客様設置" in router_type:
        lead_time_router = 10
    else:
        lead_time_router = 4
        
    lead_time_entry = 1 if "Webエントリー" in entry_method else 3
    
    total_lead_time = lead_time_router + lead_time_entry
    
    # 計算
    limit_date = get_business_day_delta(target_construction_date, total_lead_time, direction="backward")
    start_date = get_business_day_delta(target_construction_date, 2, direction="forward")
    
    # 結果表示（ダークモード対応CSSに微調整済み）
    st.markdown(f"""
    <div class="result-card">
        <div class="result-title">📢 この日までに申込書を受領してください</div>
        <div class="result-date">{limit_date.month}月{limit_date.day}日 ({limit_date.strftime('%a')})</div>
        <hr style="border-top: 1px solid #555;">
        <div class="sub-info">
            <b>工事希望日：</b> {target_construction_date.month}月{target_construction_date.day}日<br>
            <b>最短利用開始：</b> {start_date.month}月{start_date.day}日<br>
            <small>※土日祝を除いた {total_lead_time} 営業日前で計算</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if limit_date < datetime.date.today():
        st.error("🚨 注意：算出された申込日が過ぎています。")
