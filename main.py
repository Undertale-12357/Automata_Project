import tkinter as tk
from gui import FAApp
from database import FADatabase
import logging

# Set up logging
logging.basicConfig(filename='fa_tool.log', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    logging.info("Starting application")
    db = FADatabase()
    logging.info("Initializing database")
    db.init_db()
    root = tk.Tk()
    app = FAApp(root)
    logging.info("Running main application loop")
    root.mainloop()
