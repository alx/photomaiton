#
# Show printer infos
#
import cups

def main():
     # Set up CUPS
    conn = cups.Connection()
    printers = conn.getPrinters()
    printer_name = list(printers.keys())[0]
    cups.setUser("pi")
    printer_attributes = conn.getPrinterAttributes(selected_printer)

    attr = conn.getPrinterAttributes(printer)
    for key, value in attr.items():
        print(f"{key}: {value}")

    return 1


if __name__ == "__main__":
    main()

