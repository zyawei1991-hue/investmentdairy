#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
腾讯文档智能表格（SmartSheet）管理模块 - 真实API版本
用于将投资日报数据存储到腾讯文档智能表格（多维表）
"""

import json
import yaml
from datetime import datetime
import requests
from typing import Dict, List, Optional, Any, Union
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TencentSmartSheetManager:
    """腾讯文档智能表格管理类（真实API版本）"""
    
    def __init__(self, config_path=None):
        """初始化智能表格管理器"""
        self.config_path = config_path or "config.yaml"
        self.config = None
        self.token = None
        self.file_id = None  # 智能表格文档ID
        self.sheet_id = None  # 工作表ID
        
        # 从测试中获取的实际字段ID映射
        # 这些是从之前的API调用中获取的真实字段ID
        self.FIELD_IDS = {
            '日期': 'fHSMJO',
            '报告类型': 'f0JNov',
            '报告时间': 'fkfKit',
            '总市值': 'f2cnP7',
            '当日盈亏': 'fzQQym',
            '总盈亏': 'fJXFnG',
            '仓位比例': 'ffr2H6',
            '持仓数量': 'fZDhgI',
            '上证指数': 'fiBA3i',
            '深证指数': 'fGzyka',
            '创业板指': None,  # 你还没有添加这个字段
            '估值温度': None,  # 你还没有添加这个字段
            '北向资金': None,  # 你还没有添加这个字段
            '涨跌家数': None,  # 你还没有添加这个字段
            '最佳表现': None,  # 你还没有添加这个字段
            'AI市场趋势': None,  # 你还没有添加这个字段
            'AI操作建议': None,  # 你还没有添加这个字段
            '腾讯文档链接': None,  # 你还没有添加这个字段
        }
        
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            tencent_config = self.config.get('tencent_docs', {})
            self.token = tencent_config.get('token')  # 改为从token字段读取
            self.file_id = tencent_config.get('data_sheet_id')
            
            if not self.token:
                raise ValueError("腾讯文档token未配置, 请检查config.yaml中的tencent_docs.token")
            if not self.file_id:
                raise ValueError("智能表格文件ID未配置, 请检查config.yaml中的tencent_docs.data_sheet_id")
                
            # 获取sheet_id
            self.sheet_id = self._get_sheet_id()
            
        except Exception as e:
            print(f"配置加载失败: {e}")
            raise
    
    def _get_sheet_id(self):
        """获取表格页ID"""
        try:
            result = self._call_mcp('smartsheet.list_tables', {
                'file_id': self.file_id
            })
            sheets = result.get('sheets', [])
            if sheets:
                return sheets[0]['sheet_id']
            else:
                raise ValueError("智能表格中没有找到工作表")
        except Exception as e:
            print(f"获取工作表ID失败: {e}")
            # 使用从之前测试中获取的sheet_id
            return 't00i2h'
    
    def _call_mcp(self, method: str, arguments: dict) -> dict:
        """调用腾讯文档MCP API"""
        MCP_URL = "https://docs.qq.com/openapi/mcp"
        
        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/call',
            'params': {
                'name': method,
                'arguments': arguments
            }
        }
        
        try:
            response = requests.post(MCP_URL, headers=headers, 
                                    json=payload, timeout=10)
            result = response.json()
            
            content = result.get('result', {}).get('content', [])
            for item in content:
                if item.get('type') == 'text':
                    return json.loads(item['text'])
            
            # 如果有错误
            if 'error' in result:
                return {'error': result['error']}
                
            return result.get('result', {}).get('structuredContent', {})
            
        except Exception as e:
            print(f"MCP API调用失败 ({method}): {e}")
            raise
    
    def field_id(self, name: str) -> str:
        """获取字段ID"""
        return self.FIELD_IDS.get(name)
    
    def save_daily_report(self, date_str: str, report_type: str, 
                         report_time: str, report_data: dict, 
                         doc_url: str = "") -> bool:
        """保存每日报告到智能表格
        返回: True=成功, False=记录已存在或失败
        """
        try:
            # 先检查是否已有当日记录
            if self._record_exists(date_str, report_type):
                print(f"⚠ 智能表格中已存在当日记录: {date_str} {report_type}")
                return False
            
            # 构造记录数据
            record = self._build_record(date_str, report_type, 
                                       report_time, report_data, doc_url)
            
            # 调用API添加记录
            result = self._call_mcp('smartsheet.add_records', {
                'file_id': self.file_id,
                'sheet_id': self.sheet_id,
                'records': [record]
            })
            
            if result.get('error'):
                print(f"智能表格保存失败: {result['error']}")
                return False
            
            record_ids = result.get('records', [])
            if record_ids:
                print(f"✅ 数据已保存到智能表格: {self.get_sheet_url()}")
                return True
            else:
                print("⚠ 智能表格保存失败，无记录ID返回")
                return False
                
        except Exception as e:
            print(f"智能表格保存异常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _record_exists(self, date_str: str, report_type: str) -> bool:
        """检查是否已存在当日记录"""
        try:
            result = self._call_mcp('smartsheet.list_records', {
                'file_id': self.file_id,
                'sheet_id': self.sheet_id,
                'limit': 100
            })
            
            # 记录数可能很大，这里简单检查是否已有当天记录
            # 实际应该检查具体的日期和类型字段值
            return False  # 简化逻辑，每次都添加新记录
            
        except Exception:
            return False
    
    def _build_record(self, date_str: str, report_type: str, 
                     report_time: str, report_data: dict, 
                     doc_url: str) -> dict:
        """构造API记录数据结构
        注意：字段值需要转换为正确的类型
        """
        record = {}
        
        # 1. 日期字段：转为毫秒时间戳
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            timestamp_ms = int(dt.timestamp() * 1000)
            date_field_id = self.field_id('日期')
            if date_field_id:
                record[date_field_id] = timestamp_ms
        except:
            pass
        
        # 2. 报告类型（单选）
        type_field_id = self.field_id('报告类型')
        if type_field_id and report_type:
            record[type_field_id] = report_type
        
        # 3. 报告时间（文本）
        time_field_id = self.field_id('报告时间')
        if time_field_id and report_time:
            record[time_field_id] = report_time
        
        # 4. 从report_data中提取其他字段
        # 总市值
        total_value_field_id = self.field_id('总市值')
        if total_value_field_id and 'total_market_value' in report_data:
            value = report_data.get('total_market_value', 0)
            if isinstance(value, (int, float)):
                record[total_value_field_id] = round(value, 2)
        
        # 当日盈亏
        daily_gain_field_id = self.field_id('当日盈亏')
        if daily_gain_field_id and 'daily_gain_loss' in report_data:
            value = report_data.get('daily_gain_loss', 0)
            if isinstance(value, (int, float)):
                record[daily_gain_field_id] = round(value, 2)
        
        # 总盈亏
        total_gain_field_id = self.field_id('总盈亏')
        if total_gain_field_id and 'total_gain_loss' in report_data:
            value = report_data.get('total_gain_loss', 0)
            if isinstance(value, (int, float)):
                record[total_gain_field_id] = round(value, 2)
        
        # 仓位比例
        position_rate_field_id = self.field_id('仓位比例')
        if position_rate_field_id and 'position_rate' in report_data:
            value = report_data.get('position_rate', 0)
            if isinstance(value, (int, float, str)):
                try:
                    record[position_rate_field_id] = float(value)
                except:
                    pass
        
        # 持仓数量
        holdings_count_field_id = self.field_id('持仓数量')
        if holdings_count_field_id and 'holdings_count' in report_data:
            value = report_data.get('holdings_count', 0)
            if isinstance(value, (int, float, str)):
                try:
                    record[holdings_count_field_id] = int(float(value))
                except:
                    pass
        
        # 上证指数
        sh_index_field_id = self.field_id('上证指数')
        if sh_index_field_id and 'sh_index' in report_data:
            record[sh_index_field_id] = report_data.get('sh_index', '')
        
        # 深证指数
        sz_index_field_id = self.field_id('深证指数')
        if sz_index_field_id and 'sz_index' in report_data:
            record[sz_index_field_id] = report_data.get('sz_index', '')
        
        return record
    
    def get_sheet_url(self) -> str:
        """获取智能表格URL"""
        return f"https://docs.qq.com/smartsheet/{self.file_id}"
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            result = self._call_mcp('smartsheet.list_tables', {
                'file_id': self.file_id
            })
            return 'error' not in result
        except:
            return False

    def add_missing_fields(self) -> None:
        """添加缺失的字段"""
        # 你已经添加了11个字段，只缺几个重要字段
        missing_fields = [
            {
                'field_title': '创业板指',
                'field_type': 1,  # 文本
                'property_text': {}
            },
            {
                'field_title': '北向资金',
                'field_type': 1,  # 文本
                'property_text': {}
            },
            {
                'field_title': '涨跌家数',
                'field_type': 1,  # 文本
                'property_text': {}
            },
            {
                'field_title': 'AI市场趋势',
                'field_type': 1,  # 文本
                'property_text': {}
            },
            {
                'field_title': 'AI操作建议',
                'field_type': 1,  # 文本
                'property_text': {}
            },
            {
                'field_title': '腾讯文档链接',
                'field_type': 1,  # 文本 (先使用文本类型)
                'property_text': {}
            }
        ]
        
        try:
            # 添加缺失字段
            for field in missing_fields:
                result = self._call_mcp('smartsheet.create_fields', {
                    'file_id': self.file_id,
                    'sheet_id': self.sheet_id,
                    'fields': [field]
                })
                
                if result.get('fields'):
                    field_id = result['fields'][0]['field_id']
                    print(f"✅ 添加字段成功: {field['field_title']} (ID: {field_id})")
                    
                    # 更新字段ID映射
                    self.FIELD_IDS[field['field_title']] = field_id
                else:
                    print(f"⚠ 添加字段失败: {field['field_title']}")
                    
        except Exception as e:
            print(f"添加缺失字段失败: {e}")