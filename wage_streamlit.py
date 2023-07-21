import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px

# タイトルの設定
st.title('日本の賃金データのダッシュボード')

# ================================================================================
# ダッシュボード作成に必要なCSVファイルの読み込み

df_jp_ind = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_全国_全産業.csv', encoding='shift_jis')
df_jp_category = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_全国_大分類.csv', encoding='shift_jis')
df_pref_ind = pd.read_csv('./csv_data/雇用_医療福祉_一人当たり賃金_都道府県_全産業.csv', encoding='shift_jis')

# ================================================================================
# 2019年：一人当たり平均賃金のヒートマップの作成

#ヘッダーの設定
st.header('■2019年：一人当たり平均賃金のヒートマップ')

# 都道府県の県庁所在地の緯度経度のCSVファイルの読み込み
jp_lat_lon = pd.read_csv('./pref_lat_lon.csv')
# pref_lat_lon.csvファイルの都道府県名が記された列の見出しの変更
jp_lat_lon = jp_lat_lon.rename(columns={'pref_name':'都道府県名'})

# データの読み込み
df_pref_map = df_pref_ind[(df_pref_ind['年齢'] == '年齢計') & (df_pref_ind['集計年'] == 2019) ]
df_pref_map = pd.merge(df_pref_map, jp_lat_lon, on='都道府県名')

# 一人当たり賃金を最小値0, 最大値1となるように正規化
df_pref_map['一人当たり賃金（相対値）'] = ((df_pref_map['一人当たり賃金（万円）']-df_pref_map['一人当たり賃金（万円）'].min())/(df_pref_map['一人当たり賃金（万円）'].max()-df_pref_map['一人当たり賃金（万円）'].min()))

#pydeckを用いてヒートマップを表示

#1 Viewの設定
view = pdk.ViewState(
    latitude=35.689185,#東京の緯度
    longitude=139.691648,#東京の経度
    pitch=4,
    zoom=40.5
)

#2 Layerの設定
layer = pdk.Layer(
    'HeatmapLayer',
    data=df_pref_map,
    oppacity = 0.4, #透明度
    get_position = ['lon', 'lat'],
    threshold = 0.3, #閾値
    get_weight = '一人当たり賃金（相対値）' #ヒートマップ表示したいデータ列
)

#3 Deckの設定
layer_map = pdk.Deck(
    layers=layer,
    initial_view_state=view
)

#4 streamlitに設定したヒートマップを表示
st.pydeck_chart(layer_map)


# チェックボックスの設定
# チェックがついた場合にヒートマップの元であるデータフレームを表示
show_df = st.checkbox('Show DataFrame')
if show_df == True:
    st.write(df_pref_map)

# ================================================================================
# 集計年別の一人当たり平均賃金の推移を表すグラフの作成

#ヘッダーの設定
st.header('■集計年別の一人当たり賃金（万円）の推移')

# 全国データの読み込みと列名の変更
df_ts_mean = df_jp_ind[(df_jp_ind['年齢'] == '年齢計')]
df_ts_mean = df_ts_mean.rename(columns={'一人当たり賃金（万円）':'全国_一人当たり賃金（万円）'})

# 都道府県別データの読み込み
df_pref_mean = df_pref_ind[(df_pref_ind['年齢'] == '年齢計')]

# 都道府県を選択できるセレクトボックスの作成
pref_list = df_pref_mean['都道府県名'].unique()
option_pref = st.selectbox('都道府県', (pref_list))

df_pref_mean = df_pref_mean[(df_pref_mean['都道府県名'] == option_pref)]

# 全国データと都道府県別データの結合
df_mean_line = pd.merge(df_ts_mean, df_pref_mean, on='集計年')

# 結合したデータフレームから必要なデータ(列)を抽出
df_mean_line = df_mean_line[['集計年', '全国_一人当たり賃金（万円）', '一人当たり賃金（万円）']]

# インデックスを集計年に変更
df_mean_line = df_mean_line.set_index('集計年')

# streamlitで折れ線グラフを表示
st.line_chart(df_mean_line)

# ================================================================================
# 年齢階級別の全国人当たり平均賃金を表すバブルチャートの作成

#ヘッダーの設定
st.header('■年齢階級別の全国一人当たり賃金（万円）')

# データの読み込み
# 年齢計の行以外のデータを読み込む
df_mean_bubble = df_jp_ind[(df_jp_ind['年齢'] != '年齢計')]

# バブルチャートの設定
fig = px.scatter(
    df_mean_bubble,
    x='一人当たり賃金（万円）',
    y='年間賞与その他特別給与額（万円）',
    range_x=[150, 700],
    range_y=[0, 150],
    size='所定内給与額（万円）',
    size_max=38,
    color='年齢',
    animation_frame='集計年',
    animation_group='年齢'
)

# streamlitでバブルチャートを表示
st.plotly_chart(fig)


# ================================================================================
# 産業別の平均賃金を表す棒グラフの作成

#ヘッダーの設定
st.header('■産業別の賃金推移')

# 集計年を選択するセレクトボックスの作成
year_list = df_jp_category['集計年'].unique()
option_year = st.selectbox('集計年', (year_list))

# 賃金の種類を選択するセレクトボックスの作成
wage_list = ['一人当たり賃金（万円）', '所定内給与額（万円）', '年間賞与その他特別給与額（万円）']
option_wage = st.selectbox('賃金の種類', (wage_list))

# 選択した集計年のデータを抽出
df_mean_categ = df_jp_category[(df_jp_category['集計年'] == option_year)]

max_x = df_mean_categ[option_wage].max() + 50 # +50のマージがあることでグラフが見やすくなる

# 棒グラフの設定
fig = px.bar(
    df_mean_categ,
    x=option_wage,
    y='産業大分類名',
    color='産業大分類名',
    animation_frame='年齢',
    range_x=[0, max_x],
    orientation='h',
    width=800,
    height=500
)

# streamlitで棒グラフを表示
st.plotly_chart(fig)

# ================================================================================
# 出典元の記載

st.text('出典：RESAS（地域経済分析システム）')
st.text('本結果はRESAS（地域経済分析システム）を加工して作成')
