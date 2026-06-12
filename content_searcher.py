#!/usr/bin/env python3
"""
智能文稿搜索工具
先搜索网上是否有现成文稿，再问是否需要转录
"""

import sys
import re
import requests
from pathlib import Path
from urllib.parse import urlparse, quote_plus
from bs4 import BeautifulSoup

def extract_video_info(url):
    """从URL中提取视频标题等信息"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = ''
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        return {'title': title, 'url': url}
    except Exception as e:
        print(f"⚠️ 提取视频信息失败: {e}")
        return {'title': '', 'url': url}

def search_web_transcript(title, url):
    """在网上搜索文稿"""
    print(f"\n🔍 正在搜索网上文稿...")
    print(f"   标题: {title if title else '未知'}")
    
    search_keywords = []
    
    if title:
        clean_title = re.sub(r'[-|].*$', '', title).strip()
        search_keywords.append(f"{clean_title} 文字稿")
        search_keywords.append(f"{clean_title} 文稿")
        search_keywords.append(f"{clean_title} transcript")
    
    search_keywords.append(f"{url} 文字稿")
    search_keywords.append(f"{url} 文稿")
    
    results = []
    
    for keyword in search_keywords[:3]:
        try:
            search_url = f"https://www.baidu.com/s?wd={quote_plus(keyword)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(search_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for result in soup.find_all('div', class_='result')[:3]:
                try:
                    link = result.find('a')
                    if link and link.get('href'):
                        title_text = link.get_text().strip()
                        href = link.get('href')
                        if title_text and href:
                            results.append({
                                'title': title_text,
                                'url': href,
                                'keyword': keyword
                            })
                except:
                    pass
                    
            if len(results) >= 5:
                break
        except Exception as e:
            print(f"   搜索 '{keyword}' 失败: {e}")
            continue
    
    return results

def extract_content_from_url(url):
    """尝试从URL中提取文稿内容"""
    try:
        print(f"📥 尝试获取内容: {url[:50]}...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        if len(content) > 500:
            return content
        
        return None
    except Exception as e:
        print(f"   获取失败: {e}")
        return None

def format_transcript_with_timestamps(content):
    """将文稿格式化为带时间戳的格式"""
    if not content:
        return None
    
    lines = content.split('\n')
    
    formatted = []
    time_counter = 0
    
    for line in lines:
        if line.strip():
            minutes = time_counter // 60
            seconds = time_counter % 60
            hours = minutes // 60
            minutes = minutes % 60
            
            timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            formatted.append(f"{timestamp} - {line.strip()}")
            
            time_counter += max(10, len(line) // 20)
    
    if formatted:
        return '\n'.join(formatted)
    
    return None

def save_transcript(content, output_dir='.'):
    """保存文稿"""
    output_path = Path(output_dir) / 'transcript.txt'
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 文稿已保存: {output_path}")
    return str(output_path)

def main():
    print("=" * 70)
    print("🔍 智能文稿搜索工具")
    print("=" * 70)
    
    if len(sys.argv) < 2:
        print("\n用法: python3 content_searcher.py <视频链接>")
        print("示例: python3 content_searcher.py https://www.bilibili.com/video/BV1Z9QABeEgf")
        sys.exit(1)
    
    url = sys.argv[1]
    current_dir = Path.cwd()
    
    print(f"\n📹 分析链接: {url}")
    
    video_info = extract_video_info(url)
    
    search_results = search_web_transcript(video_info['title'], video_info['url'])
    
    if search_results:
        print(f"\n✅ 找到 {len(search_results)} 个可能的文稿来源:")
        print("-" * 70)
        for i, result in enumerate(search_results, 1):
            print(f"{i}. {result['title'][:60]}...")
            print(f"   {result['url'][:60]}...")
            print()
        
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
                output_file = save_transcript(formatted, current_dir)
                
                print("\n" + "=" * 70)
                print("✅ 文稿准备就绪!")
                print(f"📄 文件: {output_file}")
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
    
    print("\n💡 建议: 使用转录功能获取文稿")
    return {
        'found': False,
        'message': '未找到现成文稿，请使用转录功能'
    }

if __name__ == '__main__':
    result = main()
    if result and not result.get('found'):
        sys.exit(1)

