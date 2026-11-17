param([Parameter(Mandatory=$true)][string]$Label)
# Run on PC server after copying the exact committed release and its manifest into .local/hr-attendance001.
$ErrorActionPreference = 'Stop'
if ($Label -notmatch '^s[34](-[a-z0-9]+)?$') { throw 'Invalid release label' }
$root = 'C:\Projects\TANPHAT-ONE'
$base = Join-Path $root '.local\hr-attendance001'
$manifest = Get-Content -LiteralPath "$base\$Label-manifest.json" -Raw | ConvertFrom-Json
$addon = 'custom_addons/tp_hr_attendance/'
function FileHash([string]$relative) {
    if (-not $relative.StartsWith($addon) -or $relative.Contains('..')) { throw "Out of scope: $relative" }
    $target = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $target)) { return 'MISSING' }
    $content = [IO.File]::ReadAllText($target).Replace("`r`n", "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($content)))).Replace('-','').ToLower() }
    finally { $sha.Dispose() }
}
$container = (docker inspect tp-odoo | ConvertFrom-Json)[0]
if (-not $container.State.Running -or $container.Config.WorkingDir -ne '/workspace') { throw 'Unexpected Odoo runtime' }
foreach ($file in $manifest.baseline.PSObject.Properties) {
    if ((FileHash $file.Name) -ne $file.Value) { throw "Source drift before deploy: $($file.Name)" }
}
foreach ($file in $manifest.release.PSObject.Properties) {
    if (-not $manifest.baseline.PSObject.Properties[$file.Name] -and (FileHash $file.Name) -ne 'MISSING') { throw "Unexpected new file: $($file.Name)" }
}
$stamp = Get-Date -Format 'yyyyMMddTHHmmss'
$backup = "C:\TANPHAT-backups\hr-attendance001\$Label-$stamp"
New-Item -ItemType Directory -Path $backup | Out-Null
$sql = "SELECT json_build_object('module',(SELECT latest_version FROM ir_module_module WHERE name='tp_hr_attendance'),'employees',(SELECT count(*) FROM hr_employee),'users',(SELECT count(*) FROM res_users),'groups',(SELECT md5(string_agg(uid||':'||gid,',' ORDER BY uid,gid)) FROM res_groups_users_rel),'roster',(SELECT md5(string_agg(e.id||':'||coalesce(e.user_id,0)||':'||coalesce(v.department_id,0),',' ORDER BY e.id)) FROM hr_employee e LEFT JOIN hr_version v ON v.id=e.current_version_id),'days',(SELECT count(*) FROM tp_hr_attendance_day),'sessions',(SELECT count(*) FROM tp_hr_attendance_session),'base_url',(SELECT md5(value) FROM ir_config_parameter WHERE key='web.base.url'))"
docker exec tp-postgres psql -U tp_odoo -d tp_tanphat_dev -Atc $sql | Set-Content -LiteralPath "$base\$Label-before.json" -Encoding UTF8
if ($LASTEXITCODE -ne 0) { throw 'Snapshot failed' }
docker stop tp-odoo | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Stop failed' }
$upgradeExit = -1
try {
    docker exec tp-postgres pg_dump -U tp_odoo -F c -f /tmp/hr-attendance-pre.dump tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'pg_dump failed' }
    docker exec tp-postgres pg_restore -l /tmp/hr-attendance-pre.dump > "$backup\restore-list.txt"
    if ($LASTEXITCODE -ne 0) { throw 'Backup verification failed' }
    docker cp tp-postgres:/tmp/hr-attendance-pre.dump "$backup\tp_tanphat_dev.dump"
    if ($LASTEXITCODE -ne 0) { throw 'Backup copy failed' }
    tar -czf "$backup\filestore.tar.gz" -C "$root\docker_data\filestore" tp_tanphat_dev
    if ($LASTEXITCODE -ne 0) { throw 'Filestore backup failed' }
    tar -czf "$backup\source.tar.gz" -C $root custom_addons/tp_hr_attendance
    if ($LASTEXITCODE -ne 0) { throw 'Source backup failed' }
    Copy-Item -LiteralPath "$root\docker.odoo.conf", "$base\$Label-manifest.json", "$base\$Label-before.json" -Destination $backup
    tar -xzf "$base\$Label-release.tar.gz" -C $root
    if ($LASTEXITCODE -ne 0) { throw 'Extract failed' }
    foreach ($file in $manifest.release.PSObject.Properties) {
        if ((FileHash $file.Name) -ne $file.Value) { throw "Release checksum mismatch: $($file.Name)" }
    }
    $argsDocker = @('run','--rm','--name','tp-attendance-upgrade','--network','tanphat-one_default',
        '-v',($root+':/workspace'),'-v',($root+'\docker_data\filestore:/var/lib/odoo/filestore'),'-w','/workspace',
        $container.Config.Image,'python3','odoo-bin','-c','/workspace/docker.odoo.conf','-d','tp_tanphat_dev',
        '-u','tp_hr_attendance','--no-http','--stop-after-init','--max-cron-threads=0',
        "--logfile=/workspace/.local/hr-attendance001/$Label-upgrade.log")
    $ErrorActionPreference = 'Continue'
    & docker @argsDocker *> "$base\$Label-console.log"
    $upgradeExit = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($upgradeExit -ne 0) { throw "Upgrade failed: $upgradeExit; backup: $backup" }
} finally {
    docker start tp-odoo | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Restart failed' }
    Get-ChildItem -LiteralPath $backup -File | ForEach-Object { [pscustomobject]@{file=$_.Name; bytes=$_.Length; sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} } | ConvertTo-Json | Set-Content -LiteralPath "$backup\SHA256SUMS.json" -Encoding UTF8
}
docker exec tp-postgres psql -U tp_odoo -d tp_tanphat_dev -Atc $sql | Set-Content -LiteralPath "$base\$Label-after.json" -Encoding UTF8
$errors = @(Select-String -CaseSensitive -LiteralPath "$base\$Label-upgrade.log" -Pattern ' (ERROR|CRITICAL) ').Count
[pscustomobject]@{commit=$manifest.commit; backup=$backup; files=@($manifest.release.PSObject.Properties).Count; upgrade_exit=$upgradeExit; log_errors=$errors; version=$manifest.version} | ConvertTo-Json | Set-Content -LiteralPath "$base\$Label-result.json" -Encoding UTF8
Get-Content -LiteralPath "$base\$Label-result.json"
if ($errors -gt 0) { throw 'Upgrade logged errors: inspect before accepting' }
