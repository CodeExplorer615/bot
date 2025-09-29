import subprocess

# Запускаем первый бот
p1 = subprocess.Popen(["python3", "pas.py"])

# Запускаем второй бот
p2 = subprocess.Popen(["python3", "mvdpasbot.py"])

# Ждём, чтобы оба процесса работали
p1.wait()
p2.wait()

