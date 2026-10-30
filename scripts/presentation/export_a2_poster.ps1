param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path)
$ErrorActionPreference = 'Stop'
$source = Join-Path $Root 'deliverables\決賽海報_AI資安框架_A2.pptx'
$pdf = Join-Path $Root 'deliverables\決賽海報_AI資安框架_A2.pdf'
$png = Join-Path $Root 'deliverables\figures\poster-a2-preview.png'
$app = New-Object -ComObject PowerPoint.Application
$deck = $null
try {
    $deck = $app.Presentations.Open($source, -1, 0, 0)
    $overflow = @()
    foreach ($item in $deck.Slides.Item(1).Shapes) {
        if ($item.HasTextFrame -eq -1 -and $item.TextFrame.HasText -eq -1) {
            $bounds = $item.TextFrame2.TextRange
            if ($bounds.BoundWidth -gt ($item.Width + 2) -or $bounds.BoundHeight -gt ($item.Height + 2)) {
                $overflow += $item.Name
            }
        }
    }
    $reportFolder = Join-Path $Root 'validation\poster-a2'
    [void][System.IO.Directory]::CreateDirectory($reportFolder)
    @{slides=$deck.Slides.Count; text_overflow=$overflow} | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $reportFolder 'layout.json') -Encoding utf8
    if ($overflow.Count -gt 0) { throw 'Poster contains overflowing text frames.' }
    $range = $deck.PrintOptions.Ranges.Add(1, 1)
    # PDF/A requests portable font embedding; a concrete PrintRange is required by COM.
    $deck.ExportAsFixedFormat($pdf, 2, 2, 0, 1, 1, 0, $range, 1, '', 0, 0, -1, -1, -1)
    $deck.Slides.Item(1).Export($png, 'PNG', 1680, 2376)
    Write-Output ('Poster exported: slides=' + $deck.Slides.Count)
} finally {
    if ($null -ne $deck) { $deck.Close() }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
