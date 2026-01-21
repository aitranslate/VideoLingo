# Excel 到 CSV 迁移实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**目标:** 将项目中所有使用 Excel (`.xlsx`) 的文件迁移到 CSV 格式，移除 `openpyxl` 依赖。

**架构:** 将所有 `.xlsx` 文件路径改为 `.csv`，使用 pandas 的 `read_csv` 和 `to_csv(encoding='utf-8-sig')` 替代 `read_excel` 和 `to_excel`。所有 CSV 文件使用 `utf-8-sig` 编码，确保用户可以用 Excel 打开编辑不会乱码。

**技术栈:** Python, pandas, CSV

---

## Task 1: 更新常量定义文件

**文件:**
- 修改: `core/utils/models.py`

**Step 1: 修改文件扩展名**

将所有 `.xlsx` 文件路径改为 `.csv`:

```python
# 中间输出文件
_2_CLEANED_CHUNKS = "output/log/cleaned_chunks.csv"
_3_1_SPLIT_BY_NLP = "output/log/split_by_nlp.txt"
_3_2_SPLIT_BY_MEANING = "output/log/split_by_meaning.txt"
_4_1_TERMINOLOGY = "output/log/terminology.json"
_4_2_TRANSLATION = "output/log/translation_results.csv"
_5_SPLIT_SUB = "output/log/translation_results_for_subtitles.csv"
_5_REMERGED = "output/log/translation_results_remerged.csv"
_8_1_AUDIO_TASK = "output/audio/tts_tasks.csv"
```

**Step 2: 运行语法检查**

运行: `python -m py_compile core/utils/models.py`
Expected: 无语法错误

**Step 3: 提交**

```bash
git add core/utils/models.py
git commit -m "refactor: update file paths from xlsx to csv in models.py"
```

---

## Task 2: 更新 core/_4_1_summarize.py

**文件:**
- 修改: `core/_4_1_summarize.py:7,35-46`

**Step 1: 修改常量定义**

```python
CUSTOM_TERMS_PATH = 'custom_terms.csv'
```

**Step 2: 修改读取方式**

将:
```python
custom_terms = pd.read_excel(CUSTOM_TERMS_PATH)
custom_terms_json = {
    "terms":
        [
            {
                "src": str(row.iloc[0]),
                "tgt": str(row.iloc[1]),
                "note": str(row.iloc[2])
            }
            for _, row in custom_terms.iterrows()
        ]
}
```

改为:
```python
custom_terms = pd.read_csv(CUSTOM_TERMS_PATH)
custom_terms_json = {
    "terms":
        [
            {
                "src": str(row['Source']),
                "tgt": str(row['Trans']),
                "note": str(row['Note']) if pd.notna(row['Note']) else ''
            }
            for _, row in custom_terms.iterrows()
        ]
}
```

**Step 3: 运行语法检查**

运行: `python -m py_compile core/_4_1_summarize.py`
Expected: 无语法错误

**Step 4: 提交**

```bash
git add core/_4_1_summarize.py
git commit -m "refactor: use csv for custom_terms in _4_1_summarize.py"
```

---

## Task 3: 更新 core/_4_2_translate.py

**文件:**
- 修改: `core/_4_2_translate.py:98,108`

**Step 1: 修改读取方式**

将:
```python
df_text = pd.read_excel(_2_CLEANED_CHUNKS)
```

改为:
```python
df_text = pd.read_csv(_2_CLEANED_CHUNKS)
```

**Step 2: 修改写入方式**

将:
```python
df_time.to_excel(_4_2_TRANSLATION, index=False)
```

改为:
```python
df_time.to_csv(_4_2_TRANSLATION, index=False, encoding='utf-8-sig')
```

**Step 3: 运行语法检查**

运行: `python -m py_compile core/_4_2_translate.py`
Expected: 无语法错误

**Step 4: 提交**

```bash
git add core/_4_2_translate.py
git commit -m "refactor: use csv in _4_2_translate.py"
```

---

## Task 4: 更新 core/_5_split_sub.py

**文件:**
- 修改: `core/_5_split_sub.py:99,125-126`

**Step 1: 修改读取方式**

将:
```python
df = pd.read_excel(_4_2_TRANSLATION)
```

改为:
```python
df = pd.read_csv(_4_2_TRANSLATION)
```

**Step 2: 修改写入方式**

将:
```python
pd.DataFrame({'Source': split_src, 'Translation': split_trans}).to_excel(_5_SPLIT_SUB, index=False)
pd.DataFrame({'Source': src, 'Translation': remerged}).to_excel(_5_REMERGED, index=False)
```

改为:
```python
pd.DataFrame({'Source': split_src, 'Translation': split_trans}).to_csv(_5_SPLIT_SUB, index=False, encoding='utf-8-sig')
pd.DataFrame({'Source': src, 'Translation': remerged}).to_csv(_5_REMERGED, index=False, encoding='utf-8-sig')
```

**Step 3: 运行语法检查**

运行: `python -m py_compile core/_5_split_sub.py`
Expected: 无语法错误

**Step 4: 提交**

```bash
git add core/_5_split_sub.py
git commit -m "refactor: use csv in _5_split_sub.py"
```

---

## Task 5: 更新 core/_6_gen_sub.py

**文件:**
- 修改: `core/_6_gen_sub.py:151,153,160`

**Step 1: 修改读取方式**

将:
```python
df_text = pd.read_excel(_2_CLEANED_CHUNKS)
df_translate = pd.read_excel(_5_SPLIT_SUB)
df_translate_for_audio = pd.read_excel(_5_REMERGED)
```

改为:
```python
df_text = pd.read_csv(_2_CLEANED_CHUNKS)
df_translate = pd.read_csv(_5_SPLIT_SUB)
df_translate_for_audio = pd.read_csv(_5_REMERGED)
```

**Step 2: 运行语法检查**

运行: `python -m py_compile core/_6_gen_sub.py`
Expected: 无语法错误

**Step 3: 提交**

```bash
git add core/_6_gen_sub.py
git commit -m "refactor: use csv in _6_gen_sub.py"
```

---

## Task 6: 更新 core/_8_1_audio_task.py

**文件:**
- 修改: `core/_8_1_audio_task.py:139`

**Step 1: 修改写入方式**

将:
```python
df.to_excel(_8_1_AUDIO_TASK, index=False)
```

改为:
```python
df.to_csv(_8_1_AUDIO_TASK, index=False, encoding='utf-8-sig')
```

**Step 2: 运行语法检查**

运行: `python -m py_compile core/_8_1_audio_task.py`
Expected: 无语法错误

**Step 3: 提交**

```bash
git add core/_8_1_audio_task.py
git commit -m "refactor: use csv in _8_1_audio_task.py"
```

---

## Task 7: 更新 core/_8_2_dub_chunks.py

**文件:**
- 修改: `core/_8_2_dub_chunks.py:134,202`

**Step 1: 修改读取方式**

将:
```python
df = pd.read_excel(_8_1_AUDIO_TASK)
```

改为:
```python
df = pd.read_csv(_8_1_AUDIO_TASK)
```

**Step 2: 修改写入方式**

将:
```python
df.to_excel(_8_1_AUDIO_TASK, index=False)
```

改为:
```python
df.to_csv(_8_1_AUDIO_TASK, index=False, encoding='utf-8-sig')
```

**Step 3: 运行语法检查**

运行: `python -m py_compile core/_8_2_dub_chunks.py`
Expected: 无语法错误

**Step 4: 提交**

```bash
git add core/_8_2_dub_chunks.py
git commit -m "refactor: use csv in _8_2_dub_chunks.py"
```

---

## Task 8: 更新 core/_9_refer_audio.py

**文件:**
- 修改: `core/_9_refer_audio.py:35`

**Step 1: 修改读取方式**

将:
```python
df = pd.read_excel(_8_1_AUDIO_TASK)
```

改为:
```python
df = pd.read_csv(_8_1_AUDIO_TASK)
```

**Step 2: 运行语法检查**

运行: `python -m py_compile core/_9_refer_audio.py`
Expected: 无语法错误

**Step 3: 提交**

```bash
git add core/_9_refer_audio.py
git commit -m "refactor: use csv in _9_refer_audio.py"
```

---

## Task 9: 更新 core/_10_gen_audio.py

**文件:**
- 修改: `core/_10_gen_audio.py:218,228`

**Step 1: 修改读取方式**

将:
```python
tasks_df = pd.read_excel(_8_1_AUDIO_TASK)
```

改为:
```python
tasks_df = pd.read_csv(_8_1_AUDIO_TASK)
```

**Step 2: 修改写入方式**

将:
```python
tasks_df.to_excel(_8_1_AUDIO_TASK, index=False)
```

改为:
```python
tasks_df.to_csv(_8_1_AUDIO_TASK, index=False, encoding='utf-8-sig')
```

**Step 3: 运行语法检查**

运行: `python -m py_compile core/_10_gen_audio.py`
Expected: 无语法错误

**Step 4: 提交**

```bash
git add core/_10_gen_audio.py
git commit -m "refactor: use csv in _10_gen_audio.py"
```

---

## Task 10: 更新 core/_11_merge_audio.py

**文件:**
- 修改: `core/_11_merge_audio.py:19`

**Step 1: 修改读取方式**

将:
```python
df = pd.read_excel(excel_file)
```

改为:
```python
df = pd.read_csv(excel_file)
```

**Step 2: 运行语法检查**

运行: `python -m py_compile core/_11_merge_audio.py`
Expected: 无语法错误

**Step 3: 提交**

```bash
git add core/_11_merge_audio.py
git commit -m "refactor: use csv in _11_merge_audio.py"
```

---

## Task 11: 更新 core/spacy_utils/split_by_mark.py

**文件:**
- 修改: `core/spacy_utils/split_by_mark.py:15`

**Step 1: 修改读取方式**

将:
```python
chunks = pd.read_excel("output/log/cleaned_chunks.xlsx")
```

改为:
```python
chunks = pd.read_csv("output/log/cleaned_chunks.csv")
```

**Step 2: 运行语法检查**

运行: `python -m py_compile core/spacy_utils/split_by_mark.py`
Expected: 无语法错误

**Step 3: 提交**

```bash
git add core/spacy_utils/split_by_mark.py
git commit -m "refactor: use csv in split_by_mark.py"
```

---

## Task 12: 更新 batch/utils/batch_processor.py

**文件:**
- 修改: `batch/utils/batch_processor.py:34,90`

**Step 1: 修改读取方式**

将:
```python
df = pd.read_excel('batch/tasks_setting.xlsx')
```

改为:
```python
df = pd.read_csv('batch/tasks_setting.csv')
```

**Step 2: 修改写入方式**

将:
```python
df.to_excel('batch/tasks_setting.xlsx', index=False)
```

改为:
```python
df.to_csv('batch/tasks_setting.csv', index=False, encoding='utf-8-sig')
```

**Step 3: 运行语法检查**

运行: `python -m py_compile batch/utils/batch_processor.py`
Expected: 无语法错误

**Step 4: 提交**

```bash
git add batch/utils/batch_processor.py
git commit -m "refactor: use csv in batch_processor.py"
```

---

## Task 13: 更新 batch/utils/settings_check.py

**文件:**
- 修改: `batch/utils/settings_check.py:7,15`

**Step 1: 修改常量定义**

将:
```python
SETTINGS_FILE = 'batch/tasks_setting.xlsx'
```

改为:
```python
SETTINGS_FILE = 'batch/tasks_setting.csv'
```

**Step 2: 修改读取方式**

将:
```python
df = pd.read_excel(SETTINGS_FILE)
```

改为:
```python
df = pd.read_csv(SETTINGS_FILE)
```

**Step 3: 运行语法检查**

运行: `python -m py_compile batch/utils/settings_check.py`
Expected: 无语法错误

**Step 4: 提交**

```bash
git add batch/utils/settings_check.py
git commit -m "refactor: use csv in settings_check.py"
```

---

## Task 14: 移除 openpyxl 依赖

**文件:**
- 修改: `requirements.txt:9`

**Step 1: 删除 openpyxl 依赖**

将:
```
openpyxl==3.1.5
```

删除该行

**Step 2: 提交**

```bash
git add requirements.txt
git commit -m "deps: remove openpyxl dependency"
```

---

## Task 15: 更新 .gitignore

**文件:**
- 修改: `.gitignore:160`

**Step 1: 修改文件名**

将:
```
batch/tasks_setting.xlsx
```

改为:
```
batch/tasks_setting.csv
```

**Step 2: 提交**

```bash
git add .gitignore
git commit -m "chore: update gitignore for csv files"
```

---

## Task 16: 更新 README 文档

**文件:**
- 删除: `batch/README.md`
- 修改: `batch/README.zh.md` (重命名为 `batch/README.md`)

**Step 1: 删除英文版 README**

```bash
del batch\README.md
```

**Step 2: 重命名中文版 README**

```bash
move batch\README.zh.md batch\README.md
```

**Step 3: 更新文件内容**

将所有 `tasks_setting.xlsx` 替换为 `tasks_setting.csv`:
- 第 16 行
- 第 36 行
- 第 38 行
- 第 49 行

**Step 4: 提交**

```bash
git add batch/
git commit -m "docs: update batch README for csv, keep only Chinese version"
```

---

## Task 17: 创建 custom_terms.csv 模板

**文件:**
- 创建: `custom_terms.csv`

**Step 1: 创建模板文件**

创建 `custom_terms.csv` 文件，内容为：
```csv
Source,Trans,Note
```

**Step 2: 提交**

```bash
git add custom_terms.csv
git commit -m "feat: add custom_terms.csv template"
```

---

## Task 18: 创建 batch/tasks_setting.csv 模板

**文件:**
- 创建: `batch/tasks_setting.csv`

**Step 1: 创建模板文件**

创建 `batch/tasks_setting.csv` 文件，内容为：
```csv
Video File,Source Language,Target Language,Dubbing,Status
```

**Step 2: 提交**

```bash
git add batch/tasks_setting.csv
git commit -m "feat: add batch/tasks_setting.csv template"
```

---

## Task 19: 最终验证

**Step 1: 语法检查所有修改的文件**

运行:
```bash
python -m py_compile core/utils/models.py
python -m py_compile core/_4_1_summarize.py
python -m py_compile core/_4_2_translate.py
python -m py_compile core/_5_split_sub.py
python -m py_compile core/_6_gen_sub.py
python -m py_compile core/_8_1_audio_task.py
python -m py_compile core/_8_2_dub_chunks.py
python -m py_compile core/_9_refer_audio.py
python -m py_compile core/_10_gen_audio.py
python -m py_compile core/_11_merge_audio.py
python -m py_compile core/spacy_utils/split_by_mark.py
python -m py_compile batch/utils/batch_processor.py
python -m py_compile batch/utils/settings_check.py
```

Expected: 全部无语法错误

**Step 2: 检查是否有遗漏的 xlsx 引用**

运行:
```bash
grep -r "read_excel\|to_excel\|\.xlsx" --include="*.py" core/ batch/
```

Expected: 没有输出（表示所有 Excel 相关代码都已替换）

**Step 3: 最终提交**

```bash
git add -A
git commit -m "chore: final verification for Excel to CSV migration"
```

---

## 测试建议

在实施完成后，建议进行以下测试：

1. **手动编辑测试**: 用 Excel 打开 `custom_terms.csv` 和 `batch/tasks_setting.csv`，确认可以正常编辑和保存
2. **流程测试**: 运行完整的视频处理流程，确认 CSV 文件读写正常
3. **批处理测试**: 运行批处理模式，确认 `tasks_setting.csv` 正常工作

---

## 回滚计划

如果需要回滚，可以：

```bash
git checkout main
git branch -D excel-to-csv
git worktree remove ../VideoLingo-excel-to-csv
```
