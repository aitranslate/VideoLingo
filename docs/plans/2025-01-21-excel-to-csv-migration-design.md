# Excel 到 CSV 迁移设计

**日期**: 2025-01-21
**作者**: Claude Code
**状态**: 设计完成

## 概述

将项目中所有使用 Excel (`.xlsx`) 的文件迁移到 CSV 格式，移除 `openpyxl` 依赖。

## 1. 文件映射

| 原文件 | 新文件 | 用途 |
|--------|--------|------|
| `custom_terms.xlsx` | `custom_terms.csv` | 用户自定义术语表 |
| `batch/tasks_setting.xlsx` | `batch/tasks_setting.csv` | 批处理任务配置 |
| `output/log/cleaned_chunks.xlsx` | `output/log/cleaned_chunks.csv` | 清理后的音频块 |
| `output/log/translation_results.xlsx` | `output/log/translation_results.csv` | 翻译结果 |
| `output/log/translation_results_for_subtitles.xlsx` | `output/log/translation_results_for_subtitles.csv` | 字幕翻译结果 |
| `output/log/translation_results_remerged.xlsx` | `output/log/translation_results_remerged.csv` | 重新合并的翻译结果 |
| `output/audio/tts_tasks.xlsx` | `output/audio/tts_tasks.csv` | TTS 任务表 |

## 2. 代码变更范围

### 常量定义
- `core/utils/models.py` - 更新所有 Excel 文件路径为 CSV

### 核心业务代码
- `core/_4_1_summarize.py` - 读取 `custom_terms.xlsx` → `custom_terms.csv`
- `core/_4_2_translate.py` - 读取/写入 Excel → CSV
- `core/_5_split_sub.py` - 读取/写入 Excel → CSV
- `core/_6_gen_sub.py` - 读取 Excel → CSV
- `core/_8_1_audio_task.py` - 写入 Excel → CSV
- `core/_8_2_dub_chunks.py` - 读取/写入 Excel → CSV
- `core/_9_refer_audio.py` - 读取 Excel → CSV
- `core/_10_gen_audio.py` - 读取/写入 Excel → CSV
- `core/_11_merge_audio.py` - 读取 Excel → CSV

### 批处理模块
- `batch/utils/batch_processor.py` - 读取/写入 Excel → CSV
- `batch/utils/settings_check.py` - 读取 Excel → CSV

### 其他
- `core/spacy_utils/split_by_mark.py` - 读取 Excel → CSV

### 依赖文件
- `requirements.txt` - 移除 `openpyxl==3.1.5`

## 3. 代码变更模式

### 读取文件
```python
# 旧代码
df = pd.read_excel('file.xlsx')

# 新代码
df = pd.read_csv('file.csv')
```

### 写入文件
```python
# 旧代码
df.to_excel('file.xlsx', index=False)

# 新代码
df.to_csv('file.csv', index=False, encoding='utf-8-sig')
```

### 编码策略
所有 CSV 文件统一使用 `utf-8-sig` 编码（带 BOM），确保用户可以用 Excel 直接打开编辑，不会出现中文乱码。

## 4. 需要特别注意的问题

### 问题 1: custom_terms.csv 列结构
- 原 Excel 文件列名：`Source`, `Trans`, `Explain(Optional)`
- 当前代码使用 `row.iloc[0/1/2]` 按位置读取
- 迁移到 CSV 后，列名简化为：`Source`, `Trans`, `Note`
- 代码改用列名访问：

```python
# 旧代码
"src": str(row.iloc[0]),
"tgt": str(row.iloc[1]),
"note": str(row.iloc[2])

# 新代码
"src": str(row['Source']),
"tgt": str(row['Trans']),
"note": str(row['Note'])
```

### 问题 2: tasks_setting.csv 列结构
- 列名保持不变：`Video File`, `Source Language`, `Target Language`, `Dubbing`, `Status`
- 无需特殊处理

### 问题 3: 嵌套数据列
- `tts_tasks.csv` 中的 `lines` 和 `new_sub_times` 列存储的是列表/元组的字符串表示
- CSV 读取后会变成字符串，需要 `eval()` 或 `ast.literal_eval()` 处理
- 保持现有的 `eval()` 处理方式不变

### 问题 4: 数据类型
- Excel 中 `NaN` 在 CSV 中显示为空字符串
- pandas 读取 CSV 时空字符串默认解析为 `NaN`，行为一致
- 无需额外处理

## 5. 文档更新

### README 文件
1. 删除 `batch/README.md`
2. 将 `batch/README.zh.md` 重命名为 `batch/README.md`
3. 更新其中所有引用 `tasks_setting.xlsx` 的地方为 `tasks_setting.csv`

### .gitignore
- 将 `batch/tasks_setting.xlsx` 改为 `batch/tasks_setting.csv`

## 6. 实施步骤

1. 更新常量定义 (`core/utils/models.py`)
2. 更新核心业务代码 (8 个文件)
3. 更新批处理模块 (2 个文件)
4. 更新其他相关代码
5. 更新 requirements.txt (移除 openpyxl)
6. 更新文档 (README 和 .gitignore)
7. 测试验证

### 注意事项
- 每次修改后确保 `encoding='utf-8-sig'` 参数正确添加
- `custom_terms.csv` 的列名访问方式需要同步更新
- 确保所有 `read_excel` → `read_csv` 和 `to_excel` → `to_csv` 替换完整
