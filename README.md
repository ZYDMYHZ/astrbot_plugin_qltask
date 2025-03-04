# 青龙面板任务管理插件

## 功能
- 查看环境变量列表
- 查看定时任务列表
- 执行指定的定时任务
- 查看任务执行日志

## 安装
1. 将插件文件夹复制到 `data/plugins` 目录下

## 配置说明
1. 在青龙面板中创建应用
   - 打开青龙面板
   - 进入 "系统设置" -> "应用设置"
   - 点击 "创建应用"
   - 记录生成的 Client ID 和 Client Secret

2. 修改配置文件
   - url: 青龙面板的访问地址
   - client_id: 应用的 Client ID
   - client_secret: 应用的 Client Secret

## 使用方法
- `/qltask help` - 显示帮助信息
- `/qltask envs` - 查看环境变量列表
- `/qltask ls [页码]` - 查看定时任务列表
- `/qltask run <任务ID>` - 执行指定的定时任务
- `/qltask log <任务ID>` - 查看指定任务的日志

## 注意事项
- 确保青龙面板可以正常访问
- 配置的应用需要有相应的权限