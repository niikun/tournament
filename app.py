import streamlit as st
import pandas as pd
import random
import uuid
import os
from weasyprint import HTML

def create_bracket(teams):
    """
    最大8チームを想定。
    チーム数が2,4,8以外の場合はBYEを入れて2のべき乗に合わせます。
    戻り値: rounds_list
      例) [
        [("A","B"),("C","D"),("E","F"),("G","BYE")],  # 1回戦
        [("勝者1","勝者2"),("勝者3","勝者4")],          # 準決勝
        [("勝者(準決1)","勝者(準決2)")]               # 決勝
      ]
    """
    # 2,4,8以上であれば対応
    size = len(teams)
    target_sizes = [2,4,8,16,32]
    bracket_size = min([s for s in target_sizes if s >= size], default=8)
    while len(teams) < bracket_size:
        teams.append("BYE")

    # 1回戦のマッチアップ
    random.shuffle(teams)
    round1 = [(teams[i], teams[i+1]) for i in range(0, bracket_size, 2)]

    # ラウンドを順次生成（シングルエリミネーション）
    rounds = [round1]
    current_matches = round1
    while len(current_matches) > 1:
        next_matches = []
        for i in range(0, len(current_matches), 2):
            # 2試合分の「勝者同士」で次の試合が行われる
            match1 = current_matches[i]
            match2 = current_matches[i+1] if i+1 < len(current_matches) else ("BYE","BYE")
            next_matches.append((f"WIN({match1[0]} vs {match1[1]})", f"WIN({match2[0]} vs {match2[1]})"))
        rounds.append(next_matches)
        current_matches = next_matches

    return rounds

def bracket_html(rounds):
    """
    rounds: create_bracketで生成されたラウンド情報
    例:
      rounds[0] -> 1回戦 (試合数=チーム数/2)
      rounds[1] -> 準決勝
      rounds[2] -> 決勝
    """
    # ラウンド名（最大で 1回戦, 準決勝, 決勝 くらい）
    # 必要に応じて拡張 1回戦→2回戦→3回戦 等
    round_names = ["1回戦","準決勝","決勝","準々決勝","ベスト8","ベスト16"]
    # ラウンド数に合わせて逆順に並ばないよう適宜調整する
    round_count = len(rounds)
    # 例: round_count=3なら ["1回戦","準決勝","決勝"]
    #    round_count=2なら ["1回戦","決勝"]
    # ※多い場合は round_names を拡張or自動生成
    use_names = round_names[:round_count]

    use_names.reverse()  # 後ろが1回戦、手前が決勝の並びにする
    rounds.reverse()     # roundsも逆にして [決勝][準決勝][1回戦] の順で表示

    # CSSを組み込んだHTMLを作成（線を描くにはpositionなど少し工夫）
    html = f"""
<html>
<head>
<meta charset='utf-8'/>
<style>
  body {{
    font-family: sans-serif;
    text-align: center;
  }}
  h1 {{
    margin: 10px 0;
  }}
  .trophy {{
    font-size: 40px;
    margin: 10px;
  }}
  .bracket {{
    display: flex;
    justify-content: center;
    align-items: flex-start;
    margin-top: 20px;
  }}
  .round {{
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 0 20px;
    position: relative;
  }}
  .round-title {{
    font-weight: bold;
    margin-bottom: 10px;
  }}
  .match-container {{
    display: flex;
    flex-direction: column;
    gap: 10px;
    position: relative;
  }}
  /* マッチブロック */
  .match {{
    background: #cfead9;
    padding: 10px 15px;
    border-radius: 6px;
    border: 1px solid #aaa;
    min-width: 140px;
    text-align: center;
  }}
  .spacer {{
    height: 40px; /* 試合間の線をつなぐための余白 */
  }}

  /* 線を描くための例示。より複雑にやるなら各マッチをposition:absoluteで配置しラインを引く方法もあり */
  /* ここでは簡易表現。より本格的にはCanvas/SVGを使うか、positionで手動配置など要カスタマイズ */
</style>
</head>
<body>
<div class="trophy">🏆</div>
<h1>トーナメント表</h1>
<div class="bracket">
"""
    for r_idx, round_matches in enumerate(rounds):
        html += f'<div class="round"><div class="round-title">{use_names[r_idx]}</div>'
        html += '<div class="match-container">'
        for match in round_matches:
            t1, t2 = match
            # 簡易的に "WIN(...)" は表示を縮める
            team1 = t1.replace("WIN(","").replace(")","").replace(" vs "," / ")
            team2 = t2.replace("WIN(","").replace(")","").replace(" vs "," / ")
            html += f'<div class="match">{team1}<br>vs<br>{team2}</div>'
            # 下に余白を挟む
            html += '<div class="spacer"></div>'
        html += '</div></div>'
    html += "</div></body></html>"
    return html

def html_to_pdf(html_code, pdf_path):
    HTML(string=html_code).write_pdf(pdf_path)

#---- Streamlit アプリ ----#
from weasyprint import HTML

def main():
    st.set_page_config(page_title="トーナメント表", layout="wide")
    st.title("日本式 横方向トーナメント表 (HTML+CSS)")

    uploaded_file = st.file_uploader("CSVファイルをアップロード（name列が必要）", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "name" not in df.columns:
            st.error("CSVに 'name' 列が必要です。")
            return
        teams = df["name"].dropna().tolist()
        if len(teams) < 2:
            st.warning("2チーム以上が必要です。")
            return

        st.write(f"{len(teams)} チームを読み込みました。")
        # トーナメント作成
        bracket_data = create_bracket(teams)
        # HTML生成
        html_code = bracket_html(bracket_data)
        # 表示
        st.components.v1.html(html_code, height=800, scrolling=True)

        # PDF出力
        pdf_path = f"tournament_{uuid.uuid4().hex}.pdf"
        html_to_pdf(html_code, pdf_path)
        with open(pdf_path, "rb") as f:
            st.download_button("PDFダウンロード", f, file_name="tournament.pdf")
        os.remove(pdf_path)

if __name__ == "__main__":
    main()
