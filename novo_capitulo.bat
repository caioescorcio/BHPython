@echo off
setlocal enabledelayedexpansion

rem Encontra a maior pasta cX
set max=0
for /d %%d in (c*) do (
    set name=%%~nxd
    if "!name:~0,1!" == "c" (
        set num=!name:~1!
        if !num! gtr !max! (
            set max=!num!
        )
    )
)

rem Incrementa X e cria a nova pasta e arquivo
set /a new_num=max+1
set new_folder=c%new_num%
md "!new_folder!"
echo # Capitulo %new_num% > "!new_folder!\Capitulo_%new_num%.md"

rem Executa os comandos na nova pasta
cd "!new_folder!"
mkdir codigos
cd codigos
python -m venv venv3
call .\venv3\Scripts\activate.bat

endlocal
