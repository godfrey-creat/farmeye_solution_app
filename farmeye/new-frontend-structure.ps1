# setup-structure.ps1

$structure = @{
    "templates" = @(
        "base.html"
    )
    "templates/dashboard" = @(
        "index.html", "field_map.html", "analytics.html", "irrigation.html",
        "weather.html", "pest_control.html", "schedule.html"
    )
    "templates/partials" = @(
        "sidebar.html", "header.html", "notifications.html", "weather_widget.html",
        "field_health.html", "soil_health.html", "moisture_level.html",
        "growth_stage.html", "alerts.html", "field_view.html", "satellite_imagery.html",
        "timeline.html"
    )
    "templates/auth" = @(
        "auth.html", "reset_password.html", "verification.html"
    )
    "templates/partials/auth" = @(
        "login_form.html", "register_form.html"
    )
    "static/css" = @(
        "main.css", "auth.css"
    )
    "static/css/components" = @(
        "sidebar.css", "notifications.css", "cards.css"
    )
    "static/js" = @(
        "main.js", "charts.js", "notifications.js", "auth.js"
    )
}

foreach ($folder in $structure.Keys) {
    if (-not (Test-Path $folder)) {
        New-Item -Path $folder -ItemType Directory -Force | Out-Null
        Write-Host "Created folder: $folder"
    }

    foreach ($file in $structure[$folder]) {
        $filePath = Join-Path -Path $folder -ChildPath $file
        if (-not (Test-Path $filePath)) {
            New-Item -Path $filePath -ItemType File -Force | Out-Null
            Write-Host "Created file: $filePath"
        }
    }
}
