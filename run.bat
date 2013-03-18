@ECHO OFF

SET pvis_port=8500
SET pvis_addr=0.0.0.0
SET pvis_daemon=0
SET pvis_pass=
SET pvis_cmdmode=
GOTO :parse_args

:parse_arg
	IF "%pvis_cmdmode%"=="" (
		IF "%1"=="--daemon" (
			SET pvis_daemon=1
		) ELSE (
			IF "%1"=="--stop-daemon" (
				env\Scripts\pserve.exe --stop-daemon --pid-file=daemon.pid
				GOTO :end
			) ELSE (
				IF "%1"=="--port" (
					SET pvis_cmdmode=port
				) ELSE (
					IF "%1"=="--address" (
						SET pvis_cmdmode=address
					) ELSE (
						SET pvis_pass=%pvis_pass%^ %1
					)
				)
			)
		)
	) ELSE (
		IF "%pvis_cmdmode%"=="port" (
			SET pvis_port=%1
		) ELSE (
			IF "%pvis_cmdmode%"=="address" (
				SET pvis_addr=%1
			) ELSE (
				ECHO "Internal error"
			)
		)
		SET pvis_cmdmode=
	)
	goto :eof

:parse_args
	FOR %%G IN (%*) DO (CALL :parse_arg %%G)
	SET pvis_cmdmode=

IF %pvis_daemon% EQU% 0 (
	env\Scripts\python.exe protvis\server.py %pvis_addr% %pvis_port% %pvis_pass%
) ELSE (
	env\Scripts\pserve.exe production.ini start --pid-file=daemon.pid http_port=%pvis_port% http_address=%pvis_addr% %pvis_pass%
)

SET pvis_port=
SET pvis_addr=
SET pvis_daemon=
SET pvis_pass=