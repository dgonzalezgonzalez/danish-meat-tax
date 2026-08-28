param(
    [string]$InputPath = "data/raw/eu_beef_trade_data_en.csv",
    [string]$OutputPath = "data/processed/eu_beef_trade_pair_month_panel.csv"
)

$ErrorActionPreference = "Stop"

function Convert-ToInvariantDouble {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return 0.0
    }
    return [double]::Parse($Value.Trim(), [Globalization.CultureInfo]::InvariantCulture)
}

$windowStart = [datetime]::new(2023, 4, 1)
$windowEnd = [datetime]::new(2025, 9, 1)
$months = for ($date = $windowStart; $date -le $windowEnd; $date = $date.AddMonths(1)) {
    $date.ToString("yyyy-MM")
}

$monthly = @{}
$pairs = @{}
$rows = Import-Csv $InputPath
foreach ($row in $rows) {
    if ($row.Flow -ne "IMPORT") {
        continue
    }
    $date = [datetime]::ParseExact(
        $row.'Month Date',
        "dd/MM/yyyy",
        [Globalization.CultureInfo]::InvariantCulture
    )
    if ($date -lt $windowStart -or $date -gt $windowEnd) {
        continue
    }

    $memberState = $row.'Member State'.Trim()
    $partner = $row.Partner.Trim()
    $pairId = "$memberState|$partner"
    $month = $date.ToString("yyyy-MM")
    $key = "$pairId|$month"
    $pairs[$pairId] = [pscustomobject]@{
        memberState = $memberState
        partner = $partner
    }

    if (-not $monthly.ContainsKey($key)) {
        $monthly[$key] = [pscustomobject]@{
            productWeight = 0.0
            carcaseWeight = 0.0
            value = 0.0
            productRows = 0
        }
    }
    $cell = $monthly[$key]
    $cell.productWeight += Convert-ToInvariantDouble $row.'Product Weight in tonnes'
    $cell.carcaseWeight += Convert-ToInvariantDouble $row.'Carcase Weight in tonnes'
    $cell.value += Convert-ToInvariantDouble $row.'Value in thousand euro'
    $cell.productRows++
}

$panel = foreach ($pairId in ($pairs.Keys | Sort-Object)) {
    $pair = $pairs[$pairId]
    foreach ($month in $months) {
        $key = "$pairId|$month"
        if ($monthly.ContainsKey($key)) {
            $cell = $monthly[$key]
        } else {
            $cell = [pscustomobject]@{
                productWeight = 0.0
                carcaseWeight = 0.0
                value = 0.0
                productRows = 0
            }
        }
        [pscustomobject]@{
            member_state = $pair.memberState
            partner = $pair.partner
            pair_id = $pairId
            month = $month
            product_weight_tonnes = [math]::Round($cell.productWeight, 8)
            carcase_weight_tonnes = [math]::Round($cell.carcaseWeight, 8)
            value_thousand_euro = [math]::Round($cell.value, 8)
            n_product_rows = $cell.productRows
            source_method = "European Commission Beef Trade bulk CSV; Eurostat COMEXT statistical regime 4"
        }
    }
}

$directory = Split-Path -Parent $OutputPath
if ($directory -and -not (Test-Path $directory)) {
    New-Item -ItemType Directory -Path $directory | Out-Null
}
$panel | Export-Csv -Path $OutputPath -NoTypeInformation -Encoding UTF8

$treatedPairs = ($pairs.Values | Where-Object {$_.memberState -eq "Denmark"}).Count
$zeroMonths = ($panel | Where-Object {$_.carcase_weight_tonnes -eq 0}).Count
Write-Output ("pairs={0}; treated_pairs={1}; months={2}; observations={3}; zero_months={4}" -f `
    $pairs.Count, $treatedPairs, $months.Count, $panel.Count, $zeroMonths)
