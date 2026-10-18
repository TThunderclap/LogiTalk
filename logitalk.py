import threading
from socket import *
from customtkinter import *
from PIL import Image


class MainWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry('400x300')

        self.label = None
        self.entry = None

        # Панель меню
        self.menu_frame = CTkFrame(self, width=30, height=300)
        self.menu_frame.pack_propagate(False)
        self.menu_frame.place(x=0, y=0)

        self.is_show_menu = False
        self.speed_animate_menu = -5

        self.btn = CTkButton(self, text='▶️', command=self.toggle_show_menu, width=30)
        self.btn.place(x=0, y=0)

        # Основний інтерфейс чату
        self.chat_field = CTkTextbox(self, font=('Arial', 14, 'bold'), state='disabled')
        self.chat_field.place(x=0, y=0)

        self.message_entry = CTkEntry(self, placeholder_text='Введіть повідомлення:', height=40)
        self.message_entry.place(x=0, y=0)

        self.send_button = CTkButton(self, text='>', width=50, height=40, command=self.send_message)
        self.send_button.place(x=0, y=0)

        # Відправка клавішею Enter
        self.message_entry.bind('<Return>', lambda event: self.send_message())

        self.username = 'Роман'
        self.sock = None

        # Підключення до локального тестового сервера
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.connect(('4.tcp.eu.ngrok.io', 15691))
            hello = f"TEXT@{self.username}@[SYSTEM] {self.username} приєднався(лась) до чату!\n"
            self.sock.sendall(hello.encode('utf-8'))
            threading.Thread(target=self.recv_message, daemon=True).start()
            self.add_message("[Система]: Успішно підключено до сервера.")
        except Exception as e:
            self.sock = None
            self.add_message(f"Не вдалося підключитися до сервера: {e}")

        # Додавання логотипа
        try:
            image = Image.open(r"C:\Users\Excalibur\Pictures\logichatlogo.png")
            img_ctk = CTkImage(light_image=image, size=(200, 200))
            self.logo_label = CTkLabel(self, text="", image=img_ctk)
            self.logo_label.place(relx=1.0, rely=0.0, anchor="ne")
        except Exception:
            pass

        self.adaptive_ui()

    def toggle_show_menu(self):
        if self.is_show_menu:
            self.is_show_menu = False
            self.speed_animate_menu = -10
            self.btn.configure(text='▶️')
            self.show_menu()
        else:
            self.is_show_menu = True
            self.speed_animate_menu = 10
            self.btn.configure(text='◀️')
            self.show_menu()

            if not self.label:
                self.label = CTkLabel(self.menu_frame, text='Імʼя')
                self.label.pack(pady=30)
                self.entry = CTkEntry(self.menu_frame)
                self.entry.pack()

    def show_menu(self):
        current_width = self.menu_frame.winfo_width()
        new_width = current_width + self.speed_animate_menu

        if self.is_show_menu and current_width < 200:
            self.menu_frame.configure(width=min(new_width, 200))
            self.after(10, self.show_menu)
        elif not self.is_show_menu and current_width > 30:
            self.menu_frame.configure(width=max(new_width, 30))
            self.after(10, self.show_menu)
            if current_width <= 40 and self.label and self.entry:
                self.label.destroy()
                self.entry.destroy()
                self.label = None
                self.entry = None

    def adaptive_ui(self):
        menu_w = self.menu_frame.winfo_width()
        win_w = self.winfo_width()
        win_h = self.winfo_height()

        self.menu_frame.configure(height=win_h)
        self.chat_field.place(x=menu_w, y=0)
        self.chat_field.configure(
            width=max(win_w - menu_w, 10),
            height=max(win_h - 40, 10)
        )

        self.send_button.place(x=win_w - 50, y=win_h - 40)
        self.message_entry.place(x=menu_w, y=win_h - 40)
        self.message_entry.configure(
            width=max(win_w - menu_w - 50, 10)
        )

        self.after(50, self.adaptive_ui)

    def add_message(self, text):
        def update_chat():
            self.chat_field.configure(state='normal')
            self.chat_field.insert(END, text + '\n')
            self.chat_field.configure(state='disabled')
            self.chat_field.see(END)

        self.after(0, update_chat)

    def send_message(self):
        message = self.message_entry.get().strip()
        if not message:
            return

        # Перевірка наявності сокету
        if not self.sock:
            self.add_message("[Помилка відправки]: Немає з'єднання з сервером.")
            return

        data = f"TEXT@{self.username}@{message}\n"
        try:
            self.sock.sendall(data.encode('utf-8'))
            # Локальне відображення власного повідомлення
            self.add_message(f"{self.username}: {message}")
            self.message_entry.delete(0, END)
        except Exception as e:
            self.add_message(f"[Помилка відправки]: {e}")
            if self.sock:
                try:
                    self.sock.close()
                except:
                    pass
                self.sock = None

    def recv_message(self):
        buffer = ""
        while True:
            try:
                if not self.sock:
                    break
                chunk = self.sock.recv(4096)
                if not chunk:
                    self.add_message("[Система]: З'єднання з сервером розірвано.")
                    break
                buffer += chunk.decode('utf-8', errors='ignore')

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except Exception:
                break

        # Коректне закриття дескриптора сокета
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

    def handle_line(self, line):
        if not line:
            return

        parts = line.split("@", 2)
        msg_type = parts[0]

        if msg_type == "TEXT" and len(parts) >= 3:
            author = parts[1]
            message = parts[2]
            # Ігноруємо дублювання власного тексту, якщо сервер поверне його назад
            if author == self.username:
                return
            self.add_message(f"{author}: {message}")
        elif msg_type == "IMAGE" and len(parts) >= 3:
            author = parts[1]
            filename = parts[2]
            self.add_message(f"{author} надіслав(ла) зображення: {filename}")
        elif msg_type == "SYSTEM" and len(parts) >= 2:
            self.add_message(f"[СИСТЕМА]: {parts[1]}")
        else:
            self.add_message(line)


if __name__ == "__main__":
    win = MainWindow()
    win.mainloop()