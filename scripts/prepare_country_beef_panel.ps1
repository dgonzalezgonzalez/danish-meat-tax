param(
    [string]$InputPath = "data/raw/eu_beef_carcass_prices_2023m04_2025m09.json",
    [string]$OutputPath = "data/processed/eu_beef_country_month_panel.csv"
)

$ErrorActionPreference = "Stop"

$rows = Get-Content -Raw $InputPath | ConvertFrom-Json
$weekly = foreach ($row in $rows) {
    if ($row.productCode -ne "AO2" -or $row.memberStateCode -eq "EU") {
        continue
    }

    $date = [datetime]::ParseExact($row.beginDate, "dd/MM/yyyy", $null)
    $price = [double]($row.price -replace "[^0-9.-]", "")
    [pscustomobject]@{
        memberStateCode = $row.memberStateCode
        memberStateName = $row.memberStateName
        month = "{0}m{1}" -f $date.Year, $date.Month
        week_begin = $date.ToString("yyyy-MM-dd")
        price_eur_100kg = $price
        category = $row.category
        productCode = $row.productCode
        unit = $row.unit
    }
}

$monthly = foreach ($group in ($weekly | Group-Object memberStateCode, month)) {
    $first = $group.Group[0]
    $mean = ($group.Group | Measure-Object -Property price_eur_100kg -Average).Average
    [pscustomobject]@{
        memberStateCode = $first.memberStateCode
        memberStateName = $first.memberStateName
        month = $first.month
        price_eur_100kg = [math]::Round($mean, 8)
        n_weekly = $group.Count
        category = $first.category
        productCode = $first.productCode
        unit = $first.unit
    }
}

$completeStates = $monthly |
    Group-Object memberStateCode |
    Where-Object { $_.Count -eq 30 } |
    Select-Object -ExpandProperty Name

$panel = $monthly |
    Where-Object { $completeStates -contains $_.memberStateCode } |
    Sort-Object memberStateCode, month

$outputDirectory = Split-Path -Parent $OutputPath
if ($outputDirectory -and -not (Test-Path $outputDirectory)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$panel | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

Write-Output ("series={0}; months={1}; observations={2}" -f `
    (($panel | Select-Object -ExpandProperty memberStateCode -Unique).Count),
    (($panel | Select-Object -ExpandProperty month -Unique).Count),
    $panel.Count)
