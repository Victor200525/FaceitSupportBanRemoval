import asyncio
import tkinter as tk
from tkinter import messagebox, scrolledtext
from PIL import Image, ImageTk
import threading
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import sys

# 🔧 Универсальный путь к ресурсам (картинкам), работает в .exe и .py
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class FaceitBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("FACEIT Ban Removal")
        self.root.geometry("600x550")
        self.root.configure(bg="#222222")
        self.root.resizable(False, False)

        # 📷 Загружаем логотип
        logo_path = resource_path("faceit_logo.png")
        try:
            resample_mode = Image.Resampling.LANCZOS
        except AttributeError:
            resample_mode = Image.ANTIALIAS

        logo_img = Image.open(logo_path)
        logo_img = logo_img.resize((100, 100), resample_mode)
        self.logo_photo = ImageTk.PhotoImage(logo_img)

        logo_label = tk.Label(root, image=self.logo_photo, bg="#222222")
        logo_label.pack(pady=(15, 10))

        title = tk.Label(root, text="FACEIT Ban Removal",
                         font=("Segoe UI", 16, "bold"), fg="white", bg="#222222")
        title.pack(pady=(0, 15))

        frame = tk.Frame(root, bg="#333333", padx=20, pady=20)
        frame.pack(padx=30, pady=15, fill="x")

        tk.Label(frame, text="Email:", font=("Segoe UI", 11), fg="white", bg="#333333").grid(row=0, column=0, sticky="w")
        self.email_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.email_var, width=50, font=("Segoe UI", 11)).grid(row=1, column=0, pady=(0,15))

        tk.Label(frame, text="FACEIT Profile URL:", font=("Segoe UI", 11), fg="white", bg="#333333").grid(row=2, column=0, sticky="w")
        self.profile_url_var = tk.StringVar()
        tk.Entry(frame, textvariable=self.profile_url_var, width=50, font=("Segoe UI", 11)).grid(row=3, column=0, pady=(0,15))

        self.submit_btn = tk.Button(root, text="Отправить заявку", font=("Segoe UI", 12, "bold"), bg="#ff5a00", fg="white",
                                    activebackground="#ff7a00", activeforeground="white", command=self.toggle_bot)
        self.submit_btn.pack(pady=10, ipadx=10, ipady=5)

        self.log_box = scrolledtext.ScrolledText(root, height=10, state='disabled', font=("Consolas", 10),
                                                 bg="#1e1e1e", fg="lime")
        self.log_box.pack(fill='both', expand=True, padx=20, pady=(10, 15))

        self.bot_running = False

    def log(self, message):
        self.log_box.configure(state='normal')
        self.log_box.insert(tk.END, f"{message}\n")
        self.log_box.configure(state='disabled')
        self.log_box.yview(tk.END)

    def thread_safe_log(self, message):
        self.root.after(0, self.log, message)

    def toggle_bot(self):
        if self.bot_running:
            self.bot_running = False
            self.thread_safe_log("[*] Остановка процесса по запросу пользователя...")
            self.submit_btn.config(text="Отправить заявку")
        else:
            email = self.email_var.get().strip()
            profile_url = self.profile_url_var.get().strip()

            if not email or not profile_url:
                messagebox.showerror("Ошибка", "Введите Email и ссылку на профиль.")
                return

            self.bot_running = True
            self.submit_btn.config(text="Остановить")
            threading.Thread(target=self.run_bot, args=(email, profile_url), daemon=True).start()

    def run_bot(self, email, profile_url):
        try:
            asyncio.run(self.fill_faceit_form(email, profile_url))
        except asyncio.CancelledError:
            self.thread_safe_log("[*] Асинхронная операция была прервана.")
        finally:
            self.bot_running = False
            self.root.after(0, lambda: self.submit_btn.config(text="Отправить заявку"))

    async def fill_faceit_form(self, email, profile_url):
        def check_running():
            if not self.bot_running:
                self.thread_safe_log("[*] Процесс остановлен.")
                raise asyncio.CancelledError()

        descriptions = [
            "I've tried to connect for 4 times but server just didn't let me in",
            "I couldn't join because of an unknown server error, faceit AC was on",
            "It was literally not my fault, I have tried multiple times but the match didn't let me in"
        ]

        profile_folder = "my_profile"
        profile_path = os.path.abspath(profile_folder)
        os.makedirs(profile_path, exist_ok=True)

        try:
            check_running()
            self.thread_safe_log("[*] Запускаю Chrome с пользовательским профилем...")
            service = Service(ChromeDriverManager().install())
            options = webdriver.ChromeOptions()
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--profile-directory=Default")
            options.add_argument("--disable-notifications")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-blink-features=AutomationControlled")
            #options.add_argument("window-position=-32000,-32000")  # Скрыть за пределы экрана
            #options.add_argument("window-size=800,600")

            driver = webdriver.Chrome(service=service, options=options)
            driver.minimize_window()
            wait = WebDriverWait(driver, 10)

            check_running()
            self.thread_safe_log("[1] Переход на страницу поддержки FACEIT...")
            driver.get("https://support.faceit.com/hc/en-us/requests/new")
            time.sleep(5)

            check_running()
            await asyncio.sleep(0)
            wait.until(EC.presence_of_element_located((By.ID, "request_anonymous_requester_email")))

            self.thread_safe_log("[2] Ввод email...")
            driver.find_element(By.ID, "request_anonymous_requester_email").send_keys(email)
            time.sleep(random.uniform(1, 2))

            self.thread_safe_log("[3] Выбор причины (I am banned)...")
            driver.execute_script("""
                var el = document.getElementById('request_custom_fields_26697809');
                el.value = 'i_am_banned____afk/leaver_ban';
                el.dispatchEvent(new Event('change'));
            """)
            time.sleep(random.uniform(1, 2))

            self.thread_safe_log("[4] Указание игры (CS2)...")
            driver.execute_script("document.getElementById('request_custom_fields_360000521599').value = 'cs2';")
            time.sleep(random.uniform(1, 2))

            self.thread_safe_log("[5] Вставка ссылки на профиль...")
            driver.find_element(By.ID, "request_custom_fields_360000516280").send_keys(profile_url)
            time.sleep(random.uniform(1, 2))

            self.thread_safe_log("[6] Указание региона (Europe)...")
            driver.execute_script("document.getElementById('request_custom_fields_14872816896284').value = 'region_eu';")
            time.sleep(random.uniform(1, 2))

            self.thread_safe_log("[7] Заполнение темы обращения...")
            driver.find_element(By.ID, "request_subject").send_keys("Not able to connect to server")
            time.sleep(random.uniform(1, 2))

            self.thread_safe_log("[8] Вставка описания...")
            driver.find_element(By.ID, "request_description").send_keys(random.choice(descriptions))
            time.sleep(random.uniform(1, 2))

            self.thread_safe_log("[9] Отправка формы...")
            driver.find_element(By.NAME, "commit").click()
            time.sleep(3)

            try:
                wait.until(EC.url_contains("requests"))
                self.thread_safe_log("✅ Форма успешно отправлена!")
            except TimeoutException:
                self.thread_safe_log("⚠ Не удалось подтвердить отправку формы.")

        except asyncio.CancelledError:
            self.thread_safe_log("[*] Процесс был остановлен.")
        except Exception as e:
            self.thread_safe_log(f"❌ Ошибка: {str(e)}")
        finally:
            if 'driver' in locals():
                driver.quit()
                self.thread_safe_log("[✔] Браузер закрыт.")


if __name__ == "__main__":
    root = tk.Tk()
    app = FaceitBotGUI(root)
    root.mainloop()
