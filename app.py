from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
import requests
import json
import re
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get API key from environment variable
API_KEY = os.getenv('SILICONFLOW_API_KEY')
API_URL = 'https://api.siliconflow.cn/v1/chat/completions'

# 存储当前小说的信息
current_novel = {
    'title': '',
    'genre': '',
    'outline': '',
    'chapters': [],
    'last_chapter_summary': '',
    'current_chapter': 1,
    'total_chapters': 0,
    'total_words': 0,
    'start_time': None,
    'estimated_completion_time': None
}

def count_chinese_words(text):
    """计算中文文本的字数"""
    # 移除空格和换行符
    text = text.replace(' ', '').replace('\n', '')
    return len(text)

def save_chapter_to_file(chapter_content):
    """保存章节到本地文件"""
    if not current_novel['title']:
        return
    
    # 创建novels目录（如果不存在）
    if not os.path.exists('novels'):
        os.makedirs('novels')
    
    # 生成文件名
    filename = f"novels/{current_novel['title']}.txt"
    
    # 追加写入文件
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(chapter_content + '\n\n')

def generate_chapter_summary(chapter_content):
    """生成章节摘要"""
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    summary_prompt = f"请用100字以内总结以下章节的主要内容：\n{chapter_content}"
    summary_data = {
        "model": "Qwen/Qwen3-32B",
        "messages": [
            {"role": "user", "content": summary_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 200,
        "top_p": 0.7,
        "stream": False
    }
    
    try:
        summary_response = requests.post(API_URL, headers=headers, json=summary_data)
        return summary_response.json()['choices'][0]['message']['content']
    except Exception as e:
        return str(e)

def get_progress_info():
    """获取当前进度信息"""
    total_words = current_novel['total_words']
    chapters_completed = current_novel['current_chapter'] - 1
    total_chapters = current_novel['total_chapters']
    completion_percentage = (chapters_completed / total_chapters) * 100 if total_chapters > 0 else 0
    
    # 计算预计剩余时间
    remaining_time = "计算中..."
    if current_novel['start_time'] and chapters_completed > 0:
        elapsed_time = (datetime.now() - current_novel['start_time']).total_seconds()
        avg_time_per_chapter = elapsed_time / chapters_completed
        remaining_chapters = total_chapters - chapters_completed
        remaining_seconds = avg_time_per_chapter * remaining_chapters
        
        if remaining_seconds < 60:
            remaining_time = f"约{int(remaining_seconds)}秒"
        elif remaining_seconds < 3600:
            remaining_time = f"约{int(remaining_seconds/60)}分钟"
        else:
            remaining_time = f"约{round(remaining_seconds/3600, 1)}小时"

    return {
        'total_words': total_words,
        'chapters_completed': chapters_completed,
        'total_chapters': total_chapters,
        'completion_percentage': round(completion_percentage, 1),
        'remaining_time': remaining_time,
        'avg_words_per_chapter': round(total_words / chapters_completed) if chapters_completed > 0 else 0
    }

def generate_chapter():
    """生成单个章节"""
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 构建系统提示
    system_message = f"你是一个专业的小说家。请写一个{current_novel['genre']}类型的故事。\n"
    system_message += f"小说大纲：{current_novel['outline']}\n"
    if current_novel['last_chapter_summary']:
        system_message += f"上一个章节的剧情是：{current_novel['last_chapter_summary']}\n"
    
    # 构建用户提示
    user_message = f"请生成第{current_novel['current_chapter']}章的内容，要求：\n"
    user_message += "1. 章节标题要简洁有力\n"
    user_message += "2. 内容要连贯，符合故事发展\n"
    user_message += "3. 字数在2000字左右\n"
    user_message += "4. 请根据小说大纲和上一章的内容来发展剧情\n"
    user_message += "请以'第X章 章节标题'的格式开始，然后直接写正文内容。"
    
    data = {
        "model": "Qwen/Qwen3-32B",
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.7,
        "max_tokens": 4096,
        "top_p": 0.7,
        "stream": False
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=data)
        response.raise_for_status()
        chapter_content = response.json()['choices'][0]['message']['content']
        
        # 提取章节标题和内容
        chapter_match = re.match(r'第(\d+)章\s+(.*?)\n(.*)', chapter_content, re.DOTALL)
        if chapter_match:
            chapter_num = chapter_match.group(1)
            chapter_title = chapter_match.group(2)
            chapter_text = chapter_match.group(3)
            
            # 更新当前章节信息
            current_novel['chapters'].append({
                'number': chapter_num,
                'title': chapter_title,
                'content': chapter_text
            })
            
            # 更新总字数
            current_novel['total_words'] += count_chinese_words(chapter_content)
            
            # 保存章节到文件
            save_chapter_to_file(chapter_content)
            
            # 生成章节摘要
            current_novel['last_chapter_summary'] = generate_chapter_summary(chapter_content)
            
            # 更新章节计数
            current_novel['current_chapter'] += 1
            
            # 获取进度信息
            progress_info = get_progress_info()
            
            return {
                'content': chapter_content,
                'progress': progress_info
            }
        else:
            # 如果正则匹配失败，尝试更宽松的匹配
            chapter_match = re.match(r'第(\d+)章\s+(.*?)(?:\n|$)(.*)', chapter_content, re.DOTALL)
            if chapter_match:
                chapter_num = chapter_match.group(1)
                chapter_title = chapter_match.group(2)
                chapter_text = chapter_match.group(3)
                
                # 更新当前章节信息
                current_novel['chapters'].append({
                    'number': chapter_num,
                    'title': chapter_title,
                    'content': chapter_text
                })
                
                # 更新总字数
                current_novel['total_words'] += count_chinese_words(chapter_content)
                
                # 保存章节到文件
                save_chapter_to_file(chapter_content)
                
                # 生成章节摘要
                current_novel['last_chapter_summary'] = generate_chapter_summary(chapter_content)
                
                # 更新章节计数
                current_novel['current_chapter'] += 1
                
                # 获取进度信息
                progress_info = get_progress_info()
                
                return {
                    'content': chapter_content,
                    'progress': progress_info
                }
            else:
                # 如果还是匹配失败，直接使用内容
                current_novel['chapters'].append({
                    'number': str(current_novel['current_chapter']),
                    'title': '未知标题',
                    'content': chapter_content
                })
                
                # 更新总字数
                current_novel['total_words'] += count_chinese_words(chapter_content)
                
                # 保存章节到文件
                save_chapter_to_file(chapter_content)
                
                # 生成章节摘要
                current_novel['last_chapter_summary'] = generate_chapter_summary(chapter_content)
                
                # 更新章节计数
                current_novel['current_chapter'] += 1
                
                # 获取进度信息
                progress_info = get_progress_info()
                
                return {
                    'content': chapter_content,
                    'progress': progress_info
                }
    except Exception as e:
        return {
            'content': str(e),
            'progress': get_progress_info()
        }

def save_novel_state():
    """保存小说状态到文件"""
    if not current_novel['title']:
        return
    
    try:
        # 创建novels目录（如果不存在）
        if not os.path.exists('novels'):
            os.makedirs('novels')
        
        # 生成状态文件名
        state_filename = f"novels/{current_novel['title']}_state.json"
        
        # 只保存必要的信息
        state_to_save = {
            'title': current_novel['title'],
            'genre': current_novel['genre'],
            'outline': current_novel['outline'],
            'chapters': current_novel['chapters'],
            'last_chapter_summary': current_novel['last_chapter_summary'],
            'current_chapter': current_novel['current_chapter'],
            'total_chapters': current_novel['total_chapters'],
            'total_words': current_novel['total_words'],
            'start_time': current_novel['start_time'].isoformat() if current_novel['start_time'] else None
        }
        
        # 保存状态
        with open(state_filename, 'w', encoding='utf-8') as f:
            json.dump(state_to_save, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存小说状态时出错: {str(e)}")

def load_novel_state(title):
    """从文件加载小说状态"""
    state_filename = f"novels/{title}_state.json"
    try:
        if os.path.exists(state_filename):
            with open(state_filename, 'r', encoding='utf-8') as f:
                try:
                    state = json.load(f)
                    # 转换时间字符串为datetime对象
                    if state.get('start_time'):
                        state['start_time'] = datetime.fromisoformat(state['start_time'])
                    return state
                except json.JSONDecodeError:
                    print(f"JSON解析错误，删除损坏的文件: {state_filename}")
                    os.remove(state_filename)
                    return None
    except Exception as e:
        print(f"加载小说状态时出错: {str(e)}")
        return None
    return None

def auto_generate_chapters():
    """自动生成剩余章节"""
    try:
        while current_novel['current_chapter'] <= current_novel['total_chapters']:
            result = generate_chapter()
            if isinstance(result, dict) and 'error' in result:
                return result
            
            # 每生成一章就保存状态
            save_novel_state()
            
            # 返回当前进度
            return {
                'status': 'generating',
                'message': f'正在生成第{current_novel["current_chapter"]}章',
                'chapter': result['content'],
                'progress': result['progress']
            }
            
        return {
            'status': 'complete',
            'message': '小说已完成',
            'progress': get_progress_info()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'生成过程中出错: {str(e)}',
            'progress': get_progress_info()
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_novel', methods=['POST'])
def start_novel():
    data = request.json
    title = data.get('title', '')
    
    # 检查是否已有同名小说
    existing_novel = load_novel_state(title)
    if existing_novel:
        # 恢复已有小说状态
        global current_novel
        current_novel = existing_novel
        return jsonify({
            'status': 'resume',
            'message': f'发现未完成的小说《{title}》，是否继续生成？',
            'progress': get_progress_info()
        })
    
    # 初始化新小说
    current_novel['title'] = title
    current_novel['genre'] = data.get('genre', '')
    current_novel['outline'] = data.get('outline', '')
    current_novel['chapters'] = []
    current_novel['last_chapter_summary'] = ''
    current_novel['current_chapter'] = 1
    current_novel['total_chapters'] = data.get('total_chapters', 10)
    current_novel['total_words'] = 0
    current_novel['start_time'] = datetime.now()
    
    # 保存初始状态
    save_novel_state()
    
    # 开始生成第一章
    result = auto_generate_chapters()
    return jsonify(result)

@app.route('/resume_novel', methods=['POST'])
def resume_novel():
    """继续生成小说"""
    result = auto_generate_chapters()
    return jsonify(result)

@app.route('/get_novel_list', methods=['GET'])
def get_novel_list():
    """获取所有小说列表"""
    if not os.path.exists('novels'):
        return jsonify({'novels': []})
    
    novels = []
    for filename in os.listdir('novels'):
        if filename.endswith('_state.json'):
            title = filename.replace('_state.json', '')
            state_file = f"novels/{filename}"
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                novels.append({
                    'title': title,
                    'genre': state.get('genre', ''),
                    'progress': get_progress_info(),
                    'last_updated': os.path.getmtime(state_file)
                })
    
    return jsonify({'novels': novels})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True) 