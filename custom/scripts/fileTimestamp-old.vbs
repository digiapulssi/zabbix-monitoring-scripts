' SUMMARY
' fileTimestamp.vbs

' This script loops given folder's subfolders recursively.
' If there are files, it checks the latest timestamp of these files.
' During looping folders and files, it constructs json format output
' PARAMS
' starting folder
' RETURNS
' json format output: folder path and the latest timestamp of files in that folder

Public public_counterPilkku	'public variable is needed to handle the comma after "the first data row" in the json output
Dim objFSO, objFolder, startFolder

On Error Resume Next

Set objFSO = CreateObject("Scripting.FileSystemObject")
startFolder = WScript.Arguments(0)
'startFolder = "f:\startFolder" 'for testing

Set objFolder = objFSO.GetFolder(startFolder)
'checking that given path exists
If Err.Number <> 0 Then
		WScript.StdOut.Write "Error: " & Err.Description & " (" & Err.Number & ")"
		WScript.Quit Err.Number
End If

Set colFiles = objFolder.Files

'writes the beginning characters into json output
WScript.StdOut.Write "{""data"":["

'goes through given folder's subfolders and writes the json output data
ShowSubFolders objFSO.GetFolder(startFolder)

'writes the final characters into json output
WScript.StdOut.Write "]}"

'Method that loops given folder's subfolders recursively
Sub ShowSubFolders(Folder)

    Dim latestTime, currentTime
    Dim counterFiles

    Set objFSO = CreateObject("Scripting.FileSystemObject")

		'loops folders
		For Each Subfolder In Folder.SubFolders

        Set objFolder = objFSO.GetFolder(Subfolder.Path)

				'going to loop files only if there are any
				If objFolder.Files.Count > 0 Then

						Set colFiles = objFolder.Files
		        counterFiles = 0

						'writes comma after the first "data row"
						If public_counterPilkku > 0 Then
								WScript.StdOut.Write ",{ ""{#FOLDER}"":""" & Subfolder.Path & ""","
						Else
								WScript.StdOut.Write "{ ""{#FOLDER}"":""" & Subfolder.Path & ""","
						End If

						public_counterPilkku = public_counterPilkku + 1

						'loops files
		        For Each objFile In colFiles

								'handles the latest timestamp
			          If counterFiles = 0 Then
			          	latestTime = objFile.DateLastModified
			          Else
			            currentTime = objFile.DateLastModified

									'compares two dates and returns their difference in seconds
									'minus value means newer timestamp
			            If DateDiff("s", currentTime, latestTime) < 0 Then
			            	latestTime = currentTime
			            End If
			          End If

		            counterFiles = counterFiles + 1

						Next

						'writes the latest timestamp after all files are gone through
	        	WScript.StdOut.Write """{#TIME}"":""" & latestTime & """}"

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
