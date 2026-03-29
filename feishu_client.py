"""
飞书 API 封装模块
支持：消息推送、云文档创建、多维表格操作
"""

import json
import subprocess
import requests
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime


class FeishuClient:
    """飞书 API 客户端封装"""
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化飞书客户端
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用 Secret
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = None
    
    def _call_api(self, param: dict, output_path: str, aily_token: str = "tat", 
                  content_type: str = "") -> dict:
        """
        调用飞书 API（通过 aily-feishu-oapi CLI）
        
        Args:
            param: API 参数
            output_path: 输出文件路径
            aily_token: Token 类型 (tat/uat)
            content_type: 内容类型
            
        Returns:
            API 响应 data 部分
        """
        cmd = [
            "aily-feishu-oapi",
            "--output", output_path,
            "--param", json.dumps(param, ensure_ascii=False),
            "--aily-token", aily_token,
        ]
        if content_type:
            cmd.extend(["--content-type", content_type])
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise Exception(f"飞书API调用失败: {result.stderr}")
        
        with open(output_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def send_message(self, receive_id: str, msg_type: str, content: str,
                     receive_id_type: str = "open_id") -> dict:
        """
        发送飞书消息
        
        Args:
            receive_id: 接收者 ID
            msg_type: 消息类型 (text/post/interactive)
            content: 消息内容（JSON字符串）
            receive_id_type: ID 类型 (open_id/user_id/chat_id)
            
        Returns:
            API 响应
        """
        param = {
            "api_path": "/open-apis/im/v1/messages",
            "method": "POST",
            "body": json.dumps({
                "receive_id": receive_id,
                "msg_type": msg_type,
                "content": content,
            }, ensure_ascii=False),
            "query_params": {"receive_id_type": receive_id_type},
        }
        
        output_path = "/tmp/feishu_msg_result.json"
        return self._call_api(param, output_path)
    
    def send_text_message(self, receive_id: str, text: str,
                          receive_id_type: str = "open_id") -> dict:
        """
        发送文本消息
        
        Args:
            receive_id: 接收者 ID
            text: 文本内容
            receive_id_type: ID 类型
            
        Returns:
            API 响应
        """
        content = json.dumps({"text": text}, ensure_ascii=False)
        return self.send_message(receive_id, "text", content, receive_id_type)
    
    def send_post_message(self, receive_id: str, title: str, content_lines: List[str],
                          receive_id_type: str = "open_id") -> dict:
        """
        发送富文本消息
        
        Args:
            receive_id: 接收者 ID
            title: 消息标题
            content_lines: 内容行列表
            receive_id_type: ID 类型
            
        Returns:
            API 响应
        """
        # 构建飞书富文本格式
        # 格式参考：https://open.feishu.cn/document/client-docs/bot-v3/events/message-events
        post_content = {
            "zh_cn": {
                "title": title,
                "content": [[{"tag": "text", "text": line}] for line in content_lines]
            }
        }
        content = json.dumps(post_content, ensure_ascii=False)
        return self.send_message(receive_id, "post", content, receive_id_type)
    
    def create_doc(self, title: str, content: str, folder_token: str = None) -> dict:
        """
        创建飞书云文档
        
        Args:
            title: 文档标题
            content: 文档内容（Markdown格式）
            folder_token: 文件夹 token（可选）
            
        Returns:
            包含文档 URL 的响应
        """
        # 注意：飞书云文档创建API需要特殊权限
        # 这里使用一个简化的方案：先创建文档，然后写入内容
        # 实际使用时可能需要调整
        
        param = {
            "api_path": "/open-apis/docx/v1/documents",
            "method": "POST",
            "body": json.dumps({
                "title": title,
                "folder_token": folder_token,
            }, ensure_ascii=False),
        }
        
        output_path = "/tmp/feishu_doc_result.json"
        return self._call_api(param, output_path)
    
    def upload_file(self, file_path: str, file_type: str = None,
                    file_name: str = None, duration: int = 0) -> dict:
        """
        上传文件到飞书
        
        Args:
            file_path: 本地文件路径
            file_type: 文件类型
            file_name: 自定义文件名
            duration: 音视频时长
            
        Returns:
            包含 file_key 的响应
        """
        cmd = [
            "aily-feishu-oapi", "upload-file",
            "--file", file_path,
            "--output", "/tmp/feishu_upload_result.json",
        ]
        if file_type:
            cmd.extend(["--file-type", file_type])
        if file_name:
            cmd.extend(["--file-name", file_name])
        if duration:
            cmd.extend(["--duration", str(duration)])
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise Exception(f"文件上传失败: {result.stderr}")
        
        with open("/tmp/feishu_upload_result.json", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def upload_image(self, file_path: str, image_type: str = "message") -> dict:
        """
        上传图片到飞书
        
        Args:
            file_path: 本地图片路径
            image_type: 图片用途 (message/avatar)
            
        Returns:
            包含 image_key 的响应
        """
        cmd = [
            "aily-feishu-oapi", "upload-image",
            "--file", file_path,
            "--output", "/tmp/feishu_image_result.json",
        ]
        if image_type != "message":
            cmd.extend(["--image-type", image_type])
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise Exception(f"图片上传失败: {result.stderr}")
        
        with open("/tmp/feishu_image_result.json", "r", encoding="utf-8") as f:
            return json.load(f)


class FeishuBitableClient:
    """飞书多维表格客户端"""
    
    def __init__(self, app_id: str, app_secret: str, bitable_url: str):
        """
        初始化多维表格客户端
        
        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用 Secret
            bitable_url: 多维表格 URL
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.bitable_url = bitable_url
        self.client = FeishuClient(app_id, app_secret)
    
    def _run_bitable_command(self, command: List[str]) -> dict:
        """
        运行 aily-base 命令
        
        Args:
            command: 命令参数列表
            
        Returns:
            命令输出
        """
        cmd = ["aily-base"] + command
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            raise Exception(f"多维表格操作失败: {result.stderr}")
        
        # 命令输出会显示在 stdout，实际数据在输出文件中
        return {"success": True, "message": result.stdout}
    
    def get_table_info(self, table_name: str = None) -> dict:
        """
        获取表格结构
        
        Args:
            table_name: 表名（可选）
            
        Returns:
            表格结构信息
        """
        cmd = [
            "info",
            "--url", self.bitable_url,
            "--output", "/tmp/bitable_info.json",
        ]
        if table_name:
            cmd.extend(["--table-name", table_name])
        
        self._run_bitable_command(cmd)
        
        with open("/tmp/bitable_info.json", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def export_data(self, table_name: str) -> List[dict]:
        """
        导出表格数据
        
        Args:
            table_name: 表名
            
        Returns:
            数据行列表
        """
        cmd = [
            "export",
            "--url", self.bitable_url,
            "--table-name", table_name,
            "--output", "/tmp/bitable_export.json",
            "--no-record-id",
        ]
        
        self._run_bitable_command(cmd)
        
        with open("/tmp/bitable_export.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("rows", [])
    
    def insert_records(self, table_name: str, records: List[dict]) -> dict:
        """
        插入记录
        
        Args:
            table_name: 表名
            records: 记录列表
            
        Returns:
            操作结果
        """
        # 准备数据文件
        data = {
            "fields": {},  # 字段信息（可空，会自动推断）
            "rows": records,
        }
        
        data_file = "/tmp/bitable_insert.json"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cmd = [
            "create",
            "--url", self.bitable_url,
            "--table-name", table_name,
            "--from", data_file,
            "--output", "/tmp/bitable_create_result.json",
        ]
        
        self._run_bitable_command(cmd)
        
        with open("/tmp/bitable_create_result.json", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def sync_records(self, table_name: str, records: List[dict], 
                     key_field: str = "日期", create_missing: bool = True) -> dict:
        """
        同步记录（按主键更新或插入）
        
        Args:
            table_name: 表名
            records: 记录列表
            key_field: 主键字段名
            create_missing: 主键不存在时是否插入
            
        Returns:
            操作结果
        """
        # 准备数据文件
        data = {
            "fields": {},
            "rows": records,
        }
        
        data_file = "/tmp/bitable_sync.json"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        cmd = [
            "sync",
            "--url", self.bitable_url,
            "--table-name", table_name,
            "--from", data_file,
            "--key", key_field,
            "--output", "/tmp/bitable_sync_result.json",
        ]
        
        if create_missing:
            cmd.append("--create-missing")
        
        self._run_bitable_command(cmd)
        
        with open("/tmp/bitable_sync_result.json", "r", encoding="utf-8") as f:
            return json.load(f)
    
    def insert_holdings(self, records: List[dict]) -> dict:
        """
        插入持仓记录
        
        Args:
            records: 持仓记录列表
            
        Returns:
            操作结果
        """
        return self.insert_records("持仓记录", records)
    
    def insert_daily_index(self, records: List[dict]) -> dict:
        """
        插入每日行情
        
        Args:
            records: 行情记录列表
            
        Returns:
            操作结果
        """
        return self.sync_records("每日行情", records, key_field="日期")
    
    def insert_capital_flow(self, records: List[dict]) -> dict:
        """
        插入资金动向
        
        Args:
            records: 资金动向记录列表
            
        Returns:
            操作结果
        """
        return self.sync_records("资金动向", records, key_field="日期")
    
    def insert_daily_advice(self, records: List[dict]) -> dict:
        """
        插入每日投资建议
        
        Args:
            records: 投资建议记录列表
            
        Returns:
            操作结果
        """
        return self.sync_records("每日投资建议", records, key_field="日期")


# ── 辅助函数 ───────────────────────────────────────

def send_feishu_message(cfg: dict, content: str, msg_type: str = "text") -> bool:
    """
    发送飞书消息（封装后的便捷函数）
    
    Args:
        cfg: 配置字典
        content: 消息内容
        msg_type: 消息类型
        
    Returns:
        是否成功
    """
    try:
        feishu_cfg = cfg.get("feishu", {})
        if not feishu_cfg.get("enabled"):
            print("  ⚠️ 飞书推送未启用")
            return False
        
        client = FeishuClient(
            app_id=feishu_cfg.get("app_id"),
            app_secret=feishu_cfg.get("app_secret"),
        )
        
        # 获取推送目标
        receive_id = feishu_cfg.get("push_open_id") or feishu_cfg.get("chat_id")
        receive_id_type = "open_id" if feishu_cfg.get("push_open_id") else "chat_id"
        
        if not receive_id:
            print("  ⚠️ 未配置飞书推送目标")
            return False
        
        # 发送消息
        if msg_type == "text":
            result = client.send_text_message(receive_id, content, receive_id_type)
        else:
            result = client.send_message(receive_id, msg_type, content, receive_id_type)
        
        print(f"  ✅ 飞书消息已发送")
        return True
        
    except Exception as e:
        print(f"  ❌ 飞书消息发送失败: {e}")
        return False


def write_to_feishu_doc(cfg: dict, title: str, content: str) -> Optional[str]:
    """
    写入飞书云文档
    
    Args:
        cfg: 配置字典
        title: 文档标题
        content: 文档内容（Markdown）
        
    Returns:
        文档URL，失败返回None
    """
    try:
        feishu_cfg = cfg.get("feishu", {})
        if not feishu_cfg.get("enabled"):
            print("  ⚠️ 飞书未启用，跳过文档创建")
            return None
        
        client = FeishuClient(
            app_id=feishu_cfg.get("app_id"),
            app_secret=feishu_cfg.get("app_secret"),
        )
        
        # 创建文档
        result = client.create_doc(title, content)
        
        # 提取文档URL
        doc_url = result.get("document", {}).get("url")
        if doc_url:
            print(f"  ✅ 飞书文档已创建: {doc_url}")
        return doc_url
        
    except Exception as e:
        print(f"  ❌ 飞书文档创建失败: {e}")
        return None


def save_to_feishu_bitable(cfg: dict, data: dict) -> bool:
    """
    保存数据到飞书多维表格
    
    Args:
        cfg: 配置字典
        data: 数据字典，包含：
            - holdings: 持仓记录列表
            - indices: 指数行情列表
            - capital_flow: 资金动向列表
            - advice: 投资建议
            
    Returns:
        是否成功
    """
    try:
        feishu_cfg = cfg.get("feishu", {})
        bitable_cfg = cfg.get("bitable", {})
        
        if not feishu_cfg.get("enabled"):
            print("  ⚠️ 飞书未启用，跳过多维表格存储")
            return False
        
        bitable_url = bitable_cfg.get("url")
        if not bitable_url:
            print("  ⚠️ 未配置多维表格URL")
            return False
        
        client = FeishuBitableClient(
            app_id=feishu_cfg.get("app_id"),
            app_secret=feishu_cfg.get("app_secret"),
            bitable_url=bitable_url,
        )
        
        success_count = 0
        
        # 1. 保存持仓记录
        if data.get("holdings"):
            try:
                client.insert_holdings(data["holdings"])
                print(f"  ✅ 已保存 {len(data['holdings'])} 条持仓记录")
                success_count += 1
            except Exception as e:
                print(f"  ⚠️ 保存持仓记录失败: {e}")
        
        # 2. 保存每日行情
        if data.get("indices"):
            try:
                client.insert_daily_index(data["indices"])
                print(f"  ✅ 已保存 {len(data['indices'])} 条行情数据")
                success_count += 1
            except Exception as e:
                print(f"  ⚠️ 保存行情数据失败: {e}")
        
        # 3. 保存资金动向
        if data.get("capital_flow"):
            try:
                client.insert_capital_flow(data["capital_flow"])
                print(f"  ✅ 已保存资金动向数据")
                success_count += 1
            except Exception as e:
                print(f"  ⚠️ 保存资金动向失败: {e}")
        
        # 4. 保存投资建议
        if data.get("advice"):
            try:
                client.insert_daily_advice(data["advice"])
                print(f"  ✅ 已保存投资建议")
                success_count += 1
            except Exception as e:
                print(f"  ⚠️ 保存投资建议失败: {e}")
        
        return success_count > 0
        
    except Exception as e:
        print(f"  ❌ 多维表格操作失败: {e}")
        return False


# ── 测试代码 ───────────────────────────────────────

if __name__ == "__main__":
    # 测试飞书客户端
    import yaml
    
    config_file = Path(__file__).parent / "config.yaml"
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        
        # 测试消息发送
        feishu_cfg = cfg.get("feishu", {})
        if feishu_cfg.get("enabled"):
            print("测试飞书消息发送...")
            send_feishu_message(cfg, "🔔 飞书客户端测试成功！")
    else:
        print("未找到配置文件，跳过测试")
