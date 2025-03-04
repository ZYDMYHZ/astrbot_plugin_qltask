from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.star.filter.permission import PermissionType
import aiohttp
import json
from typing import Optional

@register("qltask", "ZYDMYHZ", "青龙面板任务管理插件", "0.0.2", "https://github.com/ZYDMYHZ/astrbot_plugin_qltask")
class MyPlugin(Star):
    def __init__(self, context: Context, config: dict):
        super().__init__(context)
        self.config = config
        self.base_url = config.get('url', '').rstrip('/')
        self.client_id = config.get('client_id', '')
        self.client_secret = config.get('client_secret', '')
        self.token = None
        
        if not all([self.base_url, self.client_id, self.client_secret]):
            logger.error("请在配置文件中设置青龙面板的 url、client_id 和 client_secret")   

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("qltask help")
    async def help(self, event: AstrMessageEvent):
        '''显示帮助信息'''
        help_info = {
            "name": "青龙面板任务管理插件",
            "commands": {
                "/qltask help": "显示此帮助信息",
                "/qltask envs": "查看环境变量列表",
                "/qltask ls": "查看定时任务列表",
                "/qltask run <任务ID>": "执行指定的定时任务",
                "/qltask log <任务ID>": "查看指定任务的日志"
            }
        }

        # 格式化输出
        # result = f"=== {help_info['name']} v{help_info['version']} ===\n\n"
        result = "可用命令：\n"
        for cmd, desc in help_info['commands'].items():
            result += f"{cmd:<20} {desc}\n"
        # result += f"\nGitHub: {help_info['github']}"

        yield event.plain_result(result)
            
    async def get_token(self) -> Optional[str]:
        """获取青龙面板 API token"""
        if self.token:
            return self.token
            
        url = f"{self.base_url}/open/auth/token"
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 200:
                            self.token = result['data']['token']
                            logger.info(f"获取 token 成功: {self.token}")
                            return self.token
                    logger.error(f"获取 token 失败: {await response.text()}")
        except Exception as e:
            logger.error(f"获取 token 异常: {str(e)}")
        return None
        
    async def get_envs(self) -> Optional[list]:
        """获取青龙面板环境变量列表"""
        token = await self.get_token()
        if not token:
            return None
            
        url = f"{self.base_url}/open/envs"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 200:
                            return result.get('data', [])
                    logger.error(f"获取环境变量失败: {await response.text()}")
        except Exception as e:
            logger.error(f"获取环境变量异常: {str(e)}")
        return None

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("qltask envs")
    async def list_envs(self, event: AstrMessageEvent):
        '''查看环境变量列表'''
        envs = await self.get_envs()
        if not envs:
            yield event.plain_result("获取环境变量失败，请检查配置和网络连接")
            return
            
        if len(envs) == 0:
            yield event.plain_result("环境变量列表为空")
            return
            
        result = "=== 青龙面板环境变量列表 ===\n\n"
        for env in envs:
            name = env.get('name', '未命名')
            value = env.get('value', '')
            # 对敏感信息进行脱敏处理
            if len(value) > 6:
                value = value[:3] + '****' + value[-3:]
            elif len(value) > 0:
                value = '****'
                
            status = "启用" if env.get('status') == 0 else "禁用"
            result += f"名称: {name}\n值: {value}\n状态: {status}\n\n"
            
        yield event.plain_result(result)


    async def get_crons(self) -> Optional[list]:
        """获取青龙面板定时任务列表"""
        token = await self.get_token()
        if not token:
            return None
            
        url = f"{self.base_url}/open/crons"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 200:
                            # 直接从 data.data 中获取任务列表
                            data = result.get('data', {})
                            if isinstance(data, dict):
                                return data.get('data', [])
                            return []
                    logger.error(f"获取定时任务列表失败: {await response.text()}")
        except Exception as e:
            logger.error(f"获取定时任务列表异常: {str(e)}")
        return None

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("qltask ls")
    async def list_crons(self, event: AstrMessageEvent):
        '''查看定时任务列表'''
        # 获取页码参数，默认为第1页
        try:
            # 从消息链中获取文本内容
            message_chain = event.message_obj.message
            logger.info(f"消息链: {message_chain}")
            
            # 处理 Plain 类型消息
            text_content = ""
            if message_chain and hasattr(message_chain[0], 'text'):
                text_content = message_chain[0].text.strip()
            
            # 解析页码参数
            args = text_content.replace("qltask ls", "").strip()
            logger.info(f"解析到的参数: {args}")  # 添加日志以便调试
            page = int(args or "1")
            if page < 1:
                page = 1
        except (ValueError, AttributeError) as e:
            logger.error(f"解析页码参数失败: {str(e)}")  # 添加错误日志
            page = 1
            
        crons = await self.get_crons()
        if not crons:
            yield event.plain_result("获取定时任务列表失败，请检查配置和网络连接")
            return
            
        if len(crons) == 0:
            yield event.plain_result("定时任务列表为空")
            return
            
        # 分页处理
        page_size = 5  # 每页显示5个任务
        total_pages = (len(crons) + page_size - 1) // page_size  # 向上取整
        
        if page > total_pages:
            yield event.plain_result(f"页码超出范围，总共只有 {total_pages} 页")
            return
            
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(crons))
        page_crons = crons[start_idx:end_idx]
            
        result = f"=== 青龙面板定时任务列表 (第 {page}/{total_pages} 页) ===\n\n"
        for cron in page_crons:
            name = cron.get('name', '未命名')
            command = cron.get('command', '')
            schedule = cron.get('schedule', '')
            status = "禁用" if cron.get('isDisabled', 0) == 1 else "启用"
            cron_id = cron.get('id', '')
            
            result += f"ID: {cron_id}\n"
            result += f"名称: {name}\n"
            result += f"命令: {command}\n"
            result += f"定时: {schedule}\n"
            result += f"状态: {status}\n"
            result += "-" * 30 + "\n"
            
        result += f"\n使用 /qltask ls <页码> 查看其他页"
        yield event.plain_result(result)
    

    async def get_cron_log(self, cron_id: str) -> Optional[str]:
        """获取青龙面板任务日志"""
        token = await self.get_token()
        if not token:
            return None
            
        url = f"{self.base_url}/open/crons/{cron_id}/log"
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 200:
                            return result.get('data', '')
                    logger.error(f"获取任务日志失败: {await response.text()}")
        except Exception as e:
            logger.error(f"获取任务日志异常: {str(e)}")
        return None

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("qltask log")
    async def show_cron_log(self, event: AstrMessageEvent):
        '''查看指定任务的日志'''
        # 从消息链中获取文本内容
        message_chain = event.message_obj.message
        logger.info(f"消息链: {message_chain}")
        
        # 处理 Plain 类型消息
        text_content = ""
        if message_chain and hasattr(message_chain[0], 'text'):
            text_content = message_chain[0].text.strip()
                
        args = text_content.replace("qltask log", "").strip()
        if not args:
            yield event.plain_result("请提供任务ID，例如：/qltask log 12345")
            return
            
        log_content = await self.get_cron_log(args)
        if log_content is None:
            yield event.plain_result("获取任务日志失败，请检查任务ID是否正确")
            return
            
        if not log_content:
            yield event.plain_result("该任务暂无日志")
            return
            
        # 如果日志内容太长，只显示最后1000个字符
        if len(log_content) > 2000: 
            log_content = "...\n" + log_content[-2000:]
            
        result = f"=== 任务 {args} 的日志 ===\n\n{log_content}"
        yield event.plain_result(result)

    async def run_cron(self, cron_id: str) -> bool:
        """执行指定的定时任务"""
        token = await self.get_token()
        if not token:
            return False
            
        url = f"{self.base_url}/open/crons/run"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        data = [cron_id]  # 需要传入任务ID数组
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('code') == 200:
                            return True
                    logger.error(f"执行任务失败: {await response.text()}")
        except Exception as e:
            logger.error(f"执行任务异常: {str(e)}")
        return False

    @filter.permission_type(PermissionType.ADMIN)
    @filter.command("qltask run")
    async def execute_cron(self, event: AstrMessageEvent):
        '''执行指定的定时任务'''
        # 从消息链中获取文本内容
        message_chain = event.message_obj.message
        logger.info(f"消息链: {message_chain}")
        
        # 处理 Plain 类型消息
        text_content = ""
        if message_chain and hasattr(message_chain[0], 'text'):
            text_content = message_chain[0].text.strip()
                
        args = text_content.replace("qltask run", "").strip()
        if not args:
            yield event.plain_result("请提供任务ID，例如：/qltask run 12345")
            return
            
        success = await self.run_cron(args)
        if success:
            yield event.plain_result(f"任务 {args} 已开始执行，可使用 /qltask log {args} 查看执行日志")
        else:
            yield event.plain_result("执行任务失败，请检查任务ID是否正确")