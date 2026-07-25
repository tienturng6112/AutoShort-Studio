import codecs

with codecs.open('desktop_app.py', 'r', 'utf-8') as f:
    text = f.read()

entry_point = """
if __name__ == '__main__':
    import traceback
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print("Startup Failed:\\n")
        traceback.print_exc()
        input("\\nPress Enter to exit...")
        sys.exit(1)
"""

if "if __name__ == '__main__':" not in text:
    text += '\n' + entry_point
    with codecs.open('desktop_app.py', 'w', 'utf-8') as f:
        f.write(text)
    print("Added entry point.")
else:
    print("Entry point already exists.")
