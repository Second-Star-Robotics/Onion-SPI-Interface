import sys
import time
import argparse
import spidev

def printHex(numbers):
    # Print 10 hexadecimal numbers per row, comma-separated
    for i in range(0, len(numbers), 10):
        print(', '.join(hex(num) for num in numbers[i:i+10]))

# Do a half-duplex transmission where input_array bytes are written and bytes_to_read bytes are read
def spiSend(input_array, bytes_to_read):
    #print(f"Half-duplex transmission: writing {len(input_array)} bytes, reading {bytes_to_read} bytes")
    spi.writebytes(input_array)
    #time.sleep(1)
    spi.readbytes(1)
    return spi.readbytes(1) 
    #return spi.xfer3(input_array, bytes_to_read)

def test_spi_send(n):
    errors = 0
    for i in range(1, n+1):
        sent_byte = [i%129]
        read_bytes = spiSend(sent_byte, 1)
        if sent_byte[0] != read_bytes[0]:
            print(f"Error: {hex(sent_byte[0])} != {hex(read_bytes[0])}")
            errors += 1
        #else:
            #print(f"{hex(sent_byte[0])} == {hex(read_bytes[0])}")
        #time.sleep(1)
        
        #if i % 1000 == 0:
            #print(f"Sent {i} bytes so far")
    return errors        

def format_frequency(hz):
    if hz >= 1e6:  # MHz
        return f"{hz / 1e6:.3f} MHz"
    elif hz >= 1e3:  # KHz
        return f"{hz / 1e3:.3f} KHz"
    else:  # Hz
        return f"{hz:.3f} Hz"

def format_BPS(bytes, sec):
    bps = bytes / sec;
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

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Send and read bytes via SPI.')
parser.add_argument('iterations', metavar='N', type=int, help='the number of iterations')
parser.add_argument('-f', '--frequency', metavar='F', type=int, default=100000, help='the frequency in Hz')

args = parser.parse_args()

 
spi = spidev.SpiDev(0,1)
spi.max_speed_hz = args.frequency
spi.mode = 0b00
print(f"Mode: {spi.mode}, Speed: {format_frequency(spi.max_speed_hz)}, Iterations: {format(args.iterations, ',')}")

start_time = time.time()
err = test_spi_send(args.iterations)
elapsed_time = time.time() - start_time

if err == 0:
    print(f"All {format(args.iterations, ',')} bytes sent and received successfully in {format_time(elapsed_time)} - Transfer speed: {format_BPS(args.iterations, elapsed_time )}")   
else:
    print(f"Errors: {err}") 

#readVals = spiSend([0x60], 1)
#printHex(readVals)


