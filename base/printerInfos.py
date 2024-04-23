#
# Show printer infos
#
import cups
import time

def main():
     # Set up CUPS
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = list(printers.keys())[0]
    cups.setUser("pi")
    attr = conn.getPrinterAttributes(printer_name)
    for key, value in attr.items():
        if key=="marker-message":
            print(f"{key}: {value}")

    return 1


if __name__ == "__main__":
    while True:
        main()
        time.sleep(300)

