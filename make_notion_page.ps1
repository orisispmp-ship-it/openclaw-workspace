$headers = @{
    "Authorization" = "Bearer ntn_52…Lbf8"
    "Notion-Version" = "2026-03-11"
    "Content-Type" = "application/json"
}

$body = @{
    parent = @{
        type = "workspace"
    }
    icon = @{
        type = "emoji"
        emoji = "📊"
    }
    properties = @{
        title = @{
            title = @(
                @{
                    type = "text"
                    text = @{
                        content = "KOSPI 연도별 월별 최저점 분석 (2015~2024)"
                    }
                }
            )
        }
    }
    children = @(
        @{ object = "block"; type = "heading_2"; heading_2 = @{ rich_text = @(@{ type = "text"; text = @{ content = "연도별 최저점 (종가 기준)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2015: 8월 (1,941)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2016: 1월 (1,912)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2017: 1월 (2,068)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2018: 10월 (2,030)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2019: 8월 (1,968)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2020: 3월 (1,755) - 코로나19 쇼크" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2021: 11월 (2,839)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2022: 9월 (2,155)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2023: 10월 (2,278)" } }) } },
        @{ object = "block"; type = "paragraph"; paragraph = @{ rich_text = @(@{ type = "text"; text = @{ content = "2024: 12월 (2,399)" } }) } }
    )
} | ConvertTo-Json -Depth 10

try {
    $result = Invoke-RestMethod -Uri "https://api.notion.com/v1/pages" -Method Post -Headers $headers -Body $body
    $result | ConvertTo-Json -Compress | Out-File "C:\Users\orisi\.openclaw\workspace\created.txt" -Encoding UTF8
    Write-Output "SUCCESS: $($result.id)"
} catch {
    $_.Exception.Message | Out-File "C:\Users\orisi\.openclaw\workspace\created.txt" -Encoding UTF8
    Write-Output "FAILED: $($_.Exception.Message)"
}
