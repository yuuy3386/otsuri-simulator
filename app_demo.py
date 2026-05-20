"""
app_demo.py — ポートフォリオ公開用デモ版
  - デモ用商品データ（実在商品を避けたサンプル）を使用
  - 固定セット価格・自動適用ロジックを含む
  - 実運用の app.py・GAS・商品データには一切影響しない

実行方法:
  streamlit run app_demo.py

設定切り替え（ローカル確認用）:
  公開デモ  → from config_demo import DEMO_CONFIG as DEMO_CONFIG（デフォルト）
  実運用確認 → from config_real import REAL_CONFIG as DEMO_CONFIG に変更
"""

import streamlit as st
from config_demo import DEMO_CONFIG

# ─────────────────────────────────────────
#  設定読み込み
# ─────────────────────────────────────────
MENU      = DEMO_CONFIG["menu"]
SETS      = DEMO_CONFIG["sets"]
APP_TITLE = DEMO_CONFIG["title"]

st.set_page_config(page_title="キッチンカー管理ツール（デモ）", layout="wide")

# ─────────────────────────────────────────
#  初期化
# ─────────────────────────────────────────
if "cart" not in st.session_state:
    st.session_state.cart = {}   # {商品名: 個数}

# ─────────────────────────────────────────
#  タイトル
# ─────────────────────────────────────────
st.title(APP_TITLE)
st.caption("商品タップ → セット自動適用 → 復唱テキスト生成 → 合計表示")
st.info("DEMO — サンプルデータを使用しています", icon="ℹ️")

# ─────────────────────────────────────────
#  セット自動計算（純関数）
# ─────────────────────────────────────────
def compute_sets(cart: dict) -> dict:
    """
    カートからセットを自動適用し、適用済みセット・残り単品・割引額を返す。
    セットは discount 降順（大きい割引を優先）で適用。
    """
    pool = dict(cart)   # 消費量を操作するコピー
    applied = []

    # discount 降順でソート（None は 0 扱い）
    sorted_sets = sorted(
        SETS.items(),
        key=lambda kv: kv[1].get("discount", 0),
        reverse=True,
    )

    for set_name, cfg in sorted_sets:
        items = cfg["items"]
        set_price = cfg.get("set_price")
        discount  = cfg.get("discount", 0)
        if set_price is None:
            continue  # 固定価格なしのセットはスキップ

        # items の必要数をカウント
        needed = {}
        for item in items:
            needed[item] = needed.get(item, 0) + 1

        # プールから消費できるか確認
        if all(pool.get(item, 0) >= qty for item, qty in needed.items()):
            consumed = []
            for item, qty in needed.items():
                pool[item] -= qty
                if pool[item] == 0:
                    del pool[item]
                consumed.append(f"{item}" + (f"×{qty}" if qty > 1 else ""))
            applied.append({
                "name":      set_name,
                "set_price": set_price,
                "discount":  discount,
                "contents":  "・".join(consumed),
            })

    remaining = {k: v for k, v in pool.items() if v > 0}
    total_discount = sum(s["discount"] for s in applied)
    set_total  = sum(s["set_price"] for s in applied)
    rem_total  = sum(MENU.get(k, 0) * v for k, v in remaining.items())
    final_total = set_total + rem_total

    return {
        "applied":        applied,
        "remaining":      remaining,
        "total_discount": total_discount,
        "set_total":      set_total,
        "rem_total":      rem_total,
        "final_total":    final_total,
    }

# ─────────────────────────────────────────
#  レイアウト: 左列=入力, 右列=注文内容
# ─────────────────────────────────────────
col_input, col_order = st.columns([1, 1], gap="large")

with col_input:
    # ── 商品ボタン ──
    st.subheader("商品を選ぶ")
    items = list(MENU.items())
    btn_cols = st.columns(3)
    for i, (name, price) in enumerate(items):
        with btn_cols[i % 3]:
            if st.button(f"{name}\n¥{price:,}", key=f"item_{name}", use_container_width=True):
                st.session_state.cart[name] = st.session_state.cart.get(name, 0) + 1
                st.rerun()

    # ── セット情報 ──
    st.subheader("固定セット（自動適用）")
    for set_name, cfg in SETS.items():
        if cfg.get("set_price") is None:
            continue
        contents = []
        needed = {}
        for item in cfg["items"]:
            needed[item] = needed.get(item, 0) + 1
        for item, qty in needed.items():
            contents.append(item + (f"×{qty}" if qty > 1 else ""))
        disc = cfg.get("discount", 0)
        st.caption(
            f"**{set_name}** ¥{cfg['set_price']:,}（−¥{disc}）　"
            + "・".join(contents)
        )

    # ── リセット ──
    st.markdown("---")
    if st.button("🔄 注文をリセット", use_container_width=True):
        st.session_state.cart = {}
        st.rerun()

with col_order:
    st.subheader("注文内容")

    cart = st.session_state.cart
    if not cart or all(v == 0 for v in cart.values()):
        st.write("商品をタップして追加してください")
    else:
        result = compute_sets(cart)

        # ── 適用済みセット ──
        if result["applied"]:
            st.markdown("**✅ 適用済みセット**")
            for s in result["applied"]:
                st.success(
                    f"**{s['name']}** ×1　¥{s['set_price']:,}\n\n"
                    f"{s['contents']}　−¥{s['discount']} 割引適用中"
                )

        # ── 残り単品 ──
        if result["remaining"]:
            st.markdown("**残り単品**")
            for name, qty in result["remaining"].items():
                price = MENU.get(name, 0)
                st.write(f"　{name} ×{qty}　¥{price * qty:,}")

        # ── 合計 ──
        st.markdown("---")
        if result["total_discount"] > 0:
            st.write(f"合計割引　**−¥{result['total_discount']:,}**")
        st.markdown(f"### 合計　¥{result['final_total']:,}")

        # ── 復唱補助 ──
        st.markdown("---")
        st.markdown("**復唱**")
        parts = []
        for s in result["applied"]:
            parts.append(f"{s['name']}1つ")
        if result["remaining"]:
            rem_parts = []
            for name, qty in result["remaining"].items():
                rem_parts.append(name + (f"{qty}個" if qty > 1 else "1つ"))
            if result["applied"]:
                parts.append("残り" + "、".join(rem_parts))
            else:
                parts.extend(rem_parts)
        parts.append(f"合計{result['final_total']:,}円です")
        recite_text = "、".join(parts) + "。"

        st.info(recite_text)

        # ── お会計 ──
        st.markdown("---")
        st.subheader("お会計")
        mode = st.radio("モード", ["自動計算", "練習モード（答え合わせ）"], horizontal=True)
        received = st.number_input("お預かり金額 (円)", min_value=0, step=10, value=0)
        change = received - result["final_total"]

        if mode == "自動計算":
            if received == 0:
                st.write("お預かり金額を入力してください")
            elif change < 0:
                st.error(f"不足　{abs(change):,}円")
            else:
                st.success(f"お釣り　**¥{change:,}**")
        else:
            user_change = st.number_input("お釣りを入力 (円)", min_value=0, step=10)
            if st.button("答え合わせ", use_container_width=True):
                if received == 0:
                    st.warning("お預かり金額を入力してください")
                elif change < 0:
                    st.error(f"金額が不足しています（{abs(change):,}円）")
                elif user_change == change:
                    st.success("正解！")
                else:
                    st.error(f"不正解：正しくは ¥{change:,}")
