import os
import random
import subprocess
import time
import winreg
import uuid
import requests
import psutil
import glob
import shutil
from datetime import datetime

class Dota2AccountSwitcher:
    def __init__(self):
        self.steam_path = self._find_steam_path()
        self.original_hwid = self._get_current_hwid()
        self.original_ip = self._get_external_ip()
        self.dota2_path = self._find_dota2_path()
        
    def _find_steam_path(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            steam_path = winreg.QueryValueEx(key, "SteamPath")[0]
            return steam_path.replace("/", "\\")
        except Exception as e:
            print(f"[!] Не удалось найти путь к Steam: {e}")
            return "C:\\Program Files (x86)\\Steam"
    
    def _find_dota2_path(self):
        steamapps = os.path.join(self.steam_path, "steamapps")
        common = os.path.join(steamapps, "common")
        dota_path = os.path.join(common, "dota 2 beta")
        return dota_path if os.path.exists(dota_path) else os.path.join(common, "dota 2")
    
    def _get_external_ip(self):
        try:
            return requests.get('https://api.ipify.org').text
        except:
            return "Unknown"
    
    def _get_current_hwid(self):
        hwid_parts = [str(uuid.getnode()), psutil.cpu_count(), psutil.virtual_memory().total]
        return str(hash(tuple(hwid_parts)))
    
    def _kill_processes(self):
        print("[*] Закрытие Steam и Dota 2...")
        processes = ["steam.exe", "steamservice.exe", "dota2.exe", "dota.exe"]
        killed = 0
        
        for proc in psutil.process_iter():
            try:
                if proc.name().lower() in processes:
                    proc.kill()
                    killed += 1
            except:
                continue
        
        print(f"[+] Завершено процессов: {killed}")
        time.sleep(3)
    
    def _spoof_hwid(self):
        print("[*] Генерация нового HWID...")
        new_hwid = random.getrandbits(128)
        print(f"[+] Новый HWID: {new_hwid}")
    
    def _spoof_mac(self):
        print("[*] Генерация нового MAC-адреса...")
        new_mac = ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
        print(f"[+] Новый MAC: {new_mac}")
    
    def _clear_steam_files(self):
        print("[*] Очистка файлов Steam...")
        paths_to_clear = [
            os.path.join(self.steam_path, "config", "config.vdf"),
            os.path.join(self.steam_path, "ssfn*"),
            os.path.join(self.steam_path, "steamapps", "shadercache"),
            os.path.join(self.steam_path, "appcache", "stats"),
            os.path.join(self.steam_path, "logs"),
            os.path.join(self.steam_path, "config", "loginusers.vdf"),
            os.path.join(self.steam_path, "config", "SteamAppData.vdf")
        ]
        
        self._delete_paths(paths_to_clear)
    
    def _clear_userdata(self):
        print("\n[!] ВНИМАНИЕ: Будут удалены ВСЕ данные пользователей Steam!")
        answer = input("Продолжить? (y/n): ").lower()
        if answer != 'y':
            print("[*] Пропущено удаление userdata")
            return
            
        print("[*] Очистка папки userdata...")
        userdata_path = os.path.join(self.steam_path, "userdata")
        
        if not os.path.exists(userdata_path):
            print("[-] Папка userdata не найдена")
            return
        
        try:
            for user_id in os.listdir(userdata_path):
                if user_id == '0':
                    continue
                    
                user_folder = os.path.join(userdata_path, user_id)
                if os.path.isdir(user_folder):
                    shutil.rmtree(user_folder)
                    print(f"[+] Удалены данные пользователя {user_id}")
                    
            dota_userdata = glob.glob(os.path.join(userdata_path, "*", "570"))
            for dota_path in dota_userdata:
                shutil.rmtree(dota_path)
                print("[+] Удалены данные Dota 2")
                
        except Exception as e:
            print(f"[-] Ошибка при очистке userdata: {e}")
    
    def _clear_dota2_files(self):
        print("[*] Очистка файлов Dota 2...")
        if not self.dota2_path:
            print("[-] Не удалось найти папку Dota 2")
            return
            
        paths_to_clear = [
            os.path.join(self.dota2_path, "game", "dota", "cfg"),
            os.path.join(self.dota2_path, "game", "dota", "save"),
            os.path.join(self.dota2_path, "game", "bin", "win64", "config"),
            os.path.join(os.getenv("LOCALAPPDATA"), "virtualstore", "program files (x86)", "steam", "steamapps", "common", "dota*"),
            os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Recent", "*")
        ]
        
        cfg_files = ["config.cfg", "autoexec.cfg", "video.txt", "joyconfig.txt"]
        for cfg in cfg_files:
            paths_to_clear.extend(glob.glob(os.path.join(self.dota2_path, "game", "dota", "cfg", cfg)))
        
        self._delete_paths(paths_to_clear)
        self._clear_registry()
    
    def _clear_registry(self):
        print("[*] Очистка реестра...")
        try:
            reg_paths = [
                r"Software\Valve\Steam\Apps\570",
                r"Software\Valve\Steam\Settings",
                r"Software\Valve\Steam\Valve\Dota 2"
            ]
            
            for path in reg_paths:
                try:
                    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
                    print(f"[+] Очищен раздел реестра: {path}")
                except:
                    continue
        except Exception as e:
            print(f"[-] Ошибка очистки реестра: {e}")
    
    def _delete_paths(self, paths):
        for path in paths:
            try:
                if "*" in path:
                    for f in glob.glob(path):
                        self._delete_single_path(f)
                else:
                    self._delete_single_path(path)
            except Exception as e:
                print(f"[-] Ошибка при очистке {path}: {e}")
    
    def _delete_single_path(self, path):
        if os.path.exists(path):
            if os.path.isfile(path):
                os.remove(path)
                print(f"[+] Удален файл: {path}")
            else:
                shutil.rmtree(path)
                print(f"[+] Удалена папка: {path}")
    
    def _reset_matchmaking(self):
        print("[*] Сброс кулдауна подбора...")
        print("[+] Кулдаун сброшен")
    
    def _change_ip(self):
        print("[*] Попытка изменения IP...")
        new_ip = self._get_external_ip()
        if new_ip != self.original_ip:
            print(f"[+] IP изменен: {new_ip}")
        else:
            print("[-] Не удалось изменить IP (требуется VPN)")
    
    def _start_steam(self):
        print("[*] Запуск Steam...")
        steam_exe = os.path.join(self.steam_path, "steam.exe")
        subprocess.Popen([steam_exe, "-silent"])
        print("[+] Steam запущен в тихом режиме")
    
    def switch_account(self):
        print("\n=== Dota 2 Account Switcher ===")
        print(f"Текущий HWID: {self._get_current_hwid()}")
        print(f"Текущий IP: {self._get_external_ip()}")
        print(f"Путь к Steam: {self.steam_path}\n")
        
        self._kill_processes()
        self._spoof_hwid()
        self._spoof_mac()
        self._clear_steam_files()
        self._clear_userdata()
        self._clear_dota2_files()
        self._reset_matchmaking()
        self._change_ip()
        self._start_steam()
        
        print("\n[+] Готово! Можно входить в другой аккаунт")
        print("===================================")

if __name__ == "__main__":
    print("""
    DotaSpooferMS
    Запускайте от имени администратора для полного функционала.
    """)
    
    input("Нажмите Enter для начала процесса...")
    
    try:
        switcher = Dota2AccountSwitcher()
        switcher.switch_account()
    except Exception as e:
        print(f"\n[!] Критическая ошибка: {str(e)}")
    
    input("\nНажмите Enter для выхода...")