# Builds the EyeControl Windows release and Python package.
#   dist\eyecontrol.exe                         console executable (PyInstaller, one file)
#   dist\EyeControl-<v>-windows.zip             eyecontrol.exe + LISEZMOI.txt + LICENSE.txt
#   dist\eyecontrol-<v>-py3-none-any.whl        Python package (Linux / Kali with pipx, or pip)
# Requires the dev venv: python -m venv .venv; .venv\Scripts\python -m pip install -e ".\cli[dev]" pyinstaller
# (building from the venv keeps unrelated global packages out of the executable)
# Usage : powershell -ExecutionPolicy Bypass -File build_windows.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root
$python = Join-Path $root ".venv\Scripts\python.exe"

$version = (Select-String -Path "cli\eyecontrol\__init__.py" -Pattern '__version__ = "(.+)"').Matches[0].Groups[1].Value
Write-Host "EyeControl $version"

Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force dist | Out-Null

# 1. Console executable (no --windowed: EyeControl lives in the terminal)
& $python -m PyInstaller --noconfirm --onefile --console --name eyecontrol `
    --icon "$root\assets\icon.ico" --paths "$root\cli" --collect-submodules eyecontrol `
    --distpath dist --workpath build\pyinstaller --specpath build `
    "$root\cli\eyecontrol\__main__.py"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

# 2. Quick check of the produced executable
$out = & dist\eyecontrol.exe --version
if ($out -ne "EyeControl $version") { throw "Unexpected version: $out" }
Write-Host "Executable OK: $out"

# 3. Windows archive
$stage = "build\zip"
New-Item -ItemType Directory -Force $stage | Out-Null
Copy-Item dist\eyecontrol.exe $stage
Copy-Item LISEZMOI.txt $stage
Copy-Item LICENSE "$stage\LICENSE.txt"
Compress-Archive -Path "$stage\*" -DestinationPath "dist\EyeControl-$version-windows.zip" -Force

# 4. Python package (wheel)
& $python -m pip wheel .\cli --no-deps -w dist -q
if ($LASTEXITCODE -ne 0) { throw "Wheel build failed" }

Get-ChildItem dist | ForEach-Object {
    "{0,-40} {1,10}  {2}" -f $_.Name, $_.Length, (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower()
}
