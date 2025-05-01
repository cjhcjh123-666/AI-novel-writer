# AI 小说创作助手

一个基于 Flask 和 SiliconFlow API 的 AI 小说创作助手，可以自动生成连贯的小说章节。

## 功能特点

- 🎯 自动生成连贯的小说章节
- 📝 支持自定义小说标题、类型和大纲
- 📊 实时显示创作进度
- 💾 自动保存小说状态，支持断点续传
- 🎨 美观的现代化用户界面
- 📱 响应式设计，支持移动端访问

## 技术栈

- 后端：Python Flask
- 前端：HTML, CSS, JavaScript
- API：SiliconFlow API (Qwen3-32B 模型)
- 数据存储：本地文件系统

## 安装说明

1. 克隆项目到本地：
```bash
git clone https://github.com/yourusername/ai-novel-writer.git
cd ai-novel-writer
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建 `.env` 文件并添加你的 SiliconFlow API 密钥：
```
SILICONFLOW_API_KEY=your_api_key_here
```

## 使用说明

1. 启动应用：
```bash
python app.py
```

2. 在浏览器中访问：
```
http://localhost:5001
```

3. 使用方法：
   - 填写小说标题、类型和大纲
   - 设置总章节数
   - 点击"开始创作"按钮
   - 系统会自动生成章节并显示进度
   - 可以随时中断，下次打开时会自动继续

## 项目结构

```
ai-novel-writer/
├── app.py              # Flask 应用主文件
├── requirements.txt    # 项目依赖
├── .env               # 环境变量配置
├── static/
│   └── style.css      # 样式文件
├── templates/
│   └── index.html     # 前端模板
└── novels/            # 生成的小说存储目录
```

## 注意事项

- 需要有效的 SiliconFlow API 密钥
- 建议在生成大量章节时保持网络连接稳定
- 生成的小说内容会保存在 `novels` 目录下

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进项目！

## 许可证

MIT License

## 联系方式

如有任何问题或建议，欢迎联系：
- GitHub: [cjhcjh123-666]((https://github.com/cjhcjh123-666))
- Email: 551512053@qq.com
