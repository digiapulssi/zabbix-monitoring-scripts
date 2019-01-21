# Zabbix discovery: Find all running processes that can be monitored via Process performance counters

Write-Host -NoNewline '{"data":'

# Find all Counter instances of \Process(*)\% Processor Time set
# Initial example taken from https://stackoverflow.com/questions/38551504/continuously-monitors-the-cpu-usage-of-top-x-processes
#
# We can't just get InstanceName property because in some cases there are multiple performance counters with
# similar InstanceName properties, however the performenace counter path is different for each of them
# (eg. Teams, Teams#1, Teams#2 that are all different processes even though InstanceName is Teams for all of them)
#
$commands = Get-Counter -Counter "\Process(*)\% Processor Time" -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty CounterSamples |
  where {$_.Status -eq 0 -and $_.instancename -notin "_total", "idle"} |   # Filter out processes we can't access
  select @{N="{#PROCESS}";E={
     $_.Path -replace "^.*\\Process\((.*)\)\\% Processor Time$",'$1'
  }} |
  ConvertTo-Json -Compress
Write-Host -NoNewline $commands

Write-Host -NoNewline '}'
