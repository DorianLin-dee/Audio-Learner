# 🎙️ Audio Learner - 音视频学习内容分析助手

将视频/播客音频内容快速转化为中文分析笔记。支持说话者识别和翻译辅助，适合学习外文访谈和公开课。

---

## 📦 功能

- **音频下载**：支持 B站、YouTube 等主流平台
- **语音转录**：使用 Whisper 本地模型，多语言自动检测
- **说话者识别**：基于停顿时间的分组算法
- **翻译辅助**：Google Translate API 翻译原文
- **结构化输出**：中文思维导图、核心观点、关键结论

---

## 🚀 快速开始

### 1. 安装依赖

```bash
brew install ffmpeg
pip3 install yt-dlp openai-whisper requests
```

### 2. 下载音频并转录

```bash
python3 quick_transcribe.py "https://www.bilibili.com/video/BV1xxxxx"
```

### 3. 高级转录（带翻译和说话者识别）

```bash
python3 local_whisper_transcriber_final.py audio_downloads/video.mp3 \
    --speaker-names "张三,李四" \
    --output-dir ./outputs
```

### 4. 在 SOLO 中使用

将 `Audio-learner` 目录放到项目的 `.trae/skills/` 下，然后在 SOLO 中选择此 Skill 即可。

---

## 📂 项目结构

```
Audio-learner/
├── SKILL.md                              # Skill 核心说明（给 SOLO AI 看）
├── README.md                             # 快速上手指南
├── quick_transcribe.py                   # 快速下载+转录工具
├── local_whisper_transcriber_final.py    # 核心工具（转录+翻译+说话者）
├── local_whisper_transcriber.py          # 基础转录工具
├── content_searcher.py                   # 搜索现成文稿
└── example_output.md                     # 输出示例
```

---

## 💡 使用场景

| 场景 | 描述 |
|------|------|
| 学习外语内容 | 听外文访谈、公开课，自动提取核心要点 |
| 整理访谈记录 | 多人对话自动区分说话者，分析各方观点 |
| 内容创作素材 | 快速提取视频关键要点，用于二次创作 |
| 知识管理 | 将音视频内容转化为可搜索、可引用的笔记 |

---

## 📝 输出格式

```markdown
📚 内容分析

**主题**：...
**说话者**：...
**总时长**：...

---

## 📋 内容框架

├── 1. ... [00:00]
│   └── ...
└── 2. ... [00:05]

---

## 💡 核心观点

1. **观点标题**
   原文："..." [SPEAKER_01 @ 00:05:20]

---

## 🎯 关键结论

1. ...
2. ...
3. ...
4. ...
5. ...

---

## 🗣️ 说话者观点分布

- **SPEAKER_01**：主要讨论了... 占 XX%
- **SPEAKER_02**：主要讨论了... 占 XX%
```

---

## ⚠️ 注意事项

- **隐私友好**：所有处理在本地完成，音频不上传任何服务器
- **第一次使用**：会自动下载 Whisper 模型（~150MB），请耐心等待
- **分析质量**：取决于转录质量，说话清晰的视频效果更好
- **长视频**：超过30分钟的视频建议分段处理

---

## 🔧 参数说明

### local_whisper_transcriber_final.py

| 参数 | 说明 | 示例 |
|------|------|------|
| `input` | 视频链接或本地音频文件 | `audio.mp3` |
| `--speaker-names` | 说话者名称，逗号分隔 | `"张三,李四"` |
| `--output-dir` | 输出目录 | `./outputs` |

---

## 📄 License

MIT License
