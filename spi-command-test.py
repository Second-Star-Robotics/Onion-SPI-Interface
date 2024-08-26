import sys
import time
import argparse
import spidev

def printHex(numbers):
    # Print 10 hexadecimal numbers per row, comma-separated
    for i in range(0, len(numbers), 10):
        print(', '.join(hex(num) for num in numbers[i:i+10]))

def print_sector(sector):
    print("Offset: 00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F")
    print("-------------------------------------------------------")

    for i in range(0, len(sector), 16):
        offset = f"{i:06X}"
        row = " ".join(f"{byte:02X}" for byte in sector[i:i+8])
        row += "  " + " ".join(f"{byte:02X}" for byte in sector[i+8:i+16])
        print(f"{offset}: {row}")

# Do a half-duplex transmission where input_array bytes are written and bytes_to_read bytes are read
def spiSend(spi, input_array, bytes_to_read):
    spi.writebytes(input_array)
    spi.readbytes(1)
    return spi.readbytes(1)

def test_spi_send(spi, n):
    errors = 0
    for i in range(1, n+1):
        sent_byte = [i % 129]
        read_bytes = spiSend(spi, sent_byte, 1)
        if sent_byte[0] != read_bytes[0]:
            print(f"Error: {hex(sent_byte[0])} != {hex(read_bytes[0])}")
            errors += 1
    return errors        

def format_frequency(hz):
    if hz >= 1e6:  # MHz
        return f"{hz / 1e6:.3f} MHz"
    elif hz >= 1e3:  # KHz
        return f"{hz / 1e3:.3f} KHz"
    else:  # Hz
        return f"{hz:.3f} Hz"

def format_BPS(bytes, sec):
    bps = bytes / sec
    if bps >= 1e6:  # MB/s
        return f"{bps / 1e6:.3f} MB/s"
    elif bps >= 1e3:  # KB/s
        return f"{bps / 1e3:.3f} KB/s"
    else:  # B/s
        return f"{bps:.3f} B/s"
    
def format_time(seconds):
    if seconds >= 60:  # minutes
        return f"{seconds / 60:.3f} mins"
    elif seconds >= 1:  # seconds
        return f"{seconds:.3f} secs"
    elif seconds >= 1e-3:  # milliseconds
        return f"{seconds * 1e3:.3f} ms"
    else:  # microseconds
        return f"{seconds * 1e6:.3f} µs"

#Calculate CRC32 using an ISO 3309 compliant algorithm
def crc32(data):
    crc = 0xFFFFFFFF
    poly = 0x04C11DB7
    for byte in data:
        crc ^= byte << 24
        for _ in range(8):
            if crc & 0x80000000:
                crc = (crc << 1) ^ poly
            else:
                crc <<= 1
            crc &= 0xFFFFFFFF  # Ensure CRC remains a 32-bit value
    return crc ^ 0xFFFFFFFF

#Send a quit command to SPI interface
#Command format:
#<Byte 0: 0x00> <Byte 1 - Byte 5: 0x00> <CRC-32>
def quit(spi):
    #Command byte
    command = 0x00
    #Sector number byte array
    sector_bytes = 0x00.to_bytes(4, byteorder='little')

    #Assemble message byte array
    message = [command] + list(sector_bytes)

    #Calculate CRC-32
    crc = crc32(message)
    crc_bytes = crc.to_bytes(4, byteorder='little')

    #Assemble command frame
    command_frame = message + list(crc_bytes)

    #Display hex values for command frame command_frame = <Byte 0: Command> <Byte 1 - Byte 5: Sector Number> <CRC-32>
    print("Command frame: ")
    printHex(command_frame)    

    #Send command frame
    spi.writebytes(command_frame)

#Send a write sector command to SPI interface
#Command format:
#<Byte 0: Command 0x02> <Byte 1 - Byte 5: Sector Number> <CRC-32>
def write_sector(spi, sector_number):
    #Command byte
    command = 0x02
    #Sector number byte array
    sector_bytes = sector_number.to_bytes(4, byteorder='little')

    #Assemble message byte array
    message = [command] + list(sector_bytes)

    #Calculate CRC-32
    crc = crc32(message)
    crc_bytes = crc.to_bytes(4, byteorder='little')

    #Assemble command frame
    command_frame = message + list(crc_bytes)

    #Display hex values for command frame command_frame = <Byte 0: Command> <Byte 1 - Byte 5: Sector Number> <CRC-32>
    print("Command frame: ")
    printHex(command_frame)    

    #Send command frame
    spi.writebytes(command_frame)

#Send a read sector command to SPI interface
#Command format:
#<Byte 0: Command 0x01> <Byte 1 - Byte 5: Sector Number> <CRC-32>
def read_sector(spi, sector_number):
    #Command byte
    command = 0x01
    #Sector number byte array
    sector_bytes = sector_number.to_bytes(4, byteorder='little')

    #Assemble message byte array
    command_message = [command] + list(sector_bytes)

    #Calculate CRC-32
    crc = crc32(command_message)
    crc_bytes = crc.to_bytes(4, byteorder='little')

    #Assemble command frame
    command_frame = command_message + list(crc_bytes)

    #Send command frame
    spi.writebytes(command_frame)
    #Wait for Data Ready Flag
    time.sleep(0.1) #Wait for 1 second for testing
    data_ready = False
    while not data_ready:
        data_ready = True #Set true for testing

    #SPI read 517 bytes in 8 byte increments and append to data_frame
    #read 1 byte and throw it away
    spi.readbytes(1)

    data_frame = bytearray()
    for i in range(0, 64):
        data_frame += bytearray(spi.readbytes(8))
    
    data_frame+= bytearray(spi.readbytes(4))

    #Extract sector data from data frame (first 512 bytes)
    sector_data = data_frame[:512]

    #Print sector data
    #print_sector(sector_data)

    #Calculate local CRC for sector data
    local_crc = crc32(sector_data)
    #Print local CRC as decimal
    # print(f"Local CRC: {local_crc}")

    #Print Local CRC as hex
    # print("Local CRC: ")
    # printHex(local_crc.to_bytes(4, byteorder='big'))
    
    #Calculate remote CRC from data frame
    remote_crc_bytes = data_frame[-4:]

    #extract last for bytes for remote CRC
    remote_crc_bytes = data_frame[-4:]
    #Print Remote CRC bytes as hex
    # print("Remote CRC: ")
    # printHex(remote_crc_bytes)

    #Convert remote CRC bytes to integer
    remote_crc = int.from_bytes(remote_crc_bytes, byteorder='big')

    #Test if local CRC matches remote CRC
    if local_crc == remote_crc:
        CRC_good = True
    else:
        CRC_good = False

    #Return sector data and CRC match status

    return sector_data, CRC_good

def sector_to_samples(sector_data, number_of_values=16):
    """
    Convert a 512-byte sector into a list of 32-byte samples.

    Each sample is a 32-byte array of uint8 values.

    Inputs:
    - sector_data (bytearray): A 512-byte array representing the sector data read from the SD card.
    - number_of_values (int): The number of 2-byte values in each sample. Default is 16.

    Outputs:
    - samples (list of bytearrays): A list of samples, where each sample is a 32-byte bytearray.
    """

    if len(sector_data) != 512:
        raise ValueError("Sector data must be exactly 512 bytes.")
    
    samples = []
    sample_size = number_of_values * 2  # Each sample is 32 bytes
    
    for i in range(0, 512, sample_size):
        sample = sector_data[i:i + sample_size]
        samples.append(bytearray(sample))
    
    return samples

def convert_sample_to_dict(sample, number_of_values=16):
    """
    Convert a 32-byte sample array into a dictionary of sensor data.

    Inputs:
    - sample (bytearray): A 32-byte array representing the raw sample data.
    - number_of_values (int): Number of 16-bit sensor values in each sample. Default is 16.

    Outputs:
    - sample_dict (dict): A dictionary with keys as labels and values as the sensor data.
    """
    sample_dict = {}

    # Extract 32-bit timestamp (Ticks)
    sample_dict['Ticks'] = int.from_bytes(sample[0:4], byteorder='little')

    # Extract the remaining 16-bit values
    sensor_data_labels = [
        "Reserved_1", "Reserved_2", "SS_FLAG", "Release_On", "Lamps_On", 
        "Reserved_3", "Reserved_4", "Reserved_5", "Temperature", 
        "Reserved_6", "Pressure_Value", "Pressure_Status", 
        "Battery_Value", "Camera_Record_Time"
    ]

    # The labels array above has 14 entries corresponding to the indices 2 to 15 in the C code

    for i, label in enumerate(sensor_data_labels):
        sensor_value = int.from_bytes(sample[4 + 2*i: 6 + 2*i], byteorder='little')
        sample_dict[label] = sensor_value

    return sample_dict


def main():
    # Hardcoded arguments
    iterations = 10
    frequency = 100000

    spi = spidev.SpiDev(0, 1)
    spi.max_speed_hz = frequency
    spi.mode = 0b00
    print(f"Mode: {spi.mode}, Speed: {format_frequency(spi.max_speed_hz)}, Iterations: {format(iterations, ',')}")

    sector_no = 0

    print("Infinite send loop")
    while True:
        #Send a test command
        #quit(spi)
        #write_sector(spi, sector_no)
        #Read sector data
        sector_data, CRC_good = read_sector(spi, sector_no)

        #Print sector data
        print_sector(sector_data)

        #Print CRC match status
        if CRC_good:
            print("CRC Match")
        else:
            print("CRC Mismatch")

        #Convert sector data into sample byte arrays
        samples = sector_to_samples(sector_data, 16)

        #Print sample arrays listing sector number and sample array number
        for idx, sample in enumerate(samples):
            print(f"Sample {idx + 1}: {sample.hex()}")

        #Convert sample arrays into dictionaries
        sample_dicts = [convert_sample_to_dict(sample, 16) for sample in samples]

        #Print sample dictionaries
        for idx, sample_dict in enumerate(sample_dicts):
            print(f"Sample {idx + 1}: {sample_dict}")
                
        #If sector data was good increment sector number
        if CRC_good:
            sector_no += 1
        else:
            print("CRC Mismatch - Retrying")

        #Wait for Enter to continue
        input("Press Enter to continue...")
        
    
    
    #start_time = time.time()
    #err = test_spi_send(spi, iterations)
    #elapsed_time = time.time() - start_time

    if err == 0:
        print(f"All {format(iterations, ',')} bytes sent and received successfully in {format_time(elapsed_time)} - Transfer speed: {format_BPS(iterations, elapsed_time )}")   
    else:
        print(f"Errors: {err}")

if __name__ == "__main__":
    main()
