# Registra tarea programada Windows: LinkedIn Intel cada 12 horas
$ErrorActionPreference = "Stop"
$TaskName = "OpenClaw-Intel-LinkedIn-12h"
$Script = "C:\DEV\openclaw-mauro\scripts\run-intel-linkedin-12h.ps1"

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Script`""

$Trigger = New-ScheduledTaskTrigger -Daily -At "06:00"
$Trigger.Repetition = New-ScheduledTaskTrigger -Once -At "06:00" -RepetitionInterval (New-TimeSpan -Hours 12) -RepetitionDuration (New-TimeSpan -Days 1)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Description "Scan LinkedIn Innovacion Radical y sync al servidor OpenClaw cada 12h" `
    -Force

Write-Host "Tarea registrada: $TaskName (06:00 y 18:00)"
Write-Host "Ver: taskschd.msc -> $TaskName"
