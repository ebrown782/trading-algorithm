import tkinter as tk
from tkinter import scrolledtext
import logging
from trading_algorithm import start_trading, stop_trading

# Setup logging to display in the GUI
class TextHandler(logging.Handler):
    def __init__(self, text_widget):
        logging.Handler.__init__(self)
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        def append():
            self.text_widget.configure(state='normal')
            self.text_widget.insert(tk.END, msg + '\n')
            self.text_widget.configure(state='disabled')
            self.text_widget.yview(tk.END)
        self.text_widget.after(0, append)

# Create the GUI
def create_gui():
    root = tk.Tk()
    root.title("Trading Algorithm")

    frame = tk.Frame(root)
    frame.pack(pady=20)

    start_button = tk.Button(frame, text="Start Trading", command=start_trading)
    start_button.grid(row=0, column=0, padx=10)

    stop_button = tk.Button(frame, text="Stop Trading", command=stop_trading)
    stop_button.grid(row=0, column=1, padx=10)

    log_frame = tk.Frame(root)
    log_frame.pack(pady=10)

    log_text = scrolledtext.ScrolledText(log_frame, state='disabled', width=80, height=20)
    log_text.pack()

    # Setup logging to the GUI
    text_handler = TextHandler(log_text)
    text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(text_handler)
    logging.getLogger().setLevel(logging.INFO)

    root.mainloop()

if __name__ == "__main__":
    create_gui()
