import os
import json
from core.prompts import get_summary_prompt
import pandas as pd
from core.utils import *
from core.utils.models import _3_2_SPLIT_BY_MEANING, _4_1_TERMINOLOGY

CUSTOM_TERMS_PATH = 'custom_terms.csv'

def combine_chunks():
    """Combine the text chunks identified by whisper into a single long text"""
    with open(_3_2_SPLIT_BY_MEANING, 'r', encoding='utf-8') as file:
        sentences = file.readlines()
    cleaned_sentences = [line.strip() for line in sentences]
    combined_text = ' '.join(cleaned_sentences)
    return combined_text[:load_key('summary_length')]  #! Return only the first x characters

def search_things_to_note_in_prompt(sentence):
    """Search for terms to note in the given sentence"""
    with open(_4_1_TERMINOLOGY, 'r', encoding='utf-8') as file:
        things_to_note = json.load(file)
    things_to_note_list = [term['src'] for term in things_to_note['terms'] if term['src'].lower() in sentence.lower()]
    if things_to_note_list:
        prompt = '\n'.join(
            f'{i+1}. "{term["src"]}": "{term["tgt"]}",'
            f' meaning: {term["note"]}'
            for i, term in enumerate(things_to_note['terms'])
            if term['src'] in things_to_note_list
        )
        return prompt
    else:
        return None

def get_summary():
    src_content = combine_chunks()
    # Read custom_terms.csv with error handling and multiple encoding attempts
    if os.path.exists(CUSTOM_TERMS_PATH):
        # Try different encodings (Excel on Windows often saves as GBK/GB2312)
        encodings = ['utf-8-sig', 'gbk', 'gb2312', 'utf-8']
        custom_terms = None
        for enc in encodings:
            try:
                custom_terms = pd.read_csv(CUSTOM_TERMS_PATH, encoding=enc)
                break
            except (UnicodeDecodeError, UnicodeError):
                continue
        if custom_terms is None:
            # All encodings failed, create empty DataFrame
            custom_terms = pd.DataFrame(columns=['Source', 'Trans', 'Note'])
    else:
        custom_terms = pd.DataFrame(columns=['Source', 'Trans', 'Note'])

    custom_terms_json = {
        "terms":
            [
                {
                    "src": str(row['Source']),
                    "tgt": str(row['Trans']),
                    "note": str(row['Note']) if pd.notna(row['Note']) else ''
                }
                for _, row in custom_terms.iterrows()
                if pd.notna(row['Source']) and str(row['Source']).strip()
            ]
    }
    if len(custom_terms) > 0:
        rprint(f"📖 Custom Terms Loaded: {len(custom_terms)} terms")
        rprint("📝 Terms Content:", json.dumps(custom_terms_json, indent=2, ensure_ascii=False))
    summary_prompt = get_summary_prompt(src_content, custom_terms_json)
    rprint("📝 Summarizing and extracting terminology ...")
    
    def valid_summary(response_data):
        required_keys = {'src', 'tgt', 'note'}
        if 'terms' not in response_data:
            return {"status": "error", "message": "Invalid response format"}
        for term in response_data['terms']:
            if not all(key in term for key in required_keys):
                return {"status": "error", "message": "Invalid response format"}   
        return {"status": "success", "message": "Summary completed"}

    summary = ask_gpt(summary_prompt, resp_type='json', valid_def=valid_summary, log_title='summary')
    summary['terms'].extend(custom_terms_json['terms'])
    
    with open(_4_1_TERMINOLOGY, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=4)

    rprint(f'💾 Summary log saved to → `{_4_1_TERMINOLOGY}`')

if __name__ == '__main__':
    get_summary()