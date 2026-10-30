param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
      [string]$OutputFolder = 'validation\palette-powerpoint')
$ErrorActionPreference = 'Stop'
$source = Join-Path $Root 'deliverables\決賽簡報_AI資安框架.pptx'
$folder = Join-Path $Root $OutputFolder
[void][System.IO.Directory]::CreateDirectory($folder)
$app = New-Object -ComObject PowerPoint.Application
$deck = $null
$show = $null
try {
    $deck = $app.Presentations.Open($source, -1, 0, 0)
    foreach ($slide in $deck.Slides) {
        $name = 'slide-' + $slide.SlideIndex.ToString('00') + '.png'
        $slide.Export((Join-Path $folder $name), 'PNG', 1600, 900)
    }
    $range = $deck.PrintOptions.Ranges.Add(1, $deck.Slides.Count)
    $deck.ExportAsFixedFormat((Join-Path $Root 'deliverables\決賽簡報_AI資安框架.pdf'), 2, 2, 0, 1, 1, 0, $range, 1, '', 0, 0, -1, -1, -1)
    $movie = $null
    foreach ($shape in $deck.Slides.Item(2).Shapes) {
        if ($shape.Name -eq 'OpeningFilm_30s_Embedded') { $movie = $shape }
    }
    if ($null -eq $movie) { throw 'Embedded movie missing.' }
    $deck.SlideShowSettings.ShowType = 2
    $deck.SlideShowSettings.AdvanceMode = 1
    $show = $deck.SlideShowSettings.Run()
    $show.View.GotoSlide(2)
    Start-Sleep -Seconds 3
    $first = $show.View.Player($movie.Id).CurrentPosition
    Start-Sleep -Seconds 3
    $second = $show.View.Player($movie.Id).CurrentPosition
    if ($second -le $first) { throw 'Embedded movie did not advance.' }
    Start-Sleep -Seconds 29
    $stoppedOn = $show.View.Slide.SlideIndex
    if ($stoppedOn -ne 2) { throw 'Presentation advanced unexpectedly.' }
    $show.View.GotoSlide(10)
    $qaSlide = $show.View.Slide.SlideIndex
    @{slides=$deck.Slides.Count; movie_ms=$movie.MediaFormat.Length; position_3s=$first;
      position_6s=$second; slide_after_35s=$stoppedOn; qa_start=$qaSlide} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $folder 'playback.json') -Encoding utf8
    Write-Output ('PowerPoint verified: slides=' + $deck.Slides.Count + ', movie_ms=' + $movie.MediaFormat.Length)
} finally {
    if ($null -ne $show) { $show.View.Exit() }
    # Exiting a read-only windowed slideshow may already close its presentation.
    foreach ($opened in @($app.Presentations)) {
        if ($opened.FullName -eq $source) { $opened.Close() }
    }
    [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
