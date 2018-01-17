' SCRIPT NAME
' fileTimestamp.vbs
' SUMMARY
' This script loops given folder's subfolders recursively
' and returns the latest timestamp it can find, also from starting folder
' PARAMS
' starting folder
' RETURNS
' timestamp in seconds (unix time) in UTC time
' If starting folder doesn't exist, returns 0.
' If some other error occurs, returns compiler's error message and code.

Public latestTime 'the latest timestamp from all folders' files
Dim objFSO, objFolder, startFolder

On Error Resume Next

Set objFSO = CreateObject("Scripting.FileSystemObject")
startFolder = Replace(WScript.Arguments(0),"/","\")
'startFolder = "f:\startFolder" 'for testing

Set objFolder = objFSO.GetFolder(startFolder)
'checking that the given path exists
If Err.Number <> 0 Then
    'if path doesn't exist, returns 0
    WScript.StdOut.Write 0
    WScript.Quit
End If

'goes through given folder's subfolders and hunts for the latest timestamp
FindLatestTimestamp objFolder

'sets the latest local timestamp to UTC time
Set dateTime = CreateObject("WbemScripting.SWbemDateTime")
dateTime.SetVarDate(latestTime)

'writes the latest timestamp in unix time (seconds from 1.1.1970)
WScript.StdOut.Write DateDiff("s", "1/1/1970", dateTime.GetVarDate(false))

'Method that loops given folder's subfolders recursively and finds the latest timestamp of all files
Sub FindLatestTimestamp(Folder)

	'first check the files for given folder
	Set objFolder = objFSO.GetFolder(Folder)
    If objFolder.Files.Count > 0 Then

        Set colFiles = objFolder.Files

        For Each objFile In colFiles
            'check if the file is the latest so far
            If DateDiff("s", objFile.DateLastModified, latestTime) < 0 Then
                latestTime = objFile.DateLastModified
            End If
        Next

    End If

    'then recursively start to check another folder
    For Each Subfolder In Folder.SubFolders
        FindLatestTimestamp Subfolder
    Next

End Sub

'checking if other errors have occurred
If Err.Number <> 0 Then
    WScript.StdOut.Write "Error: " & Err.Description & " (" & Err.Number & ")"
    WScript.Quit
End If
