import streamlit as st

st.set_page_config(page_title="おつりシミュレーション", layout="wide")

st.title("キッチンカー向け｜お釣り計算＆セット提案ツール")
st.caption("注文内容から最適なセット組み合わせと合計金額を自動計算します")

# -------------------------
# 商品データ
# -------------------------
menu = {
    "ビーフ": 230,
    "メンチ": 380,
    "牛すじ": 300,
    "和風だし": 180,
    "明太クリーミー": 300,
    "チーズ": 300,
    "かにクリーム": 300,
    "かぼちゃ": 270,
    "常総牛": 630,
}

set_items = {
    "3点セット": ["ビーフ", "メンチ", "牛すじ"],
    "4点セット": ["ビーフ", "メンチ", "牛すじ", "明太クリーミー"],
    "お得セット": ["ビーフ", "ビーフ", "ビーフ", "メンチ", "メンチ"],
    "お土産セット": ["ビーフ", "和風だし", "常総牛"],
}

# -------------------------
# 初期化
# -------------------------
if "cart" not in st.session_state:
    st.session_state.cart = {}

# -------------------------
# 商品選択（2列 + 押しやすい）
# -------------------------
st.write("商品を選択してください（複数選択可）")
st.subheader("商品を選択")

cols = st.columns(2)
for i, (name, price) in enumerate(menu.items()):
    with cols[i % 2]:
        if st.button(f"{name} {price}円", key=name, use_container_width=True):
            st.session_state.cart[name] = st.session_state.cart.get(name, 0) + 1

# -------------------------
# セットメニュー（2列）
# -------------------------
st.subheader("セットメニュー")

cols = st.columns(2)
for i, set_name in enumerate(set_items.keys()):
    with cols[i % 2]:
        if st.button(set_name, key=set_name, use_container_width=True):
            for item in set_items[set_name]:
                st.session_state.cart[item] = st.session_state.cart.get(item, 0) + 1

# -------------------------
# 注文内容
# -------------------------
st.subheader("注文内容")

total = 0
order_counts = st.session_state.cart.copy()

if not order_counts or all(qty == 0 for qty in order_counts.values()):
    st.write("商品を選んでください")
else:
    for item, qty in order_counts.items():
        if qty > 0:
            price = menu[item] * qty
            total += price
            st.write(f"{item} ×{qty}：{price}円")

st.markdown("---")
st.subheader(f"合計：{total}円")

# -------------------------
# お会計（下に配置）
# -------------------------
st.subheader("お会計")

mode = st.radio("モード選択", ["練習モード", "自動計算モード"])

money = st.number_input("預かり金額", min_value=0, step=1)
change = money - total

st.markdown("### おつり")

if mode == "自動計算モード":
    if money == 0:
        st.write("未入力")
    elif change < 0:
        st.error(f"{abs(change)}円 不足")
    else:
        st.success(f"{change}円")
else:
    user_change = st.number_input("おつりを入力", min_value=0, step=1)

    if st.button("答え合わせ", use_container_width=True):
        if money == 0:
            st.warning("預かり金額を入力してください")
        elif change < 0:
            st.error("金額が不足しています")
        elif user_change == change:
            st.success("正解！")
        else:
            st.error(f"不正解：正しくは {change}円")

# -------------------------
# リセット
# -------------------------
st.markdown("---")
if st.button("リセット", use_container_width=True):
    st.session_state.cart = {}
    st.rerun()