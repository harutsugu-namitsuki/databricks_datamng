$ErrorActionPreference = 'Stop'

$path = (Get-ChildItem -Path "$env:USERPROFILE\*\*\Database1.accdb" | Select-Object -First 1).FullName
if (-not $path -or -not (Test-Path $path)) {
    Write-Host "File not found at $path"
    exit
}

Write-Host "Attempting to inspect database via COM..."
try {
    $acc = New-Object -ComObject Access.Application
    $acc.Visible = $false
    # Open the database. 
    $acc.OpenCurrentDatabase($path, $false)
    
    Write-Host "`n=== Startup Properties ==="
    try {
        $db = $acc.CurrentDb()
        $props = $db.Properties
        foreach ($prop in $props) {
            if ($prop.Name -like "*Startup*") {
                Write-Host "$($prop.Name): $($prop.Value)"
            }
        }
    } catch {
        Write-Host "Could not read startup properties (or none defined)."
    }

    Write-Host "`n=== Forms (UI Components) ==="
    $acc.CurrentProject.AllForms | ForEach-Object { Write-Host $_.Name }
    
    Write-Host "`n=== Reports ==="
    $acc.CurrentProject.AllReports | ForEach-Object { Write-Host $_.Name }

    Write-Host "`n=== Modules (VBA Code) ==="
    $acc.CurrentProject.AllModules | ForEach-Object { Write-Host $_.Name }
    
    Write-Host "`n=== Macros ==="
    $acc.CurrentProject.AllMacros | ForEach-Object { Write-Host $_.Name }
    
    Write-Host "`n=== Tables (Data) ==="
    $acc.CurrentData.AllTables | ForEach-Object { 
        if ($_.Name -notlike "MSys*") {
            Write-Host $_.Name 
        }
    }

    # Try to export VBA code if possible
    Write-Host "`n=== VBA Code Snippets ==="
    try {
        $vbc = $acc.VBE.ActiveVBProject.VBComponents
        foreach ($comp in $vbc) {
            $lines = $comp.CodeModule.CountOfLines
            if ($lines -gt 0) {
                Write-Host "--- Component: $($comp.Name) ($lines lines) ---"
                # Print first 20 lines as a sample
                $printLines = [math]::Min($lines, 20)
                Write-Host $comp.CodeModule.Lines(1, $printLines)
            }
        }
    } catch {
        Write-Host "Could not read VBA Code (might require 'Trust access to the VBA project object model' in Excel/Access Trust Center)."
        Write-Host $_.Exception.Message
    }
    
    $acc.Quit()
    [System.Runtime.Interopservices.Marshal]::ReleaseComObject($acc) | Out-Null
    Write-Host "`nInspection complete."

} catch {
    Write-Host "Error during inspection:"
    Write-Host $_
    try { $acc.Quit() } catch {}
}
