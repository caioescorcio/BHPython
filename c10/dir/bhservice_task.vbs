' Substituindo MsgBox por um log
Dim objFSO, objFile
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFile = objFSO.OpenTextFile("C:\Users\caioe\Documents\Projetos\BHPython\c10\temp\log.txt", 8, True)

objFile.WriteLine "AHAHAHAHAHAHAHAAH - Executado em " & Now
objFile.Close
