param([Parameter(Mandatory=$true)][string]$Source,[Parameter(Mandatory=$true)][string]$Movie,[Parameter(Mandatory=$true)][string]$Poster,[Parameter(Mandatory=$true)][string]$Output)
$ErrorActionPreference='Stop'
$sourcePath=(Resolve-Path -LiteralPath $Source).Path
$moviePath=(Resolve-Path -LiteralPath $Movie).Path
$posterPath=(Resolve-Path -LiteralPath $Poster).Path
$outputPath=[System.IO.Path]::GetFullPath((Join-Path (Get-Location) $Output))
$app=New-Object -ComObject PowerPoint.Application
try {
 $deck=$app.Presentations.Open($sourcePath,0,0,0)
 $slide=$deck.Slides.Item(2)
 for($i=$slide.Shapes.Count;$i -ge 1;$i--){$slide.Shapes.Item($i).Delete()}
 $w=$deck.PageSetup.SlideWidth
 $h=$deck.PageSetup.SlideHeight
 $media=$slide.Shapes.AddMediaObject2($moviePath,0,-1,0,0,$w,$h)
 $media.Name='OpeningFilm_30s_Embedded'
 $media.MediaFormat.SetDisplayPictureFromFile($posterPath)
 $play=$media.AnimationSettings.PlaySettings
 $play.PlayOnEntry=-1
 foreach($effect in $slide.TimeLine.MainSequence){if($effect.Shape.Id -eq $media.Id){$effect.Timing.TriggerType=2;$effect.Timing.TriggerDelayTime=0}}
 $play.LoopUntilStopped=0
 $play.RewindMovie=0
 $play.HideWhileNotPlaying=0
 foreach($s in $deck.Slides){$s.SlideShowTransition.EntryEffect=0;$s.SlideShowTransition.AdvanceOnTime=0;$s.SlideShowTransition.AdvanceOnClick=-1}
 $deck.SlideShowSettings.AdvanceMode=1
 $deck.SaveAs($outputPath,24)
 Write-Output ('Embedded movie length (ms): '+$media.MediaFormat.Length)
 $deck.Close()
} finally {$app.Quit()}
