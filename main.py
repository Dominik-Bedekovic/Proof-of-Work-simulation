import gui

def main():
    gui.root.update_idletasks()

    width = gui.root.winfo_reqwidth()
    height = gui.root.winfo_reqheight()

    x = (
        gui.root.winfo_screenwidth() - width
    ) // 2

    y = (
        gui.root.winfo_screenheight() - height
    ) // 2

    gui.root.geometry(
        f"{width}x{height}+{x}+{y}"
    )

    gui.root.mainloop()


if __name__ == "__main__":
    main()