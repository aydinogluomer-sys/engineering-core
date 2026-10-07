param(
  [string]$Source,
  [string]$Ref,
  [Parameter(Mandatory=$true)][string]$Destination,
  [switch]$ReplaceDrift,
  [switch]$Rollback
)
$arguments = @("$PSScriptRoot/install.py", "--destination", $Destination)
if ($Rollback) { $arguments += "--rollback" } else {
  if (-not $Source -or -not $Ref) { throw "Source and Ref are required unless Rollback is used" }
  $arguments += @("--source", $Source, "--ref", $Ref)
  if ($ReplaceDrift) { $arguments += "--replace-drift" }
}
python @arguments
exit $LASTEXITCODE
