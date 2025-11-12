# Fix matplotlib + PyQt5 integration
# Run this in PowerShell

Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Matplotlib + PyQt5 Fix Script" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`nChecking current installation..." -ForegroundColor Yellow
python check_pyqt5_details.py

Write-Host "`n`n" + "="*60 -ForegroundColor Cyan
Write-Host "Attempting Fix 1: Reinstall PyQt5 components" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

Write-Host "`nUninstalling all PyQt5 packages..." -ForegroundColor Yellow
pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip

Write-Host "`nReinstalling PyQt5 5.15.9..." -ForegroundColor Yellow
pip install PyQt5==5.15.9

Write-Host "`n`nTesting..." -ForegroundColor Yellow
python test_matplotlib_qt5.py

$response = Read-Host "`nDid it work? (y/n)"
if ($response -eq 'y') {
    Write-Host "✓ Fixed!" -ForegroundColor Green
    exit
}

Write-Host "`n`n" + "="*60 -ForegroundColor Cyan
Write-Host "Attempting Fix 2: Install PyQt5-sip explicitly" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

pip install PyQt5-sip
python test_matplotlib_qt5.py

$response = Read-Host "`nDid it work? (y/n)"
if ($response -eq 'y') {
    Write-Host "✓ Fixed!" -ForegroundColor Green
    exit
}

Write-Host "`n`n" + "="*60 -ForegroundColor Cyan
Write-Host "Attempting Fix 3: Reinstall matplotlib from source" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

pip uninstall -y matplotlib
pip install matplotlib==3.7.1 --no-binary matplotlib

python test_matplotlib_qt5.py

$response = Read-Host "`nDid it work? (y/n)"
if ($response -eq 'y') {
    Write-Host "✓ Fixed!" -ForegroundColor Green
    exit
}

Write-Host "`n`n" + "="*60 -ForegroundColor Cyan
Write-Host "Attempting Fix 4: Use conda (if available)" -ForegroundColor Cyan
Write-Host "="*60 -ForegroundColor Cyan

conda install -y matplotlib=3.7.1 pyqt=5.15.9

python test_matplotlib_qt5.py

Write-Host "`n`nIf none of these worked, please:" -ForegroundColor Red
Write-Host "1. Run: python check_pyqt5_details.py" -ForegroundColor Yellow
Write-Host "2. Check the error message from FigureCanvasQTAgg import" -ForegroundColor Yellow
Write-Host "3. Install Visual C++ Redistributable if needed:" -ForegroundColor Yellow
Write-Host "   https://aka.ms/vs/17/release/vc_redist.x64.exe" -ForegroundColor Yellow
