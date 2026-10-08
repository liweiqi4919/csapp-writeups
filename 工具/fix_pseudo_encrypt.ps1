# ============================================================
# QuestionCTF 2026 / Week1 / Misc -- "压缩包" (205 pts)
# ZIP pseudo-encryption: the general purpose bit flag claims
# "encrypted" (bit 0 = 1) but the payload is plain DEFLATE.
# Fix: clear bit 0. Data stays untouched.
# ============================================================

$ErrorActionPreference = 'Stop'

$src    = 'D:\DSH\csapp\ctf-writeups\frist.zip'
$dst    = 'D:\DSH\csapp\ctf-writeups\QuestionCTF2026\frist_fixed.zip'
$outDir = 'D:\DSH\csapp\ctf-writeups\QuestionCTF2026\extracted'

$bytes = [System.IO.File]::ReadAllBytes($src)

# --- Offsets of the 2-byte "general purpose bit flag" field ---
#   Local file header  : offset 6  inside each record
#   Central directory  : offset 8  inside each record
# The field appears in BOTH places and both are lying here.
$flagOffsets = @(
    0x004A,   # local file header -> frist/final.zip
    0x0143,   # local file header -> frist/Is_this_a_real_flag.txt
    0x027E,   # central directory -> frist/final.zip
    0x02D3    # central directory -> frist/Is_this_a_real_flag.txt
)

Write-Host '--- patching flag bytes ---'
foreach ($off in $flagOffsets) {
    $old = $bytes[$off]
    $bytes[$off] = $bytes[$off] -band 0xFE      # clear bit 0 = "encrypted"
    Write-Host ("  0x{0:X4}:  0x{1:X2} -> 0x{2:X2}" -f $off, $old, $bytes[$off])
}

[System.IO.File]::WriteAllBytes($dst, $bytes)
Write-Host ''
Write-Host "patched file written: $dst"

# --- extract the patched archive ---
if (Test-Path $outDir) { Remove-Item $outDir -Recurse -Force }
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
Expand-Archive -Path $dst -DestinationPath $outDir -Force

Write-Host ''
Write-Host '--- extracted contents ---'
Get-ChildItem $outDir -Recurse -File |
    Select-Object @{N='Size';E={$_.Length}}, FullName |
    Format-Table -AutoSize
