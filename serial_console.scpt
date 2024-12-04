#############
#
# NOTE: Before attempting a USB serial connection, ensure that an appropriate driver is installed
#
# Silicon Labs CP210x USB to UART Bridge VCP Driver -- For use with USB-A to USB-micro cable
#    Supports devices with USB serial ports
#    Download from: https://www.silabs.com/developers/usb-to-uart-bridge-vcp-drivers
#
# Tripp-Lite (formerly Keyspan) -- For use with model USA-19HS
#    Supports devices with DB9 serial ports
#    Download from: https://www.tripplite.com/support/USA19HS#section-downloads
#
# Version 1.0.5, 11/29/2020, John McNally, jmcnally@acm.org
#
#############

# Create a list of available serial devices
try
	do shell script "ls /dev/tty.* | grep -E 'SLAB.+[[:digit:]]|USA19H|usb'"
on error
	display alert "No serial devices are available."
	error number -128
end try

# Prompt for TTY serial device
get paragraphs of result
set device to choose from list (result) with prompt "Choose the serial device:"
if result is false then
	error number -128
end if

# Prompt for connection speed
set speed to choose from list {"115200", "38800", "9600"} with prompt "Choose the connection speed (bps):"
if result is false then
	error number -128
end if

# Prompt for logging
set loggingResponse to choose from list {"Yes", "No"} with prompt "Turn on console logging?"
if result is false then
	error number -128
end if
if loggingResponse as string is equal to "Yes" then
	set loggingOption to "-L"
else
	set loggingOption to ""
end if

# Assemble the "screen" command line
set screenCommand to "screen " & loggingOption & " -h 10000 " & device & " " & speed & ",cs8"

# Open the Terminal window and issue the "screen" command
tell application "Terminal"
	activate
	if not (exists window 1) then
		reopen
		set myIndex to 1
	else
		set allWindows to every window
		set myIndex to number of items in allWindows
	end if
	tell window myIndex
		set number of rows to 80
		set number of columns to 160
		#set background color to "black"
		#set normal text color to "green"
		set custom title to "Serial Console"
	end tell
	do script with command screenCommand in window myIndex
end tell
