param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
      [string]$OutputFolder = 'validation\visual-refinement-20261029\powerpoint',
      [string]$PythonExecutable = 'python')
$ErrorActionPreference = 'Stop'
$folder = Join-Path $Root $OutputFolder
[void][System.IO.Directory]::CreateDirectory($folder)
$app = New-Object -ComObject PowerPoint.Application
try {
    foreach ($entry in @(@{name='決賽簡報_AI資安框架';poster=$false},@{name='決賽海報_AI資安框架_A2';poster=$true})) {
        $deck = $app.Presentations.Open((Join-Path $Root ('deliverables\'+$entry.name+'.pptx')),-1,0,0)
        try {
            foreach ($slide in $deck.Slides) {
                $png = if ($entry.poster) {Join-Path $Root 'deliverables\figures\poster-a2-preview.png'} else {Join-Path $folder ('slide-'+$slide.SlideIndex.ToString('00')+'.png')}
                if ($entry.poster) {$slide.Export($png,'PNG',1680,2376)} else {$slide.Export($png,'PNG',1600,900)}
            }
            $range=$deck.PrintOptions.Ranges.Add(1,$deck.Slides.Count)
            $deck.ExportAsFixedFormat((Join-Path $Root ('deliverables\'+$entry.name+'.pdf')),2,2,0,1,1,0,$range,1,'',0,0,-1,-1,-1)
            if (-not $entry.poster) {
                # PowerPoint may export a video placeholder as a blank PDF page.
                # Extract the exact embedded still and export it on a temporary slide.
                Add-Type -AssemblyName System.IO.Compression.FileSystem
                $image = Join-Path $folder 'opening-poster.png'
                $archive = [System.IO.Compression.ZipFile]::OpenRead((Join-Path $Root ('deliverables\'+$entry.name+'.pptx')))
                try {
                    $part = $archive.GetEntry('ppt/media/opening-poster.png')
                    if ($null -eq $part) { throw 'Embedded movie poster missing.' }
                    [System.IO.Compression.ZipFileExtensions]::ExtractToFile($part,$image,$true)
                } finally { $archive.Dispose() }
                $still = $app.Presentations.Add(0)
                try {
                    $still.PageSetup.SlideWidth = $deck.PageSetup.SlideWidth
                    $still.PageSetup.SlideHeight = $deck.PageSetup.SlideHeight
                    $page = $still.Slides.Add(1,12)
                    [void]$page.Shapes.AddPicture($image,0,-1,0,0,$still.PageSetup.SlideWidth,$still.PageSetup.SlideHeight)
                    $page.Export((Join-Path $folder 'slide-02.png'),'PNG',1600,900)
                    $posterPdf = Join-Path $folder 'opening-poster.pdf'
                    $still.SaveAs($posterPdf,32)
                } finally { $still.Close() }
                $pdf = Join-Path $Root ('deliverables\'+$entry.name+'.pdf')
                & $PythonExecutable (Join-Path $PSScriptRoot 'merge_static_poster.py') --source $pdf --poster $posterPdf --output $pdf
                if ($LASTEXITCODE -ne 0) { throw 'PDF movie poster replacement failed.' }
            }
            Write-Output ('Static export: '+$entry.name+', pages='+$deck.Slides.Count)
        } finally {$deck.Close()}
    }
} finally {[void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app)}
