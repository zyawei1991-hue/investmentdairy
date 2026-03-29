@echo off
chcp 65001 >nul
cd %~dp0
echo [%time%] 触发收盘后投资日报...
python emergency_wrapper.py --evening
echo [%time%] 执行完成
pause