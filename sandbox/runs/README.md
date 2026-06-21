# Sandbox runs

Папка для raw runtime logs будущих разрешённых запусков.

Сейчас execute не разрешён. Эта папка существует заранее, чтобы формат был понятен до появления runner-а.

Если когда-нибудь запуск будет разрешён, каждый run должен иметь:

- source id;
- run id;
- task id;
- agent id;
- точную команду;
- image/VM;
- network mode;
- mounts;
- CPU/RAM/PID/disk limits;
- timeout;
- exit code;
- список созданных файлов;
- ссылку на summary report.

Raw logs не коммитятся.
