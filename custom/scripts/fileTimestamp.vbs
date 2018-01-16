' SUMMARY
' fileTimestamp.vbs

' This script loops given folder's subfolders recursively
' and returns the latest timestamp it can find
' PARAMS
' starting folder
' RETURNS
' timestamp in seconds (unix time) in UTC time

Public latestTime 'the latest timestamp from all subfolders' files
Dim objFSO, objFolder, startFolder

On Error Resume Next

Set objFSO = CreateObject("Scripting.FileSystemObject")
startFolder = Replace(WScript.Arguments(0),"/","\")
'startFolder = "f:\startFolder" 'for testing

Set objFolder = objFSO.GetFolder(startFolder)
'checking that the given path exists
If Err.Number <> 0 Then
    WScript.StdOut.Write "Error: " & Err.Description & " (" & Err.Number & ")"
    WScript.Quit Err.Number
End If

Set colFiles = objFolder.Files

'goes through given folder's subfolders and hunts for the latest timestamp
ShowSubFolders objFSO.GetFolder(startFolder)

'sets the latest local timestamp to UTC time
Set dateTime = CreateObject("WbemScripting.SWbemDateTime")    
dateTime.SetVarDate (latestTime)

'writes the latest timestamp in unix time (seconds from 1.1.1970)
WScript.StdOut.Write DateDiff("s", "1/1/1970", dateTime.GetVarDate (false))

'Method that loops given folder's subfolders recursively
Sub ShowSubFolders(Folder)

    Set objFSO = CreateObject("Scripting.FileSystemObject")
	
    For Each Subfolder In Folder.SubFolders
	
        Set objFolder = objFSO.GetFolder(Subfolder.Path)
		
        'going to loop files only if there are any
        If objFolder.Files.Count > 0 Then

            Set colFiles = objFolder.Files
			
            For Each objFile In colFiles

                'check if file is the latest so far
                If DateDiff("s", objFile.DateLastModified, latestTime) < 0 Then
                    latestTime = objFile.DateLastModified
                End If

            Next

        End If

        'recursively starts another folder check
        ShowSubFolders Subfolder

    Next

End Sub

'checking if other errors have occured
If Err.Number <> 0 Then
    WScript.StdOut.Write "Error: " & Err.Description & " (" & Err.Number & ")"
    WScript.Quit Err.Number
End If
