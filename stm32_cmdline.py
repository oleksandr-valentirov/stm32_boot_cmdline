import argparse

import serial
from serial.tools.list_ports import comports

ACK = 0x79.to_bytes()
NACK = 0x1F.to_bytes()


def get_commands(interface: serial.Serial):
    request = 0xFF
    interface.write(request.to_bytes())

    data = interface.read(1)
    if data == NACK:
        return []

    length = interface.read(1)
    data = interface.read(int(length))
    ack = interface.read(1)

    return list(data)


def get_version(interface: serial.Serial):
    request = 0x01 + 0xFE
    interface.write(request.to_bytes())

    data = interface.read(1)
    if data == NACK:
        return "unknown"

    proto = int(interface.read(1))
    opt1 = int(interface.read(1))
    opt2 = int(interface.read(1))

    ack = interface.read(1)

    return f"{proto}.{opt1}.{opt2}"


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("-l", dest="list",
                      help="List of available COM-ports",
                      action=argparse.BooleanOptionalAction,
                      default=False
                      )
    args.add_argument("-p", dest="port",
                      help="Target COM-port",
                      default="")
    args.add_argument("-f", dest="firmware",
                      help="Path to the firmware")

    args = args.parse_args()

    if args.list:
        print("Available COM-ports:")
        ports = comports()
        for port, desc, hwid in sorted(ports):
            print("{}: {} [{}]".format(port, desc, hwid))
        exit(0)
    else:
        if not args.port:
            print("COM port is not specified")
            exit(1)
        if not args.firmware:
            print("Path to the firmware is not specified")
            exit(1)

        ser = serial.Serial(port=args.port, baudrate=115200, parity=serial.PARITY_EVEN, stopbits=1)
        try:
            ser.open()
        except serial.SerialException:
            print("COM port can't be open")
            exit(1)

        ser.write(0x7F.to_bytes())
        data = ser.read()
        if data == NACK:
            print("Bootloader initial sequence returned NACK")
            exit(1)

        print(f"Version: {get_version(ser)}")

        commands = get_commands(ser)
        if not commands:
            print("No commands available")
            exit(1)
        for cmd in commands:
            print(f"0x{hex(cmd)}")

        while True:
            cmd = input(">>> ")

            if cmd.lower() == "q":
                break
