$curr_path = (Get-Item -Path ".\").FullName
[Environment]::SetEnvironmentVariable("PYTHONPATH", $env:PYTHONPATH + ";" + $curr_path, "User")