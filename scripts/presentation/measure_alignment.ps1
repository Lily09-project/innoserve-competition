param([string]$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
      [switch]$CorrectText,
      [string]$OutputFolder = 'validation\alignment-20261029')
$ErrorActionPreference = 'Stop'
$folder = Join-Path $Root $OutputFolder
[void][System.IO.Directory]::CreateDirectory($folder)
$app = New-Object -ComObject PowerPoint.Application
function Read-Shapes($collection, $parentName) {
    $rows = @()
    foreach ($shape in $collection) {
        $name = $parentName + '/' + $shape.Name
        if ($shape.Type -eq 6) { $rows += Read-Shapes $shape.GroupItems $name }
        $row = @{name=$name; type=[int]$shape.Type; x=[double]$shape.Left; y=[double]$shape.Top;
            w=[double]$shape.Width; h=[double]$shape.Height}
        if ($shape.HasTextFrame -eq -1 -and $shape.TextFrame.HasText -eq -1) {
            $tf = $shape.TextFrame2
            $r = $tf.TextRange
            $row.text = $r.Text
            $row.bound = @([double]$r.BoundLeft,[double]$r.BoundTop,[double]$r.BoundWidth,[double]$r.BoundHeight)
            $row.align = [int]$r.ParagraphFormat.Alignment
            $row.vertical = [int]$tf.VerticalAnchor
            $row.margins = @([double]$tf.MarginLeft,[double]$tf.MarginTop,[double]$tf.MarginRight,[double]$tf.MarginBottom)
            $alignment = $row.align
            if ($alignment -in @(1,2,3)) {
                $target = [double]$shape.Left + [double]$tf.MarginLeft
                $observed = [double]$r.BoundLeft
                if ($alignment -eq 2) {
                    $target += ([double]$shape.Width-[double]$tf.MarginLeft-[double]$tf.MarginRight)/2
                    $observed += [double]$r.BoundWidth/2
                } elseif ($alignment -eq 3) {
                    $target = [double]$shape.Left+[double]$shape.Width-[double]$tf.MarginRight
                    $observed += [double]$r.BoundWidth
                }
                $stored = $shape.Tags.Item('ALIGNMENT_TARGET_X')
                if ($stored) { $target = [double]::Parse($stored,[System.Globalization.CultureInfo]::InvariantCulture) }
                if ($CorrectText) {
                    $shape.Tags.Add('ALIGNMENT_TARGET_X',$target.ToString('R',[System.Globalization.CultureInfo]::InvariantCulture))
                    $shift = $target-$observed
                    if ([Math]::Abs($shift) -gt .05) { $shape.Left = [double]$shape.Left+$shift }
                    $row.x = [double]$shape.Left
                    $row.bound = @([double]$r.BoundLeft,[double]$r.BoundTop,[double]$r.BoundWidth,[double]$r.BoundHeight)
                }
                $row.target_x = $target
            }
        }
        $rows += $row
    }
    return $rows
}
try {
    foreach ($entry in @(@{key='slides';name='決賽簡報_AI資安框架.pptx'},@{key='poster';name='決賽海報_AI資安框架_A2.pptx'})) {
        $deck = $app.Presentations.Open((Join-Path $Root ('deliverables\'+$entry.name)),$(-not $CorrectText),0,0)
        try {
            $pages = @()
            foreach ($slide in $deck.Slides) {
                $pages += @{page=$slide.SlideIndex; width=[double]$deck.PageSetup.SlideWidth;
                    height=[double]$deck.PageSetup.SlideHeight; shapes=@(Read-Shapes $slide.Shapes '')}
            }
            ConvertTo-Json -InputObject @($pages) -Depth 10 |
                Set-Content -LiteralPath (Join-Path $folder ($entry.key+'.json')) -Encoding utf8
            if ($CorrectText) { $deck.SaveAs((Join-Path $folder ($entry.key+'-aligned.pptx')),24) }
        } finally { $deck.Close() }
    }
} finally { [void][System.Runtime.InteropServices.Marshal]::ReleaseComObject($app) }
Write-Output 'Measured all text and shape frames with PowerPoint.'
