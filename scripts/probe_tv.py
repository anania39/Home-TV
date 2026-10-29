import socket
import sys

ip = "192.168.50.249"
print(f"Probing {ip}...")
for port in [38400, 8008, 8080, 8000, 80, 5000, 3000, 7676, 9080]:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.8)
    res = s.connect_ex((ip, port))
    if res == 0:
        print(f"  Port {port}: OPEN")
    s.close()

# Also scan other IPs on 192.168.50.x that might be the TV
import subprocess
print("\nPinging subnet to populate ARP...")
for last_octet in range(2, 255):
    target = f"192.168.50.{last_octet}"
    if target == "192.168.50.250":
        continue
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.05)
    if s.connect_ex((target, 38400)) == 0:
        print(f"FOUND HISENSE TV (Port 38400 OPEN) at: {target}!")
    elif s.connect_ex((target, 8008)) == 0:
        print(f"FOUND GOOGLE TV / DIAL (Port 8008 OPEN) at: {target}!")
    s.close()
print("Scan complete.")
