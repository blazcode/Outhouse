import time
import subprocess
from gpiozero import Button
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import requests

# Setup shutdown button
shutdownButton = Button(26)

# Create the I2C interface
i2c = busio.I2C(SCL, SDA)

# Create the SSD1306 OLED class
disp = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Clear display
disp.fill(0)
disp.show()

# Create blank image for drawing
width = disp.width
height = disp.height
image = Image.new("1", (width, height))

# Get drawing object to draw on image
draw = ImageDraw.Draw(image)

# Load default font
font = ImageFont.load_default()

def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org")
        if response.status_code == 200:
            return response.text
        else:
            return None
    except requests.ConnectionError:
        return None

# Initialize last_check_time to 0 to ensure the first check runs immediately
last_check_time = 0

while True:
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    if shutdownButton.is_pressed:
        time.sleep(5)
        if shutdownButton.is_pressed:
            draw.text((0, 16), "Shutting down!", font=font, fill=255)
            disp.image(image)
            disp.show()
            time.sleep(3) 
            disp.fill(0)
            disp.show()
            subprocess.call(['sudo shutdown -h now'], shell=True)
    else:
        current_time = time.time()
        
        # Check if 5 minutes have elapsed since the last public IP check
        if current_time - last_check_time >= 300:
            public_ip = get_public_ip()
            last_check_time = current_time
        
        defaultInt = subprocess.check_output("ip route show default | awk '/default/ {print $5}'", shell=True).decode("utf-8").strip()
        IP = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True).decode("utf-8").strip()
        networkInfo = f"{defaultInt} {IP}"
        
        if public_ip:
            internetAccess = f"IP: {public_ip}"
        else:
            internetAccess = "No Internet!"
        
        CPU = subprocess.check_output('cut -f 1-3 -d " " /proc/loadavg', shell=True).decode("utf-8")
        MemUsage = subprocess.check_output("free -m | awk 'NR==2{printf \"Mem: %s/%sMB %.0f%%\", $3,$2,$3*100/$2 }'", shell=True).decode("utf-8")
        Disk = subprocess.check_output('df -h | awk \'$NF=="/"{printf "OS: %dG/%dG", $3,$2}\'', shell=True).decode("utf-8")
        
        output = subprocess.check_output("sudo df -h /media/devmon/sda1-ata-ST1000LM035-1RK1", shell=True).decode("utf-8").strip()
        lines = output.split('\n')
        disk_info = lines[1] if len(lines) > 1 else ""
        if disk_info:
            fields = disk_info.split()
            used_space = fields[2]
            total_space = fields[1]
            usbDisk = f"USB: {used_space}/{total_space}"
        else:
            usbDisk = "USB: N/A"

        plexStatus = subprocess.check_output('sudo docker ps --format "{{.Status}}" -f name=plex', shell=True).decode("utf-8")

        draw.text((0, -2), networkInfo, font=font, fill=255)
        draw.text((0, 6), internetAccess, font=font, fill=255)
        draw.text((0, 16), "CPU: " + CPU, font=font, fill=255)
        draw.text((0, 24), MemUsage, font=font, fill=255)
        draw.text((0, 32), Disk, font=font, fill=255)
        draw.text((0, 40), usbDisk, font=font, fill=255)  # Encode to UTF-8
        draw.text((0, 48), "Plex: " + plexStatus, font=font, fill=255)
        
        disp.image(image)
        disp.show()

        # Don't kill the little CPU
        time.sleep(10)
