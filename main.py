import queue
import logging
import signal
import tkinter as tk
import tkinter.messagebox as tkm
from tkinter.scrolledtext import ScrolledText
from tkinter import ttk, VERTICAL, HORIZONTAL, N, S, E, W
from time import sleep


logger = logging.getLogger(__name__)


class QueueHandler(logging.Handler):
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(record)


class ConsoleUi:
    def __init__(self, frame):
        self.frame = frame

        # Create ScrolledText widget.
        self.scrolled_text = ScrolledText(frame, state="disabled", height=12)
        self.scrolled_text.grid(row=0, column=0, sticky=(N, S, W, E))
        self.scrolled_text.configure(font="TkFixedFont")
        self.scrolled_text.tag_config('INFO', foreground='black')
        self.scrolled_text.tag_config('DEBUG', foreground='gray')
        self.scrolled_text.tag_config('WARNING', foreground='orange')
        self.scrolled_text.tag_config('ERROR', foreground='red')
        self.scrolled_text.tag_config('CRITICAL', foreground='red', underline=1)

        # Create a logging handler using a queue.
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)

        # Configuring the log format.
        formatter = logging.Formatter('%(asctime)s: %(message)s')
        self.queue_handler.setFormatter(formatter)

        # Add handler to logger.
        logger.addHandler(self.queue_handler)

        # Polling messages from queue.
        self.frame.after(100, self.poll_log_queue)

    def display(self, record):
        # You need to set state="normal" to be able to write. Therefore, set "normal" temporarily.
        self.scrolled_text.configure(state="normal")

        msg = self.queue_handler.format(record)
        
        # Pass the log to scrolled_text using the insert function, passing the tag as the third argument (INFO, WARNING, etc.)
        self.scrolled_text.insert(tk.END, record.levelname + ":" + msg + "\n", record.levelname)

        # Set it back to "disabled" again to prevent users from editing it.
        self.scrolled_text.configure(state='disabled')

        # Auto scroll
        self.scrolled_text.yview(tk.END)

    def poll_log_queue(self):
        # Check if the message to be displayed exists in the queue every 100msec.
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.display(record)
        self.frame.after(100, self.poll_log_queue)

    def copy_clipboard(self):
        self.scrolled_text.clipboard_append(self.scrolled_text.get("1.0", tk.END))
        tkm.showinfo("Copy to clipboard", "Copied log to clipboard.")

    def clear_log(self):
        if tkm.askyesno("Clear log", "Are you sure you want to delete the log?") is True:
            self.scrolled_text.configure(state='normal')
            self.scrolled_text.delete("1.0", tk.END)
            self.scrolled_text.configure(state='disabled')


class InputLogUi:

    def __init__(self, frame):
        self.frame = frame
        tk.Label(self.frame, text="Input log message you want to output").grid(column=0, row=1, sticky=W)
        log_form = tk.Entry(self.frame)
        log_form.grid(column=0, row=2, sticky=W)
        tk.Button(self.frame, text="DEBUG", width=10, command=lambda: self.log(logging.DEBUG, log_form.get())).grid(column=0, row=3, sticky=W)
        tk.Button(self.frame, text="INFO", width=10, command=lambda: self.log(logging.INFO, log_form.get())).grid(column=0, row=4, sticky=W)
        tk.Button(self.frame, text="WARN", width=10, command=lambda: self.log(logging.WARNING, log_form.get())).grid(column=0, row=5, sticky=W)
        tk.Button(self.frame, text="ERROR", width=10, command=lambda: self.log(logging.ERROR, log_form.get())).grid(column=0, row=6, sticky=W)
        tk.Button(self.frame, text="CRITICAL", width=10, command=lambda: self.log(logging.CRITICAL, log_form.get())).grid(column=0, row=7, sticky=W)
        tk.Button(self.frame, text="ALL", width=10, command=lambda: self.all_log(log_form.get())).grid(column=0, row=8, sticky=W)
    
    def log(self, level, log_msg):
        logger.log(level, log_msg)

    def all_log(self, log_msg):
        log_levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]

        # In this case, the logs will be displayed together at the end.
        for level in log_levels:
            self.log(level, log_msg)
            sleep(1)


class LogUtilsUi:

    def __init__(self, frame, copy_clipboard, clear_log):
        self.frame = frame
        tk.Button(self.frame, text="Clipboard Copy", width=20, command=copy_clipboard).grid(column=0, row=3, sticky=W)
        tk.Button(self.frame, text="Clear log", width=20, command=clear_log).grid(column=0, row=4, sticky=W)

class App:

    def __init__(self, root):
        self.root = root
        root.title("Sample Logging Handler")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Create PanedWindow.
        vertical_pane = ttk.PanedWindow(self.root, orient=VERTICAL)
        vertical_pane.grid(row=0, column=0, sticky="nsew")
        horizontal_pane = ttk.PanedWindow(vertical_pane, orient=HORIZONTAL)
        vertical_pane.add(horizontal_pane)

        # Create Console frame.
        console_frame = ttk.Labelframe(horizontal_pane, text="Console")
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        horizontal_pane.add(console_frame, weight=1)

        input_log_frame = ttk.Labelframe(vertical_pane, text="Log Input Form")
        vertical_pane.add(input_log_frame, weight=1)

        log_utils_frame = ttk.Labelframe(vertical_pane, text="Log Utils")
        vertical_pane.add(log_utils_frame, weight=1)

        self.console = ConsoleUi(console_frame)
        self.input_log = InputLogUi(input_log_frame)
        self.log_utils = LogUtilsUi(log_utils_frame, self.console.copy_clipboard, self.console.copy_clipboard)
        self.log_utils = LogUtilsUi(log_utils_frame, self.console.copy_clipboard, self.console.clear_log)

        # Handling of application termination.
        self.root.protocol('WM_DELETE_WINDOW', self.quit)
        self.root.bind('<Control-q>', self.quit)
        signal.signal(signal.SIGINT, self.quit)

    def quit(self, *args):
        logging.log(logging.INFO, "Quit application.")
        self.root.destroy()


def main():
    logging.basicConfig(level=logging.DEBUG)
    root = tk.Tk()
    app = App(root)
    app.root.mainloop()


if __name__ == "__main__":
    main()
