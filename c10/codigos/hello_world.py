import tkinter as tk
from tkinter import messagebox

def show_popup():
    messagebox.showinfo("Mensagem", "Hello, World!")

# Criar a janela principal
root = tk.Tk()
root.title("Exemplo Pop-up")

# Botão para exibir o pop-up
btn = tk.Button(root, text="Mostrar Pop-up", command=show_popup)
btn.pack(pady=20)

# Executar a janela
root.mainloop()
