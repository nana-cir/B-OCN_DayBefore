import streamlit as st
import datetime
import jpholiday

# --- 設定・デザイン ---
st.set_page_config(page_title="B-OCN申込み逆算ツール", layout="centered")

# カスタムCSS（スマホ見やすさ重視＆標準アラート回避のスタイル）
st.markdown("""
    <style>
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

# --- ロジック関数 ---

def get_business_day_delta(start_date, days, direction="forward"):
    """
    営業日ベースで日付を計算する関数
    direction="forward": 未来へ (開始日 + days)
    direction="backward": 過去へ (開始日 - days)
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

# --- アプリ本体 ---

st.title("🗓️ B-OCN申込み逆算ツール")
st.caption("工事希望日から申込期限を逆算します")

# 入力フォーム（レスポンシブ対応のためst.columnsは控えめに、縦並び基本）
with st.container():
    # 1. 光回線・契約状況
    line_type = st.selectbox("光回線の種類", ["フレッツ光1ギガ", "フレッツ光10ギガ", "ドコモ光1ギガ", "ドコモ光10ギガ"])
    contract_status = st.selectbox("契約状況", ["新規および転用", "既存契約あり", "申込済み（工事日確定、工事前）", "申込済み（工事日未確定）"])
    
    # CAF番号チェック (ロジックへの影響がない場合はバリデーション用)
    caf_status = st.radio("CAF番号確認", ["CAF番号あり", "CAF番号不明"], horizontal=True)
    if caf_status == "CAF番号不明":
        st.warning("⚠️ 申込にはCAF番号が必要です。確認フローを追加してください。")

    # 2. 工事希望日
    target_construction_date = st.date_input(
        "光工事希望日 (または仮日)",
        min_value=datetime.date.today(),
        value=datetime.date.today() + datetime.timedelta(days=30)
    )

    # 3. ルーター選択
    router_type = st.selectbox("ルーター手配", [
        "レンタルルーター02（オンサイト設置）", # 14営業日
        "レンタルルーター02（お客様設置）",   # 10営業日
        "IPoE対応ルーター自営端末"          # 4営業日
    ])

    # 4. 申込登録方法
    entry_method = st.selectbox("申込登録方法", [
        "自身でWebエントリー", # 1営業日
        "RM経由"             # 3営業日
    ])

# --- 計算実行 ---
if st.button("逆算を実行する", type="primary", use_container_width=True):
    
    # リードタイム定義（営業日）
    lead_time_router = 0
    if "オンサイト" in router_type:
        lead_time_router = 14
    elif "お客様設置" in router_type:
        lead_time_router = 10
    else:
        lead_time_router = 4
        
    lead_time_entry = 1 if "Webエントリー" in entry_method else 3
    
    # 逆算ロジック： 工事日 - (ルーターリードタイム + 登録リードタイム)
    # ※直列加算として計算（登録処理後にルーター手配と仮定）
    total_lead_time = lead_time_router + lead_time_entry
    
    # 申込リミット日の計算（逆算）
    limit_date = get_business_day_delta(target_construction_date, total_lead_time, direction="backward")
    
    # 最短利用開始日の計算（順算）：工事日 + 2営業日
    start_date = get_business_day_delta(target_construction_date, 2, direction="forward")
    
    # --- 結果表示（カスタムモーダル風デザイン） ---
    # ブラウザのアラートではなく、ページ内に強調表示
    
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
    
    # 警告ロジック（もし計算結果が今日より過去の場合）
    if limit_date < datetime.date.today():
        st.error("🚨 注意：算出された申込日が過ぎています。工事希望日を後ろ倒しする必要があります。")
