import json
import sys

# --- ファイル名の定義 ---
# 読み込み元（ID付与済みファイル）
INPUT_FILE = 'output_2025_with_id.json'
# 修正済みデータの上書き/保存先
OUTPUT_FILE = 'output_2025_with_company_final.json'


# --- データ読み込み関数 ---
def load_data(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 最終ファイルが存在しない場合は、ID付与済みファイルを試す
        if filename == OUTPUT_FILE:
            return load_data(INPUT_FILE)
        
        print(f"エラー: ファイル '{filename}' が見つかりません。")
        print("1. のステップを実行し、ID付きのJSONファイルを生成してください。")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"エラー: ファイル '{filename}' のJSON形式が不正です。")
        sys.exit(1)

# --- データ保存関数 ---
def save_data(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"エラー: ファイルの保存中に問題が発生しました: {e}")
        return False

# --- ユーザー入力の配列をパースする関数 ---
def parse_array_input(input_str):
    input_str = input_str.strip()
    
    if not input_str:
        return []
    
    # ユーザー入力をJSONの配列形式 (例: ["A", "B"]) に変換するため、両端にブラケットを追加
    json_string = f'[{input_str}]'
    
    # 【修正点】シングルクォーテーションをダブルクォーテーションに置換して、JSON互換性を確保
    safe_json_string = json_string.replace("'", '"')
    
    try:
        # 修正された文字列をJSONとしてロード
        parsed_list = json.loads(safe_json_string)
        
        if not all(isinstance(item, str) for item in parsed_list):
            raise ValueError("配列の要素はすべて文字列である必要があります。")
            
        return parsed_list
    except json.JSONDecodeError as e:
        print(f"入力形式エラー: JSONとしてパースできませんでした。")
        print(f"入力は「\"項目1\", \"項目2\"」または「'項目1', '項目2'」のようにクォーテーションとカンマで区切られていますか？")
        return None
    except ValueError as e:
        print(f"入力形式エラー: {e}")
        return None

# --- メインの対話ループ ---
def interactive_correction():
    print("=====================================================")
    print("✨ スケジュールデータ 対話型修正ツール")
    print(f"   読み込みファイル: {INPUT_FILE} または {OUTPUT_FILE}")
    print(f"   出力ファイル: {OUTPUT_FILE} (上書き保存)")
    print("=====================================================")
    
    data_list = load_data(OUTPUT_FILE) 

    data_map = {item['data_id']: item for item in data_list}
    max_id = len(data_list)
    
    while True:
        prompt = f"\n修正するデータIDを入力してください (1 〜 {max_id})。\n"
        prompt += "終了する場合は 'q' を入力: "
        user_input = input(prompt).strip().lower()
        
        if user_input == 'q':
            print("\n👋 修正を終了します。現在の修正結果はファイルに保存されています。")
            break
            
        try:
            data_id = int(user_input)
            if data_id not in data_map:
                print(f"⚠️ エラー: ID {data_id} は存在しません。1 から {max_id} の間で入力してください。")
                continue
        except ValueError:
            print(f"⚠️ エラー: 無効な入力です。整数または 'q' を入力してください。")
            continue

        item_to_correct = data_map[data_id]
        
        # --- 全ての情報を一度に表示 ---
        print("\n-----------------------------------------------------")
        print(f"💡 ID: {data_id}")
        print(f"TITLE: {item_to_correct['title']}")
        print(f"  日付: {item_to_correct.get('date')} / {item_to_correct.get('time')}")
        print(f"  現Speaker: {item_to_correct.get('speaker', [])}")
        print(f"  現Company: {item_to_correct.get('company', [])}")
        print("-----------------------------------------------------")
        
        modified = False

        # --- 1. Speaker 修正 ---
        while True:
            speaker_input = input(
                "▶️ Speaker (人名) を修正しますか？\n"
                "   [修正なし: s/Return, 入力例: '名前1', '名前2']\n"
                "   新しい値 (s/入力): "
            ).strip()
            
            if speaker_input.lower() == 's' or not speaker_input:
                print("   Speaker 修正をスキップしました。")
                break
                
            parsed_speakers = parse_array_input(speaker_input)
            if parsed_speakers is not None:
                item_to_correct['speaker'] = parsed_speakers
                print("   ✅ Speaker を修正しました。")
                modified = True
                break
        
        # --- 2. Company 修正 ---
        while True:
            company_input = input(
                "▶️ Company (企業/組織名) を修正しますか？\n"
                "   [修正なし: s/Return, 入力例: '企業A', '組織B Co., Ltd.']\n"
                "   新しい値 (s/入力): "
            ).strip()

            if company_input.lower() == 's' or not company_input:
                print("   Company 修正をスキップしました。")
                break
                
            parsed_companies = parse_array_input(company_input)
            if parsed_companies is not None:
                item_to_correct['company'] = parsed_companies
                print("   ✅ Company を修正しました。")
                modified = True
                break
                
        # --- 3. データの保存 (修正が適用された場合) ---
        if modified:
            if save_data(data_list, OUTPUT_FILE):
                print(f"💾 ID: {data_id} の修正結果を {OUTPUT_FILE} に上書き保存しました。")
        else:
            print("   修正は適用されませんでした。") 


if __name__ == "__main__":
    interactive_correction()