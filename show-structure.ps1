function Show-TreeStructure {
    param (
        [string]$Path = ".",
        [int]$IndentLevel = 0
    )

    # Get items in the current directory, excluding hidden folders and node_modules
    $items = Get-ChildItem -Path $Path |
        Where-Object { 
            -not ($_.Name -like ".*") -and 
            -not ($_.Name -eq "venv") -and
            -not ($_.Name -like "*.pyc") -and
            -not ($_.PSIsContainer -and $_.Attributes -match "Hidden")
        }

    foreach ($item in $items) {
        # Create indentation
        $indent = "    " * $IndentLevel
        
        # Display current item using simple ASCII characters
        Write-Host ($indent + "+-- " + $item.Name)

        # If it's a directory, recurse into it
        if ($item.PSIsContainer) {
            Show-TreeStructure -Path $item.FullName -IndentLevel ($IndentLevel + 1)
        }
    }
}

# Call the function automatically when script is run
Show-TreeStructure -Path "."