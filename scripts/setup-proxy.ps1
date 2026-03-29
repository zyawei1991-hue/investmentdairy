# 代理配置助手

Write-Host "`n=== 系统代理配置 ===`n" -ForegroundColor Cyan

# 读取当前代理配置
$settings = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
Write-Host "当前状态:" -ForegroundColor Yellow
Write-Host "  代理启用: $($settings.ProxyEnable)"
Write-Host "  代理地址: $($settings.ProxyServer)"
Write-Host "  PAC文件: $($settings.AutoConfigURL)`n"

Write-Host "=== 可用操作 ===`n" -ForegroundColor Cyan
Write-Host "1. 禁用系统代理（临时）"
Write-Host "2. 启用系统代理"
Write-Host "3. 添加东方财富到例外（需手动配置）"
Write-Host "4. 退出"
Write-Host ""

$choice = Read-Host "请选择操作 (1-4)"

switch ($choice) {
    "1" {
        Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name "ProxyEnable" -Value 0
        Write-Host "`n✅ 系统代理已禁用" -ForegroundColor Green
        Write-Host "注意：这会临时禁用所有程序的代理" -ForegroundColor Yellow
        Write-Host "运行完成后记得重新启用（选项2）`n"
    }
    "2" {
        Set-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings" -Name "ProxyEnable" -Value 1
        Write-Host "`n✅ 系统代理已启用`n" -ForegroundColor Green
    }
    "3" {
        Write-Host "`n⚠️  需要手动配置代理例外" -ForegroundColor Yellow
        Write-Host "步骤："
        Write-Host "1. 打开 系统设置 > 网络和 Internet > 代理"
        Write-Host "2. 在 '手动设置代理' 中找到 '使用代理服务器'"
        Write-Host "3. 点击 '编辑' 添加例外："
        Write-Host "   push2.eastmoney.com;*.eastmoney.com"
        Write-Host ""
        Write-Host "或者，临时禁用代理（选项1）更简单`n"
    }
    "4" {
        Write-Host "`n退出`n"
        exit
    }
    default {
        Write-Host "`n❌ 无效选择`n" -ForegroundColor Red
    }
}

# 显示新状态
$newSettings = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings"
Write-Host "当前状态:" -ForegroundColor Yellow
Write-Host "  代理启用: $($newSettings.ProxyEnable)`n"
