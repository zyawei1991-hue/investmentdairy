#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试飞书集成功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import YamlConfig, send_to_feishu

def test_feishu_send():
    """测试飞书发送功能"""
    try:
        # 加载配置
        config = YamlConfig.get_instance()
        cfg = config.config
        
        print("飞书配置:")
        feishu_cfg = cfg.get("feishu", {})
        print(f"  enabled: {feishu_cfg.get('enabled', False)}")
        print(f"  app_id: {feishu_cfg.get('app_id', '')}")
        print(f"  push_target: {feishu_cfg.get('push_target', '')}")
        print(f"  chat_id: {feishu_cfg.get('chat_id', '')}")
        
        if feishu_cfg.get("enabled", False):
            # 测试消息
            test_msg = "[投资日报飞书集成测试]\n时间：2026年3月26日 13:35\n\n✅ 飞书集成测试完成！\n\n配置状态：\n- 定时任务已配置\n- 明天开始自动推送\n- 推送时间：08:00 和 15:30\n\n如果收到此消息，说明飞书推送通道已完全就绪！"
            
            print(f"\n发送测试消息...")
            result = send_to_feishu(cfg, test_msg)
            
            if result:
                print("✅ 飞书集成测试成功！")
                return True
            else:
                print("❌ 飞书集成测试失败")
                return False
        else:
            print("飞书推送功能未启用，请在config.yaml中设置 feishu.enabled: true")
            return False
            
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_feishu_send()
    sys.exit(0 if success else 1)