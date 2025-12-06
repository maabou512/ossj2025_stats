import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

# --- ターゲット年を2025年に設定 ---
TARGET_YEAR = 2025 

# HTMLファイルを読み込む
with open('./input.html', 'r', encoding='utf-8') as file:
    html_content = file.read()

# BeautifulSoupでHTMLを解析
soup = BeautifulSoup(html_content, 'html.parser')

# データを格納するリスト
data_list = []
current_date = None
current_date_str = None

# ベースURL
base_url = "https://events.linuxfoundation.org"

# --- 企業/組織名を抽出する関数 (V10ロジック: 役割除去と企業名カンマ保持の両立) ---
def extract_companies_from_title(title_text):
    companies = set()
    
    # 1. セッションタイトルと詳細情報を分離
    parts = title_text.split(' - ', 1)
    if len(parts) < 2:
        return sorted(list(companies))
    
    info_segment = parts[1].strip()
    
    # 2. 情報を ';' で分割 (独立した発表ペアの区切り)
    primary_chunks = [c.strip() for c in info_segment.split(';') if c.strip()]
    
    for chunk in primary_chunks:
        
        potential_company_segment = ""
        
        # 3. 【修正ロジック】最初のカンマのみで分割し、残りの全てを企業名候補とする
        parts = chunk.split(',', 1)
        
        if len(parts) == 2:
            # 最初のカンマ以降の全て（企業名/役割）を採用。これが Co., Ltd. のカンマを保持し、役割を分離する。
            potential_company_segment = parts[1].strip()
            
        elif len(parts) == 1:
            # カンマがない場合、そのまま採用
            potential_company_segment = parts[0].strip()
        else: 
            continue
            
        # 4. セグメント内の処理
        current_candidate = potential_company_segment
        
        # 4-a. 括弧内の組織名があれば取り出す (例: VMware (Broadcom))
        match_paren = re.search(r'\(([^)]+?)\)', current_candidate)
        if match_paren:
            companies.add(match_paren.group(1).strip())
            current_candidate = re.sub(r'\s*\([^)]+?\)\s*', '', current_candidate).strip()

        # 4-b. 共同発表者の区切り ' & ' が残っている場合、最後の部分を会社名とする
        # 例: "Hitachi, Ltd. & Microsoft" の場合、Microsoftが残る
        if ' & ' in current_candidate:
            current_candidate = current_candidate.split(' & ')[-1].strip()

        # 5. 会社名として妥当性があるか (大文字から始まるなど)
        if current_candidate and current_candidate[0].isupper():
            companies.add(current_candidate)
            
    return sorted(list(companies))


# tr要素をループする
for tr in soup.find_all('tr'):
    # 日付情報を含むtr (class="bar")
    if tr.get('class') == ['bar']:
        date_span = tr.find('span')
        if date_span:
            current_date = date_span.get_text(strip=True)
            
            # 日付の変換ロジックを2025年対応に変更
            if current_date:
                try:
                    date_part = current_date.split('•')[0].strip()
                    date_obj = datetime.strptime(f"{date_part} {TARGET_YEAR}", "%B %d %Y")
                    current_date_str = date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    current_date_str = None

    # データを含むtr
    elif current_date_str: 
        td_data = {}
        td_data['date'] = current_date
        date_str = current_date_str
        
        td_data['speaker'] = [] 
        td_data['company'] = [] 
        
        for td in tr.find_all('td'):
            class_name = td.get('class')[0] if td.get('class') else None
            
            if class_name == 'time':
                time_range_text = td.find('span').get_text(strip=True)
                time_range = time_range_text.split('–') 
                
                if len(time_range) == 2:
                    start_time = time_range[0].strip()
                    end_time = time_range[1].strip()
                    td_data['s_datetime'] = f"{date_str}T{start_time}:00+09:00"
                    td_data['e_datetime'] = f"{date_str}T{end_time}:00+09:00"
                td_data['time'] = time_range_text

            elif class_name == 'type':
                td_data['type'] = td.find('span').get_text(strip=True)
                
            elif class_name == 'title':
                a_tag = td.find('a')
                if a_tag:
                    title_text = a_tag.get_text(strip=True)
                    td_data['title'] = title_text
                    a_href = a_tag.get('href')
                    td_data['a_href'] = a_href
                    td_data['url'] = base_url + "/" + a_href
                else:
                    title_text = td.get_text(strip=True)
                    td_data['title'] = title_text
                
                role_list_em = td.find('em', class_='sched-role-list')
                if role_list_em:
                    role_text = role_list_em.get_text(strip=True)
                    speaker_list_str = role_text.replace('Speakers:', '').strip()
                    if speaker_list_str:
                         td_data['speaker'] = [s.strip() for s in speaker_list_str.split(',') if s.strip()]
                
                td_data['company'] = extract_companies_from_title(title_text)

                venue_div = td.find('div', class_='venue')
                if venue_div:
                    td_data['venue'] = venue_div.get_text(strip=True)

        if td_data.get('title') or td_data.get('s_datetime'):
             data_list.append(td_data)


# --- data_id を 1から始まる連番で先頭に付与する ---
final_data_list = []
for i, item in enumerate(data_list):
    data_id_value = i + 1
    
    new_item = {
        'data_id': data_id_value,
        **item
    }
    final_data_list.append(new_item)


# JSON形式で出力
OUTPUT_FILE_WITH_ID = 'output_2025_with_id.json'
with open(OUTPUT_FILE_WITH_ID, 'w', encoding='utf-8') as json_file:
    json.dump(final_data_list, json_file, ensure_ascii=False, indent=2)

print(f"データ抽出、企業名抽出（役割除去とカンマ保持の最新ロジック）、および data_id の付与が完了しました。")
print(f"結果を {OUTPUT_FILE_WITH_ID} に保存しました。")