# 鎶曡祫鏃ユ姤鑴氭湰 (PowerShell 鐗堟湰)
# 鏀寔鑾峰彇涓滄柟璐㈠瘜琛屾儏鏁版嵁锛岀敓鎴愮泩浜忔姤鍛?
# ==================== 閰嶇疆鍖哄煙 ====================
$Config = @{
    WebhookUrl = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE"
    Holdings = @(
        @{ Code = "600519"; Name = "璐靛窞鑼呭彴"; Shares = 100; Cost = 1800.00 }
        @{ Code = "000858"; Name = "浜旂伯娑?; Shares = 200; Cost = 150.00 }
        @{ Code = "300750"; Name = "瀹佸痉鏃朵唬"; Shares = 300; Cost = 200.00 }
    )
}
# =================================================

function Get-StockQuote {
    param([string]$Code)
    $market = if ($Code.StartsWith("6")) { "1" } else { "0" }
    $url = "https://push2.eastmoney.com/api/qt/stock/get?secid=$market.$code&fields=f43,f44,f45,f46,f169,f170&ut=fa5fd1943c7b386f172d6893dbfba10b"
    try {
        $response = Invoke-RestMethod -Uri $url -Method Get -TimeoutSec 10
        $data = $response.data
        return @{
            Price = $data.f43 / 100
            High = $data.f44 / 100
            Low = $data.f45 / 100
            Open = $data.f46 / 100
            Change = $data.f169 / 100
            ChangePct = $data.f170 / 100
        }
    }
    catch {
        Write-Host "Error fetching $Code`: $_" -ForegroundColor Red
        return $null
    }
}

function Build-Report {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm"
    $lines = @("Investment Report $date`n")
    $totalCost = 0.0
    $totalValue = 0.0
    $totalProfit = 0.0
    foreach ($h in $Config.Holdings) {
        $quote = Get-StockQuote -Code $h.Code
        if ($null -eq $quote) {
            $lines += "Warning: $($h.Name)($($h.Code)) fetch failed`n"
            continue
        }
        $price = $quote.Price
        $cost = $h.Cost
        $shares = $h.Shares
        $value = $price * $shares
        $profit = ($price - $cost) * $shares
        $profitPct = if ($cost -gt 0) { ($price - $cost) / $cost * 100 } else { 0 }
        $totalCost += $cost * $shares
        $totalValue += $value
        $totalProfit += $profit
        $arrow = if ($quote.ChangePct -ge 0) { "UP" } else { "DOWN" }
        $sign = if ($profit -ge 0) { "+" } else { "" }
        $lines += "$arrow $($h.Name)($($h.Code))"
        $lines += "   Price: $($price.ToString('N2'))  Change: $($quote.ChangePct.ToString('+0.00;-0.00'))%"
        $lines += "   Holdings: $shares shares  Cost: $($cost.ToString('N2'))"
        $lines += "   Profit: $($sign)$($profit.ToString('N2'))CNY ($($sign)$($profitPct.ToString('0.00;-0.00'))%)`n"
    }
    $totalPct = if ($totalCost -gt 0) { ($totalValue - $totalCost) / $totalCost * 100 } else { 0 }
    $sign = if ($totalProfit -ge 0) { "+" } else { "" }
    $lines += "=========================="
    $lines += "Total Value: $($totalValue.ToString('N2'))CNY"
    $lines += "Total Profit: $($sign)$($totalProfit.ToString('N2'))CNY ($($sign)$($totalPct.ToString('0.00;-0.00'))%)"
    return $lines -join "`n"
}

function Send-ToWeChat {
    param([string]$Message)
    $payload = @{
        msgtype = "text"
        text = @{ content = $Message }
    } | ConvertTo-Json -Depth 3
    try {
        $response = Invoke-RestMethod -Uri $Config.WebhookUrl -Method Post -Body $payload -ContentType "application/json" -TimeoutSec 10
        if ($response.errcode -eq 0) {
            Write-Host "Sent successfully" -ForegroundColor Green
        }
        else {
            Write-Host "Send failed: $($response.errmsg)" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Send error: $_" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Investment Daily Report" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
$report = Build-Report
Write-Host $report -ForegroundColor White
Write-Host "`n========================================`n" -ForegroundColor Cyan
$send = Read-Host "Send to WeChat Work? (y/n)"
if ($send -eq "y" -or $send -eq "Y") {
    if ($Config.WebhookUrl -eq "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY_HERE") {
        Write-Host "`nPlease configure real Webhook URL first" -ForegroundColor Yellow
    }
    else {
        Send-ToWeChat -Message $report
    }
}