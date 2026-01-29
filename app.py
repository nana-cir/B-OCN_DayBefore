import streamlit as st
import datetime
import jpholiday

# --- 1. 設定（これは必ず一番最初に書く！） ---
st.set_page_config(page_title="B-OCN申込み逆算ツール", layout="centered")

# --- 2. メニューや余計な表示を消すCSS ---
st.markdown("""
    <style>
    /* 右上のメニューボタン（三点リーダー）を消す */
    #MainMenu {visibility: hidden;}
    /* ヘッダーの装飾を消す */
    header {visibility: hidden;}
    /* 下のMade with Streamlitを消す */
    footer {visibility: hidden;}
    
    /* 結果カードのデザイン */
    .result-card {
        background-color: #f0f2f6;
        border-left: 5px solid #ff4b4b;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .result-title {
        font-size: 1.2rem;
        color: #31333F;
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
        color: #555;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ロジック関数 ---

def get_business_day_delta(start_date, days, direction="forward"):
    """
    営業日ベースで日付を計算する関数
    """
    current_date = start_date
    count = 0
    
    while count < days:
        if direction == "forward":
            current_date += datetime.timedelta(days=1)
        else:
            current_date -= datetime.timedelta(days=1)
            
        # 土日(5,6)と祝日判定
        if current_date.weekday() >= 5 or jpholiday.is_holiday(current_date):
            continue
        count += 1
        
    return current_date

# --- 4. アプリ本体 ---

st.title("🗓️ B-OCN申込み逆算ツール")
# st.caption("工事希望日から申込期限を逆算します") # スッキリさせるためコメントアウト

with st.container():
    # 1. 光回線・契約状況
    line_type = st.selectbox("光回線の種類", ["フレッツ光1ギガ", "フレッツ光10ギガ", "ドコモ光1ギガ", "ドコモ光10ギガ"])
    contract_status = st.selectbox("契約状況", ["新規および転用", "既存契約あり", "申込済み（工事日確定、工事前）", "申込済み（工事日未確定）"])
    
    # CAF番号チェック
    caf_status = st.radio("CAF番号確認", ["CAF番号あり", "CAF番号不明"], horizontal=True)
    if caf_status == "CAF番号不明":
        st.warning("⚠️ 申込にはCAF番号が必要です。")

    # 2. 工事希望日
    target_construction_date = st.date_input(
        "光工事希望日 (または仮日)",
        min_value=datetime.date.today(),
        value=datetime.date.today() + datetime.timedelta(days=30)
    )

    # 3. ルーター選択
    router_type = st.selectbox("ルーター手配", [
        "レンタルルーター02（オンサイト設置）",
        "レンタルルーター02（お客様設置）",
        "IPoE対応ルーター自営端末"
    ])

    # 4. 申込登録方法
    entry_method = st.selectbox("申込登録方法", [
        "自身でWebエントリー",
        "RM経由"
    ])

# --- 5. 計算実行 ---
if st.button("逆算を実行する", type="primary", use_container_width=True):
    
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
    
    # 結果表示
    st.markdown(f"""
    <div class="result-card">
        <div class="result-title">📢 この日までに申込書を受領してください</div>
        <div class="result-date">{limit_date.month}月{limit_date.day}日 ({limit_date.strftime('%a')})</div>
        <hr>
        <div class="sub-info">
            <b>工事希望日：</b> {target_construction_date.month}月{target_construction_date.day}日<br>
            <b>最短利用開始：</b> {start_date.month}月{start_date.day}日<br>
            <small>※土日祝を除いた {total_lead_time} 営業日前で計算</small>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if limit_date < datetime.date.today():
        st.error("🚨 注意：算出された申込日が過ぎています。")
