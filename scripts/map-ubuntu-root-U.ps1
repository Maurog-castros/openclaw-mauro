# Mapea la raíz del Ubuntu (Samba share ubuntu-root) como unidad U:
# Requiere: share [ubuntu-root] con read only = no en el servidor (ver setup-ubuntu-root-samba.sh)

$Server = "192.168.1.12"
$Share = "ubuntu-root"
$Remote = "\\$Server\$Share"
$Letter = "U"

# Quitar mapeo anterior en Y: si existe
if (Test-Path "${Letter}:\") {
    Write-Host "Ya existe unidad ${Letter}: — omitiendo net use."
} else {
    net use "Y:" /delete /y 2>$null | Out-Null
    $args = @(
        $Letter + ":",
        $Remote,
        "/persistent:yes"
    )
    Write-Host "Conectando $Remote como ${Letter}: ..."
    net use @args
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Si pide credenciales, usa el usuario Linux 'mauro' y la contraseña Samba (smbpasswd)." -ForegroundColor Yellow
        net use ($Letter + ":") $Remote /user:mauro /persistent:yes
    }
}

if (Test-Path "${Letter}:\") {
    Write-Host "OK: ${Letter}: -> $Remote" -ForegroundColor Green
    Get-Item "${Letter}:\"
} else {
    Write-Error "No se pudo montar ${Letter}:. Revisa Samba en el servidor."
    exit 1
}
