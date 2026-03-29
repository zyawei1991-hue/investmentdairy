#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SmartSheet

"""

import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TencentSmartSheetManager:
    """"""
    
    def __init__(self, config_path=None):
        """"""
        self.config_path = config_path or "config.yaml"
        self.config = None
        self.token = None
        self.file_id = None  # ID
        self.sheet_id = None  # ID
        
        # 
        self.FIELD_DEFINITIONS = [
            # 
            {
                "field_title": "",
                "field_type": 4,  # 
                "property_date_time": {
                    "format": "yyyy-mm-dd",
                    "auto_fill": False
                }
            },
            {
                "field_title": "",
                "field_type": 17,  # 
                "property_single_select": {
                    "options": [
                        {"text": "", "style": 3},  # 
                        {"text": "", "style": 4}   # 
                    ]
                }
            },
            {
                "field_title": "",
                "field_type": 1,  # 
                "property_text": {}
            },
            
            # 
            {
                "field_title": "",
                "field_type": 26,  # 
                "property_number": {
                    "format": "currency",
                    "decimal_places": 2
                }
            },
            {
                "field_title": "",
                "field_type": 26,  # 
                "property_number": {
                    "format": "currency", 
                    "decimal_places": 2
                }
            },
            {
                "field_title": "",
                "field_type": 26,  # 
                "property_number": {
                    "format": "currency",
                    "decimal_places": 2
                }
            },
            {
                "field_title": "",
                "field_type": 28,  # 
                "property_number": {
                    "format": "percent",
                    "decimal_places": 1
                }
            },
            {
                "field_title": "",
                "field_type": 2,  # 
                "property_number": {
                    "format": "number",
                    "decimal_places": 0
                }
            },
            
            # 
            {
                "field_title": "",
                "field_type": 1,  # 
                "property_text": {}
            },
            {
                "field_title": "", 
                "field_type": 1,
                "property_text": {}
            },
            {
                "field_title": "",
                "field_type": 1,
                "property_text": {}
            },
            {
                "field_title": "",
                "field_type": 17,  # 
                "property_single_select": {
                    "options": [
                        {"text": "", "style": 3},     # 
                        {"text": "", "style": 4},     # 
                        {"text": "", "style": 1}      # 
                    ]
                }
            },
            {
                "field_title": "",
                "field_type": 1,  # 
                "property_text": {}
            },
            {
                "field_title": "",
                "field_type": 1,  # 
                "property_text": {}
            },
            
            # AI
            {
                "field_title": "AI",
                "field_type": 1,  # 
                "property_text": {}
            },
            {
                "field_title": "AI",
                "field_type": 1,  # 
                "property_text": {}
            },
            {
                "field_title": "",
                "field_type": 8,  # 
                "property_url": {}
            }
        ]
        
        self.load_config()
    
    def load_config(self):
        """"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            tencent_config = self.config.get("tencent_docs", {})
            self.token = tencent_config.get("token")
            self.file_id = tencent_config.get("data_sheet_id")
            
            if self.token:
                print(f"Token")
            else:
                print(" Token")
                
            if self.file_id:
                print(f"ID: {self.file_id}")
            else:
                print(": ID")
                
        except Exception as e:
            print(f": {e}")
            self.config = {}
            self.token = None
            self.file_id = None
    
    def call_mcp_tool(self, tool_name: str, args: dict) -> Optional[dict]:
        """
        MCP
        
        
        WorkBuddyMCP
        """
        # API
        print(f" MCP: {tool_name}")
        print(f"   : {json.dumps(args, ensure_ascii=False, indent=2)[:200]}...")
        
        # 
        if tool_name == "smartsheet.list_tables":
            return {
                "code": 0,
                "data": {
                    "items": [
                        {
                            "sheet_id": "tbl123456",
                            "title": ""
                        }
                    ]
                }
            }
        elif tool_name == "smartsheet.add_fields":
            return {
                "code": 0,
                "data": {
                    "field_ids": [f"field_{i}" for i in range(len(args.get("fields", [])))]
                }
            }
        elif tool_name == "smartsheet.add_records":
            return {
                "code": 0,
                "data": {
                    "record_ids": [f"record_{i}" for i in range(len(args.get("records", [])))]
                }
            }
        
        return None
    
    def ensure_smart_sheet_exists(self) -> bool:
        """"""
        if not self.token:
            print(" Token")
            return False
        
        # file_id
        if self.file_id:
            print(f": {self.file_id}")
            result = self.call_mcp_tool("smartsheet.list_tables", {
                "file_id": self.file_id
            })
            
            if result and result.get("code") == 0:
                tables = result.get("data", {}).get("items", [])
                if tables:
                    self.sheet_id = tables[0].get("sheet_id")
                    print(f"ID: {self.sheet_id}")
                    return True
            else:
                print(" ")
                
        # 
        print(" ...")
        print(":")
        print("  1.  create_space_node ")
        print("  2.  file_id  sheet_id")
        print("  3.  data_sheet_id")
        
        # :
        # create_space_node(node_type="wiki_tdoc", doc_type="smartsheet", title="")
        
        return False
    
    def ensure_fields_exist(self) -> bool:
        """"""
        if not self.file_id or not self.sheet_id:
            print(" file_idsheet_id")
            return False
        
        print(f"  ({len(self.FIELD_DEFINITIONS)})...")
        
        # :
        # smartsheet.add_fields(file_id, sheet_id, fields=FIELD_DEFINITIONS)
        
        print("API:")
        print(f"  smartsheet.add_fields(file_id='{self.file_id}', sheet_id='{self.sheet_id}', ...)")
        
        return True
    
    def prepare_record_data(self, report_date: str, report_type: str, 
                           report_time: str, report_data: dict) -> dict:
        """"""
        
        summary = report_data.get("summary", {})
        market_stats = report_data.get("market_stats", {})
        ai_analysis = report_data.get("ai_analysis", "")
        
        # 
        try:
            date_obj = datetime.strptime(report_date, "%Y-%m-%d")
            date_timestamp = str(int(date_obj.timestamp() * 1000))
        except:
            date_timestamp = str(int(datetime.now().timestamp() * 1000))
        
        # 
        return {
            "field_values": {
                "": date_timestamp,  # 
                "": [{"text": report_type}],  # 
                "": [{"text": report_time, "type": "text"}],  # 
                
                # 
                "": summary.get("total_value", 0),
                "": summary.get("daily_profit_loss", 0),
                "": summary.get("total_profit_loss", 0),
                
                #  78.6% -> 0.786
                "": summary.get("position_ratio", 0) / 100.0,
                "": summary.get("holding_count", 0),
                
                # 
                "": [{"text": market_stats.get("sh_index", ""), "type": "text"}],
                "": [{"text": market_stats.get("sz_index", ""), "type": "text"}],
                "": [{"text": market_stats.get("cy_index", ""), "type": "text"}],
                "": [{"text": market_stats.get("market_temperature", "")}],
                "": [{"text": market_stats.get("north_fund_flow", ""), "type": "text"}],
                "": [{"text": market_stats.get("advance_decline", ""), "type": "text"}],
                
                # AI
                "AI": [{"text": ai_analysis.get("market_summary", "")[:100], "type": "text"}],
                "AI": [{"text": ai_analysis.get("suggestions", "")[:100], "type": "text"}],
                
                # 
                "": []  # : [{"text": "", "type": "url", "link": "https://..."}]
            }
        }
    
    def save_daily_report(self, report_date: str, report_type: str, 
                         report_time: str, report_data: dict, 
                         doc_url: str = "") -> bool:
        """
        
        
        Args:
            report_date:  (YYYY-MM-DD)
            report_type:  (""  "")
            report_time:  (HH:MM)
            report_data: 
            doc_url: 
            
        Returns:
            bool: 
        """
        print(f"\n ...")
        print(f"  : {report_date}")
        print(f"  : {report_type}")
        print(f"  : {report_time}")
        
        # 
        if not self.ensure_smart_sheet_exists():
            print(" ")
            return False
        
        # 
        if not self.ensure_fields_exist():
            print(" ")
            return False
        
        # 
        record_data = self.prepare_record_data(report_date, report_type, report_time, report_data)
        
        # 
        if doc_url:
            record_data["field_values"][""] = [
                {"text": "", "type": "url", "link": doc_url}
            ]
        
        print(f"\n :")
        for key, value in list(record_data["field_values"].items())[:5]:  # 5
            print(f"  - {key}: {value}")
        print(f"   {len(record_data['field_values'])} ")
        
        # :
        # result = smartsheet.add_records(file_id, sheet_id, records=[record_data])
        
        print("\n API:")
        print(f"""  smartsheet.add_records(
    file_id="{self.file_id}",
    sheet_id="{self.sheet_id}",
    records=[
        {json.dumps(record_data, ensure_ascii=False, indent=4)}
    ]
)""")
        
        print(f"\n : {report_date} {report_type} ")
        print("   :")
        print("     1. MCP")
        print("     2. ")
        print("     3. main.py")
        
        return True
    
    def check_existing_record(self, report_date: str, report_type: str) -> Optional[str]:
        """"""
        if not self.file_id or not self.sheet_id:
            return None
        
        # :
        # records = smartsheet.list_records(file_id, sheet_id, filter_logic="AND([]='{report_date}',[]='{report_type}')")
        
        print(f"\n  {report_date} {report_type} ...")
        print(f"  API: smartsheet.list_records(file_id='{self.file_id}', ...)")
        
        return None

def create_sample_report():
    """"""
    return {
        "summary": {
            "total_value": 202154.32,
            "daily_profit_loss": 2567.89,
            "total_profit_loss": 15789.45,
            "position_ratio": 78.6,
            "holding_count": 21
        },
        "market_stats": {
            "sh_index": "+0.45%",
            "sz_index": "+0.78%",
            "cy_index": "+1.23%",
            "market_temperature": "",
            "north_fund_flow": " 15.2",
            "advance_decline": " 2680  /  1820 "
        },
        "ai_analysis": {
            "market_summary": "ETF",
            "suggestions": "50ETF"
        }
    }

def main():
    """"""
    print("=" * 70)
    print("")
    print("=" * 70)
    
    # 
    manager = TencentSmartSheetManager()
    
    if not manager.token:
        print("\n Tokenconfig.yaml")
        print("   Token:", "" if manager.token else "")
        return
    
    print(f"\n ")
    print(f"   Token: {manager.token[:10]}...")
    
    # 
    report_date = datetime.now().strftime("%Y-%m-%d")
    report_type = ""
    report_time = "08:00"
    sample_data = create_sample_report()
    
    # 
    print(f"\n  {report_date} {report_type} ...")
    success = manager.save_daily_report(
        report_date, report_type, report_time, sample_data,
        doc_url="https://docs.qq.com/aio/DV2ZrYUtCaG1odE9G"
    )
    
    if success:
        print(f"\n :")
        print("-" * 60)
        print("\n1 :")
        print("   1.  https://docs.qq.com")
        print("   2.  -> ")
        print("   3. IDURL: https://docs.qq.com/sheet/DV{file_id}")
        
        print("\n2  (config.yaml):")
        print("   :")
        print("   ```yaml")
        print("   tencent_docs:")
        print("     token: \"7bd23133a8c346008cc7b86385e1c06d\"")
        print("     report_doc_id: \"DV1VVTk9OcUxhcEtT\"")
        print("     data_sheet_id: \"ID\"  #  ")
        print("   ```")
        
        print("\n3 :")
        print("    main.py  build_evening_brief() :")
        print("   ```python")
        print('   manager = TencentSmartSheetManager()')
        print('   manager.save_daily_report(')
        print('       date_str, "" if not is_morning else "",')
        print('       datetime.now().strftime("%H:%M"), data,')
        print('       doc_url=doc_url)')
        print('   ```')
        
        print(f"\n :")
        print("    ")
        print("    ")
        print("    ")
        print("    ")
    else:
        print("\n ")

if __name__ == "__main__":
    main()