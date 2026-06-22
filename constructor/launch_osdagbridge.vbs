Set objShell = CreateObject("Wscript.Shell")
root = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

cmd = "cmd /c ""set PATH=" & root & "\Library\bin;" & root & "\Library\mingw-w64\bin;" & root & "\Library\usr\bin;" & root & "\DLLs;" & root & "\Scripts;%PATH% && """ & root & "\Scripts\osdagbridge.exe"""""

objShell.Run cmd, 0
