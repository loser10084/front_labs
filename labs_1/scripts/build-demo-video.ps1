$ErrorActionPreference = 'Stop'

$ffmpeg = 'D:\tools\video_clip\windows版本\Jianying6.01\Jianying_Pro\6.0.1.11779\ffmpeg.exe'
if (-not (Test-Path -LiteralPath $ffmpeg)) {
    throw 'FFmpeg was not found. Update $ffmpeg to your local ffmpeg.exe path.'
}

$root = Split-Path -Parent $PSScriptRoot
$assets = Join-Path $root 'assets'
$filters = @'
[0:v]scale=1440:810:force_original_aspect_ratio=increase,crop=1440:810,zoompan=z='min(zoom+0.004,1.35)':x='(iw-iw/zoom)*0.72':y='(ih-ih/zoom)*0.5':d=1:s=1280x720:fps=30,setsar=1,format=yuv420p[v0];
[1:v]scale=1440:810:force_original_aspect_ratio=increase,crop=1440:810,zoompan=z='min(zoom+0.004,1.35)':x='(iw-iw/zoom)*0.7':y='(ih-ih/zoom)*0.5':d=1:s=1280x720:fps=30,setsar=1,format=yuv420p[v1];
[2:v]scale=1440:810:force_original_aspect_ratio=increase,crop=1440:810,zoompan=z='min(zoom+0.004,1.35)':x='(iw-iw/zoom)*0.55':y='(ih-ih/zoom)*0.5':d=1:s=1280x720:fps=30,setsar=1,format=yuv420p[v2];
[v0][v1]xfade=transition=fade:duration=0.45:offset=2.55[x1];
[x1][v2]xfade=transition=fade:duration=0.45:offset=5.10,format=yuv420p[out]
'@ -replace "`r?`n", ''

$nativeArgs = @(
    '-hide_banner', '-y', '-loglevel', 'error',
    '-loop', '1', '-t', '3', '-i', (Join-Path $assets 'exterior-v2.png'),
    '-loop', '1', '-t', '3', '-i', (Join-Path $assets 'corridor-v2.png'),
    '-loop', '1', '-t', '3', '-i', (Join-Path $assets 'timber-v2.png'),
    '-filter_complex', $filters,
    '-map', '[out]', '-an', '-c:v', 'h264_mf', '-b:v', '8M',
    '-g', '1', '-movflags', '+faststart',
    (Join-Path $assets 'architecture-v2.mp4')
)
& $ffmpeg @nativeArgs
if ($LASTEXITCODE -ne 0) {
    throw "FFmpeg failed with exit code $LASTEXITCODE"
}
