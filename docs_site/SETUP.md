# 文档站点设置指南

本指南帮助您快速设置和运行 LLM-Workshop 文档站点。

## 快速开始

### 1. 安装依赖

#### macOS

```bash
# 安装 Ruby (使用 Homebrew)
brew install ruby

# 添加到 PATH (添加到 ~/.zshrc 或 ~/.bash_profile)
echo 'export PATH="/opt/homebrew/opt/ruby/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 安装 Bundler
gem install bundler

# 安装项目依赖
cd docs_site
bundle install
```

#### Linux (Ubuntu/Debian)

```bash
# 安装 Ruby 和开发工具
sudo apt-get update
sudo apt-get install ruby-full build-essential zlib1g-dev

# 配置 gem 安装路径（避免使用 sudo）
echo '# Install Ruby Gems to ~/gems' >> ~/.bashrc
echo 'export GEM_HOME="$HOME/gems"' >> ~/.bashrc
echo 'export PATH="$HOME/gems/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# 安装 Bundler
gem install bundler

# 安装项目依赖
cd docs_site
bundle install
```

#### Windows

```bash
# 下载并安装 Ruby+Devkit from https://rubyinstaller.org/
# 安装过程中选择 "MSYS2 development toolchain"

# 安装 Bundler
gem install bundler

# 安装项目依赖
cd docs_site
bundle install
```

### 2. 本地运行

```bash
# 启动 Jekyll 服务器
cd docs_site
bundle exec jekyll serve

# 或使用实时重载
bundle exec jekyll serve --livereload

# 服务器启动后访问:
# http://localhost:4000/LLM-Workshop
```

### 3. 验证安装

访问 `http://localhost:4000/LLM-Workshop`，您应该能看到：

- ✅ 导航栏正确显示
- ✅ 首页内容完整
- ✅ Chapter 3 文档可访问
- ✅ 搜索功能正常
- ✅ 样式正确渲染

## 目录结构

```
docs_site/
├── _config.yml              # Jekyll 配置
├── Gemfile                  # Ruby 依赖
├── index.md                 # 首页
├── docs/                    # 文档内容
│   ├── chapter1/           # 各章节
│   ├── chapter2/
│   ├── chapter3/           # ✅ 已完成
│   ├── chapter4/           # 🚧 部分完成
│   └── ...
├── assets/                  # 静态资源
│   └── css/
│       └── custom.scss     # 自定义样式
├── _includes/              # 模板片段
│   └── head_custom.html
├── README.md               # 文档站点说明
├── SETUP.md               # 本文件
└── CONTRIBUTING.md        # 贡献指南
```

## 常见问题

### Q1: bundle install 失败？

**解决方案**:

```bash
# 清除缓存
bundle clean --force

# 重新安装
rm Gemfile.lock
bundle install
```

### Q2: Jekyll 启动失败？

**检查**:

```bash
# 检查 Ruby 版本 (需要 3.1+)
ruby --version

# 检查 Bundler 版本
bundle --version

# 查看详细错误信息
bundle exec jekyll serve --trace
```

### Q3: 样式没有加载？

**解决方案**:

1. 清除 Jekyll 缓存：
```bash
bundle exec jekyll clean
```

2. 重新构建：
```bash
bundle exec jekyll build
bundle exec jekyll serve
```

### Q4: 端口被占用？

**解决方案**:

```bash
# 使用不同端口
bundle exec jekyll serve --port 4001
```

## 开发工作流

### 编辑文档

1. 在 `docs/` 目录下编辑 Markdown 文件
2. Jekyll 会自动检测变化并重新构建
3. 刷新浏览器查看更新

### 添加新页面

1. 创建新的 Markdown 文件
2. 添加 YAML front matter
3. 文件会自动出现在导航中

### 修改样式

1. 编辑 `assets/css/custom.scss`
2. Jekyll 会自动编译 SCSS
3. 刷新浏览器查看效果

## 部署到 GitHub Pages

### 自动部署

推送到 `main` 分支会自动触发部署：

```bash
git add docs_site/
git commit -m "docs: 更新文档"
git push origin main
```

GitHub Actions 会自动：
1. 安装依赖
2. 构建站点
3. 部署到 GitHub Pages

### 手动构建测试

```bash
# 构建站点
cd docs_site
bundle exec jekyll build

# 检查生成的文件
ls -la _site/
```

## 性能优化

### 加快构建速度

```bash
# 增量构建
bundle exec jekyll serve --incremental

# 跳过未更改的文件
bundle exec jekyll serve --skip-initial-build
```

### 减少内存占用

在 `_config.yml` 中添加：

```yaml
# 限制 Liquid 渲染
liquid:
  error_mode: strict
  strict_filters: true
  strict_variables: true
```

## 高级配置

### 自定义域名

1. 在 `docs_site/` 下创建 `CNAME` 文件
2. 添加您的域名
3. 在域名提供商处配置 DNS

### 启用 Google Analytics

在 `_config.yml` 中添加：

```yaml
# Google Analytics
google_analytics: UA-XXXXXXXXX-X
```

### 自定义主题颜色

编辑 `assets/css/custom.scss`：

```scss
// 自定义颜色
$btn-primary-color: #007bff;
$link-color: #0366d6;
```

## 参考资源

- [Jekyll 官方文档](https://jekyllrb.com/docs/)
- [just-the-docs 主题文档](https://just-the-docs.github.io/just-the-docs/)
- [GitHub Pages 文档](https://docs.github.com/en/pages)
- [YAML 语法](https://yaml.org/)

## 获取帮助

如遇到问题：

1. 查看本文档的常见问题部分
2. 阅读 `CONTRIBUTING.md` 贡献指南
3. 在 GitHub 创建 Issue
4. 查看 Jekyll 官方文档

---

祝您使用愉快！如有问题欢迎反馈。

