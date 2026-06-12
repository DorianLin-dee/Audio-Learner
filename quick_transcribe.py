
#!/usr/bin/env python3
"""
快速转录工具 - 在当前工作目录保存结果
先搜索网上文稿，有的话先展示再问是否转录
完全免费，不需要 API Key，使用本地 Whisper
"""

import sys
import os
from pathlib import Path

# 自动添加 skill 目录到 Python 路径
SKILL_DIR = Path(__file__).parent
sys.path.insert(0, str(SKILL_DIR))

def search_transcript_first(url):
    """先尝试搜索网上文稿"""
    try:
        from content_searcher import extract_video_info, search_web_transcript, extract_content_from_url, format_transcript_with_timestamps, save_transcript
        
        print(f"\n🔍 第一步：搜索网上文稿...")
        
        video_info = extract_video_info(url)
        search_results = search_web_transcript(video_info['title'], video_info['url'])
        
        if search_results:
            print(f"\n✅ 找到 {len(search_results)} 个可能的文稿来源:")
            print("-" * 70)
            for i, result in enumerate(search_results, 1):
                print(f"{i}. {result['title'][:60]}...")
            
            found_content = None
            for result in search_results[:3]:
                content = extract_content_from_url(result['url'])
                if content:
                    print(f"\n🎉 成功获取文稿内容! (约 {len(content)} 字符)")
                    found_content = content
                    break
            
            if found_content:
                formatted = format_transcript_with_timestamps(found_content)
                if formatted:
                    current_dir = Path.cwd()
                    output_file = save_transcript(formatted, current_dir)
                    
                    print("\n" + "=" * 70)
                    print("✅ 网上文稿已获取!")
                    print("=" * 70)
                    print("\n文稿预览:")
                    print("-" * 70)
                    preview_lines = formatted.split('\n')[:20]
                    print('\n'.join(preview_lines))
                    if len(preview_lines) < len(formatted.split('\n')):
                        print("... (更多内容请查看 transcript.txt)")
                    
                    return {
                        'found': True,
                        'file': output_file,
                        'content': formatted
                    }
            else:
                print("\n⚠️ 找到一些链接，但未能提取到可用的文稿内容")
        else:
            print("\n❌ 未找到现成文稿")
        
        return {'found': False}
    except Exception as e:
        print(f"\n⚠️ 文稿搜索出错: {e}")
        return {'found': False}

def do_transcription(video_url, model_size='base', language=None, speaker_diarization=False):
    """执行转录"""
    from local_whisper_transcriber import download_audio, transcribe_local, generate_transcript
    
    current_dir = Path.cwd()
    audio_dir = current_dir / 'audio_downloads'
    transcript_file = current_dir / 'transcript.txt'
    
    print(f"\n📂 工作目录: {current_dir}")
    print(f"📄 转录文件: {transcript_file}")
    
    # 检测是否是B站
    is_bilibili = 'bilibili.com' in video_url.lower()
    if is_bilibili:
        print(f"🔧 检测到B站链接，将启用反爬虫配置...")
    
    # 第一步：下载音频（如果是URL）
    if video_url.startswith('http://') or video_url.startswith('https://'):
        audio_file = download_audio(video_url, output_dir=str(audio_dir))
        if not audio_file:
            print("\n❌ 音频下载失败，无法继续转录")
            print("\n💡 可能的解决方案:")
            print("1. B站视频需要登录状态才能下载")
            print("   - 方法1: 使用浏览器插件导出cookies到 ~/.bilibili_cookies.txt")
            print("   - 方法2: 登录后手动下载视频，然后使用本地文件路径")
            print("2. 其他平台视频可以尝试更换网络环境")
            return None
    else:
        # 本地文件
        audio_file = video_url
        print(f"📁 使用本地文件: {audio_file}")
    
    # 第二步：本地转录
    result = transcribe_local(audio_file, model_size, language, speaker_diarization)
    
    # 第三步：生成带时间戳的转录稿（在当前目录）
    transcript_file = generate_transcript(result, output_file=str(transcript_file))
    
    return transcript_file

def main():
    print("=" * 70)
    print("🎬 视频/音频智能获取工具")
    print("   先搜索网上文稿 → 找到展示 → 询问是否转录")
    print("=" * 70)
    
    if len(sys.argv) < 2:
        print("\n用法: python3 quick_transcribe.py <视频链接或本地文件路径>")
        print("\n示例:")
        print("  python3 quick_transcribe.py https://www.bilibili.com/video/BV1Z9QABeEgf")
        print("  python3 quick_transcribe.py /path/to/video.mp3 --speaker")
        print("\n可选参数:")
        print("  --skip-search - 直接转录，不搜索文稿")
        print("  --zh, --cn    - 指定为中文")
        print("  --ja, --jp    - 指定为日语")
        print("  --en, --eng   - 指定为英语")
        print("  --speaker, --diarize - 启用说话者识别（区分不同说话者）")
        print("  --tiny        - 最快，但准确率最低（约 32MB）")
        print("  --base        - 推荐日常使用（约 150MB，默认）")
        print("  --small       - 更准确，但更慢（约 500MB）")
        print("  --medium      - 非常准确，但很慢（约 1.5GB）")
        sys.exit(1)
    
    # 解析参数
    # 找到URL参数（不是以--开头的参数）
    video_url = None
    for arg in sys.argv[1:]:
        if not arg.startswith('--'):
            video_url = arg
            break
    
    if not video_url:
        print("\n❌ 请提供视频链接或本地文件路径！")
        sys.exit(1)
    
    model_size = 'base'
    skip_search = '--skip-search' in sys.argv
    language = None
    speaker_diarization = False
    
    # 语言参数
    if '--zh' in sys.argv or '--cn' in sys.argv or '--chinese' in sys.argv:
        language = 'zh'
    elif '--ja' in sys.argv or '--jp' in sys.argv or '--japanese' in sys.argv:
        language = 'ja'
    elif '--en' in sys.argv or '--eng' in sys.argv or '--english' in sys.argv:
        language = 'en'
    
    # 说话者识别参数
    if '--speaker' in sys.argv or '--diarize' in sys.argv:
        speaker_diarization = True
        print(f"🎙️ 已启用说话者识别")
    
    if '--tiny' in sys.argv:
        model_size = 'tiny'
    elif '--small' in sys.argv:
        model_size = 'small'
    elif '--medium' in sys.argv:
        model_size = 'medium'
    
    # 如果是本地文件，直接转录
    is_url = video_url.startswith('http://') or video_url.startswith('https://')
    
    if not is_url:
        print(f"\n📁 本地文件，直接转录")
        transcript_file = do_transcription(video_url, model_size, language, speaker_diarization)
        print("\n" + "=" * 70)
        print("🎉 全部完成！")
        print(f"📄 转录稿: {transcript_file}")
        print(f"💡 下一步: 打开 transcript.txt 整理格式，然后提供给学习内容分析助手！")
        print("=" * 70)
        return
    
    # 先搜索文稿（除非指定跳过）
    if not skip_search:
        search_result = search_transcript_first(video_url)
        
        if search_result.get('found'):
            print("\n" + "=" * 70)
            print("💬 网上文稿已获取!")
            print("=" * 70)
            print("\n你可以:")
            print("1. 直接使用这个文稿（推荐）")
            print("2. 还是进行转录")
            
            try:
                choice = input("\n请选择 (1 直接使用 / 2 转录，默认 1): ").strip()
                if choice == '2':
                    print("\n🔄 开始转录...")
                    transcript_file = do_transcription(video_url, model_size, language, speaker_diarization)
                    print("\n" + "=" * 70)
                    print("🎉 转录完成！")
                    print(f"📄 转录稿: {transcript_file}")
                    print(f"💡 下一步: 打开 transcript.txt 整理格式，然后提供给学习内容分析助手！")
                    print("=" * 70)
                else:
                    print("\n✅ 使用网上文稿完成!")
                    print(f"📄 文稿文件: {search_result['file']}")
                    print(f"💡 下一步: 打开 transcript.txt 整理格式，然后提供给学习内容分析助手！")
                    print("=" * 70)
            except KeyboardInterrupt:
                print("\n\n已取消，使用网上文稿")
            return
    
    # 直接转录
    print("\n🔄 开始转录...")
    transcript_file = do_transcription(video_url, model_size, language, speaker_diarization)
    print("\n" + "=" * 70)
    print("🎉 全部完成！")
    print(f"📄 转录稿: {transcript_file}")
    print(f"💡 下一步: 打开 transcript.txt 整理格式，然后提供给学习内容分析助手！")
    print("=" * 70)

if __name__ == '__main__':
    main()

