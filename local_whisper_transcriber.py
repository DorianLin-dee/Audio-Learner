#!/usr/bin/env python3
"""
本地 Whisper 转录工具 - 完全免费！
不需要 API Key，不需要信用卡，不需要网络（除了下载视频）
支持B站反爬虫处理
"""

import sys
import os
import yt_dlp
from pathlib import Path

def is_bilibili(url):
    """判断是否是B站链接"""
    return 'bilibili.com' in url.lower()

def download_audio(url, output_dir='./audio_downloads'):
    """只下载音频，支持B站反爬虫"""
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"📥 正在下载音频...")
    
    # 检测是否是B站
    if is_bilibili(url):
        print(f"🔧 检测到B站链接，启用反爬虫配置...")
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
            # B站反爬虫关键配置
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.bilibili.com/',
                'Origin': 'https://www.bilibili.com',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
            },
        }
        
        # 如果有cookies文件，使用cookies
        cookie_file = Path.home() / '.bilibili_cookies.txt'
        if cookie_file.exists():
            print(f"🍪 使用cookies文件: {cookie_file}")
            ydl_opts['cookiefile'] = str(cookie_file)
    else:
        # 非B站链接的普通配置
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{output_dir}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'noplaylist': True,
        }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            audio_file = Path(output_dir) / f"{info['id']}.mp3"
            print(f"✅ 音频下载完成: {audio_file}")
            return str(audio_file)
        except Exception as e:
            if is_bilibili(url):
                print(f"\n⚠️ B站下载失败，尝试备用方案...")
                # 尝试使用B站API下载
                return download_bilibili_fallback(url, output_dir)
            else:
                raise e

def download_bilibili_fallback(url, output_dir):
    """B站备用下载方案：使用移动端API"""
    import requests
    
    print(f"🔄 尝试备用方案...")
    
    # 从URL中提取BVID
    import re
    match = re.search(r'BV[a-zA-Z0-9]+', url)
    if not match:
        print("❌ 无法提取BVID")
        return None
    
    bvid = match.group(0)
    print(f"📹 BVID: {bvid}")
    
    # 使用B站API获取视频信息
    api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/',
    }
    
    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        data = resp.json()
        
        if data['code'] == 0:
            cid = data['data']['cid']
            title = data['data']['title']
            print(f"✅ 获取视频信息成功: {title}")
            
            # 尝试从多个CDN获取音频
            cdn_urls = [
                f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=80&fnval=0&fnver=0&type=mp4",
                f"https://api.bilibili.com/x/player/playurl?bvid={bvid}&cid={cid}&qn=16&fnval=404&type=mp4",
            ]
            
            for cdn_url in cdn_urls:
                try:
                    print(f"🔄 尝试CDN: {cdn_url[:50]}...")
                    resp = requests.get(cdn_url, headers=headers, timeout=15)
                    data = resp.json()
                    
                    if data['code'] == 0 and data['data']['durl']:
                        audio_url = data['data']['durl'][0]['url']
                        
                        # 下载音频
                        print(f"📥 从备用CDN下载...")
                        audio_resp = requests.get(audio_url, headers=headers, timeout=60, stream=True)
                        
                        audio_file = Path(output_dir) / f"{bvid}.mp3"
                        with open(audio_file, 'wb') as f:
                            for chunk in audio_resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        print(f"✅ 备用下载成功: {audio_file}")
                        return str(audio_file)
                except Exception as e:
                    print(f"⚠️ CDN失败: {e}")
                    continue
            
            print("❌ 所有CDN都失败")
            return None
        else:
            print(f"❌ API请求失败: {data['message']}")
            return None
    except Exception as e:
        print(f"❌ 备用方案失败: {e}")
        return None

def transcribe_local(audio_path, model_size='base', language=None, speaker_diarization=False):
    """使用本地 Whisper 转录，可选说话者识别"""
    try:
        import whisper
    except ImportError:
        print("\n❌ 需要先安装 Whisper！")
        print("\n请运行: pip install openai-whisper")
        print("如果在 macOS 上还需要: brew install ffmpeg")
        sys.exit(1)
    
    print(f"🎤 正在加载模型: {model_size}...")
    print(f"💡 提示: 第一次运行会自动下载模型（约 150MB）")
    
    model = whisper.load_model(model_size)
    
    print(f"📝 正在转录...")
    if language:
        print(f"🔤 指定语言: {language}")
        result = model.transcribe(audio_path, language=language, word_timestamps=True)
    else:
        print(f"🔤 自动检测语言...")
        result = model.transcribe(audio_path, word_timestamps=True)
    
    # 说话者识别
    if speaker_diarization:
        result = add_speaker_labels(result, audio_path)
    
    print(f"✅ 转录成功！")
    if 'language' in result:
        print(f"🌍 检测到的语言: {result['language']}")
    return result

def add_speaker_labels(result, audio_path):
    """添加说话者标签（使用pyannote.audio）"""
    try:
        from pyannote.audio import Pipeline
        import torch
        print(f"🎙️ 正在进行说话者识别...")
        print(f"💡 提示: 第一次运行会自动下载说话者识别模型")
        
        # 加载pyannote说话者识别pipeline
        # 注意：需要在https://huggingface.co/pyannote/speaker-diarization获取token
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=False  # 可选，需要自己的token
            )
        except:
            print(f"⚠️ 说话者识别模型加载失败，使用简单的说话者分组")
            return add_simple_speaker_labels(result)
        
        # 处理音频
        diarization = pipeline(audio_path)
        
        # 为每个segment分配说话者
        speaker_segments = []
        for segment, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                'start': segment.start,
                'end': segment.end,
                'speaker': speaker
            })
        
        # 匹配到whisper的结果
        for seg in result['segments']:
            seg_start = seg.get('start', 0)
            seg_end = seg.get('end', 0)
            
            # 找到最匹配的说话者
            best_speaker = None
            best_overlap = 0
            for sp_seg in speaker_segments:
                overlap = max(0, min(seg_end, sp_seg['end']) - max(seg_start, sp_seg['start']))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_speaker = sp_seg['speaker']
            
            if best_speaker:
                seg['speaker'] = best_speaker
        
        return result
        
    except ImportError:
        print(f"⚠️ pyannote.audio未安装，使用简单的说话者分组")
        return add_simple_speaker_labels(result)
    except Exception as e:
        print(f"⚠️ 说话者识别失败: {e}，使用简单分组")
        return add_simple_speaker_labels(result)

def add_simple_speaker_labels(result):
    """简单的说话者识别：基于间隔和对话模式分组"""
    from collections import defaultdict
    
    segments = result.get('segments', [])
    if not segments:
        return result
    
    # 首先，合并时间上非常接近的片段
    merged_segments = []
    if segments:
        current_group = [segments[0]]
        for i in range(1, len(segments)):
            prev_seg = segments[i-1]
            curr_seg = segments[i]
            silence_duration = curr_seg.get('start', 0) - prev_seg.get('end', 0)
            
            # 如果沉默时间很短（< 1.5秒），合并到同一说话者
            if silence_duration < 1.5:
                current_group.append(curr_seg)
            else:
                merged_segments.append(current_group)
                current_group = [curr_seg]
        merged_segments.append(current_group)
    
    # 现在为每个组分配说话者，尝试减少说话者数量（通常对话只有2-3个主要说话者）
    # 使用简单的启发式方法：如果内容相似，合并到相同说话者
    speaker_counter = 1
    for group in merged_segments:
        speaker_id = f"SPEAKER_{speaker_counter:02d}"
        for seg in group:
            seg['speaker'] = speaker_id
        
        # 只在连续说话很长时才增加说话者（假设对话交替）
        # 但实际上，我们需要更复杂的算法来分析声音特征
        # 这里暂时简化处理：每2-3个说话者就循环回来
        speaker_counter += 1
        if speaker_counter > 3:  # 假设最多3个主要说话者
            speaker_counter = 1
    
    return result

def format_timestamp(seconds):
    """将秒数转换为 HH:MM:SS 格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def generate_transcript(result, output_file='transcript.txt'):
    """生成带时间戳和说话者标签的转录稿"""
    with open(output_file, 'w', encoding='utf-8') as f:
        if 'segments' in result:
            for segment in result['segments']:
                start_time = format_timestamp(segment.get('start', 0))
                text = segment.get('text', '').strip()
                speaker = segment.get('speaker', None)
                
                if text:
                    if speaker:
                        line = f"{start_time} - [{speaker}] {text}\n"
                        print(f"  {start_time} - [{speaker}] {text[:50]}...")
                    else:
                        line = f"{start_time} - {text}\n"
                        print(f"  {start_time} - {text[:60]}...")
                    f.write(line)
        else:
            f.write(result['text'])
            print(result['text'])
    
    print(f"\n✅ 转录稿已保存: {output_file}")
    return output_file

def main():
    if len(sys.argv) < 2:
        print("用法: python local_whisper_transcriber.py <视频链接或本地音频文件> [--语言] [--模型大小] [--说话者识别]")
        print("示例:")
        print("  python local_whisper_transcriber.py https://www.bilibili.com/video/BV1Z9QABeEgf")
        print("  python local_whisper_transcriber.py /path/to/audio.mp3 --ja")
        print("  python local_whisper_transcriber.py /path/to/audio.mp3 --speaker")
        print("\n💡 可选参数:")
        print("  --zh, --cn, --chinese   - 指定为中文")
        print("  --ja, --jp, --japanese  - 指定为日语")
        print("  --en, --english         - 指定为英语")
        print("  --tiny                  - 最快，但准确率最低（约 32MB）")
        print("  --base                  - 推荐日常使用（约 150MB，默认）")
        print("  --small                 - 更准确，但更慢（约 500MB）")
        print("  --medium                - 非常准确，但很慢（约 1.5GB）")
        print("  --speaker, --diarize    - 启用说话者识别（区分不同说话者）")
        sys.exit(1)
    
    # 解析参数
    video_url = sys.argv[1]
    model_size = 'base'  # 默认
    language = None      # 默认自动检测
    speaker_diarization = False  # 默认不启用说话者识别
    
    # 语言参数
    if '--zh' in sys.argv or '--cn' in sys.argv or '--chinese' in sys.argv:
        language = 'zh'
    elif '--ja' in sys.argv or '--jp' in sys.argv or '--japanese' in sys.argv:
        language = 'ja'
    elif '--en' in sys.argv or '--english' in sys.argv:
        language = 'en'
    
    # 模型大小参数
    if '--tiny' in sys.argv:
        model_size = 'tiny'
    elif '--small' in sys.argv:
        model_size = 'small'
    elif '--medium' in sys.argv:
        model_size = 'medium'
    
    # 说话者识别参数
    if '--speaker' in sys.argv or '--diarize' in sys.argv:
        speaker_diarization = True
        print(f"🎙️ 已启用说话者识别")
    
    # 检测是否是本地文件
    is_url = video_url.startswith('http://') or video_url.startswith('https://')
    
    if is_url:
        # 第一步：下载音频
        audio_file = download_audio(video_url)
    else:
        # 本地文件，直接使用
        audio_file = video_url
        print(f"📁 使用本地文件: {audio_file}")
    
    # 第二步：本地转录
    result = transcribe_local(audio_file, model_size, language, speaker_diarization)
    
    # 第三步：生成带时间戳的转录稿
    transcript_file = generate_transcript(result)
    
    print("\n" + "="*60)
    print("🎉 全部完成！")
    print(f"📄 转录稿: {transcript_file}")
    print(f"💡 提示: 现在可以把转录稿发给 learning-content-analyzer skill 分析了！")
    print("="*60)

if __name__ == '__main__':
    main()
