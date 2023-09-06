import requests
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait 
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver
from selenium.webdriver.common.by import By
import json
import brotli
import os
import shutil
import cv2
import time
from concurrent.futures import ThreadPoolExecutor
import base64
from PIL import Image
from collections import Counter
import math
import re
import numpy as np
from multiprocessing import Pool, get_context, Manager
import multiprocessing
from tqdm import tqdm
import logging
from dotenv import load_dotenv

def calculate_character_frequency(input_string):
    character_frequency = {}

    for char in input_string:
        if char.isalpha():
            character_frequency[char] = character_frequency.get(char, 0) + 1
        elif char.isdigit():
            numeric_mapping = {
                '0': 'ze', '1': 'on', '2': 'tw', '3': 'th', '4': 'fo',
                '5': 'fi', '6': 'si', '7': 'se', '8': 'ei', '9': 'ni'
            }
            mapped_char = numeric_mapping[char]
            character_frequency[mapped_char] = character_frequency.get(mapped_char, 0) + 1

    result = ""
    for char, frequency in character_frequency.items():
        result += f"{char}{frequency}"

    return result

def character_position_mapping(input_string):
    character_mapping = {}

    for index, char in enumerate(input_string):
        if char.isalpha() or char.isdigit():
            if char in character_mapping:
                character_mapping[char].append(index + 1)
            else:
                character_mapping[char] = [index + 1]

    numeric_mapping = {
                '0': 'ze', '1': 'on', '2': 'tw', '3': 'th', '4': 'fo',
                '5': 'fi', '6': 'si', '7': 'se', '8': 'ei', '9': 'ni'
            }

    new_dict = {}

    for key, value in character_mapping.items():
        if key in numeric_mapping:
            new_key = numeric_mapping[key]
            new_dict[new_key] = value
        else:
            new_dict[key] = value


    return new_dict


def process_input_string(input_string, new_dict):
    result_dict = {}
    i = 0
    
    while i < len(input_string):
        key = ""
        num_str = ""
        

        if str(input_string[i]+input_string[i+1]).isalpha():
            key = input_string[i:i+2]
            i += 2
        else:
            key = input_string[i:i+1]
            i += 1
        
        while i < len(input_string) and input_string[i].isdigit():
            num_str += input_string[i]
            i += 1
        
        if num_str:
            num = int(num_str)
            
            result_dict[key] = num

    numbers = []
    keys = new_dict.keys()
    for key in keys:
        for y in range(int(result_dict[key])):
            numbers.append((new_dict[key][y]))
    
    return numbers

def recreate_the_mapping(input_string, numbers_list):
    result_dict = {}
    i = 0
    
    while i < len(input_string):
        key = ""
        num_str = ""
        

        if str(input_string[i]+input_string[i+1]).isalpha():
            key = input_string[i:i+2]
            i += 2
        else:
            key = input_string[i:i+1]
            i += 1
        
        while i < len(input_string) and input_string[i].isdigit():
            num_str += input_string[i]
            i += 1
        
        if num_str:
            num = int(num_str)
            
            result_dict[key] = num

    numeric_mapping = {
                'ze': '0', 'on': '1', 'tw': '2', 'th': '3', 'fo': '4',
                'fi': '5', 'si': '6', 'se': '7', 'ei': '8', 'ni': '9'
            }


    new_dict = {}
    for key, value in result_dict.items():
        if key in numeric_mapping:
            new_key = numeric_mapping[key]
            new_dict[new_key] = value
        else:
            new_dict[key] = value

    
    count = 0
    for key, value in new_dict.items():
        new_dict[key] = numbers_list[count:count+value]
        count += value

    return new_dict

def rebuild_string_from_mapping(character_mapping):
    max_position = max(max(positions) for positions in character_mapping.values())
    rebuilt_string = [' '] * max_position

    for char, positions in character_mapping.items():
        for position in positions:
            rebuilt_string[position - 1] = char

    return ''.join(rebuilt_string)

def extract_frames(video_path, output_folder, frame_rate):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % int(cap.get(cv2.CAP_PROP_FPS) / frame_rate + 0.5) == 0:
            frame_filename = f"{output_folder}/frame_{frame_count}.jpg"
            cv2.imwrite(frame_filename, frame)
            logging.info(f"Saved {frame_filename}")

        frame_count += 1

    cap.release()

def create_im(number_list, location):
	binary_string = "".join(format(num, "012b") for num in number_list)
	pixels = [(0,0,0) if n=="0" else (255,255,255) for n in binary_string for x in range(23)]
	width = 1280
	height = 720

	image = Image.new("RGB", (width, height))

	for x in range(width):
	    for y in range(height):
	    	try:
	    		pixel_color = pixels[x* height + y]
	    		image.putpixel((x, y), pixel_color)
	    	except:
	    		image.putpixel((x, y), (0,0,0))


	image.save(r"temp\\"+str(location)+".png")


def closer_to_white_or_black(rgb_value):
    white = (255, 255, 255)
    black = (0, 0, 0)
    
    distance_to_white = euclidean_distance(rgb_value, white)
    distance_to_black = euclidean_distance(rgb_value, black)
    
    if distance_to_white < distance_to_black:
        return True
    elif distance_to_black < distance_to_white:
        return False

def euclidean_distance(color1, color2):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    return math.sqrt((r2 - r1)**2 + (g2 - g1)**2 + (b2 - b1)**2)

def decode(image_path):
    image = Image.open(image_path)

    image_width, image_height = image.size

    extracted_number_list = []

    binary_string = ""
    temp = ""
    for x in range(image_width):
        for y in range(image_height):
            pixel_value = image.getpixel((x, y))
            if len(temp) == 23:
                counter = Counter(temp)
                most_frequent = counter.most_common(1)[0]
                binary_string += most_frequent[0]
                temp = ""
                if pixel_value == (255, 255, 255) or closer_to_white_or_black(pixel_value):
                    temp += "1"
                else:
                    temp += "0"
            else:
                if pixel_value == (255, 255, 255) or closer_to_white_or_black(pixel_value):
                    temp += "1"
                else:
                    temp += "0"
                    
            if len(binary_string) == 12:
                extracted_number = int(binary_string, 2)
                extracted_number_list.append(extracted_number)
                binary_string = ""

    try:
        extracted_number_list = list(filter(lambda x: x != 0, extracted_number_list))
    except:
        pass


    return extracted_number_list

def make_video(videon):
	image_folder = 'temp'
	video_name = videon

	files = sorted([int(file.replace(".png", "")) for file in os.listdir(image_folder) if os.path.isfile(os.path.join(image_folder, file))])
	files = [str(file_num)+".png" for file_num in files]

	if len(files)< 8:
		images = [file for file in files for y in range(2)] 
		frame = cv2.imread(os.path.join(image_folder, images[0]))
		height, width, layers = frame.shape

		video = cv2.VideoWriter(video_name, 0, len(files)*2, (width,height))
	elif len(files)>=8 and len(files)<30:
		images = [file for file in files] 
		frame = cv2.imread(os.path.join(image_folder, images[0]))
		height, width, layers = frame.shape

		fourcc = cv2.VideoWriter_fourcc(*'HFYU')
		video = cv2.VideoWriter(video_name, fourcc, len(files), (width, height))
	elif len(files)>=30:
		images = [file for file in files] 
		frame = cv2.imread(os.path.join(image_folder, images[0]))
		height, width, layers = frame.shape

		fourcc = cv2.VideoWriter_fourcc(*'HFYU')
		#video = cv2.VideoWriter(video_name, fourcc, 30, (width, height))
		video = cv2.VideoWriter(video_name,cv2.VideoWriter_fourcc(*"mp4v"), 30, (width,height))

		#os.system("ffmpeg -i "+video_name+" -vcodec libx264 "+video_name)
	for image in images:
		video.write(cv2.imread(os.path.join(image_folder, image)))

	video.release()


def retrieve(session, location):
    while True:
        try:
            s = session.get("https://libraryofbabel.info/book.cgi?"+location, timeout=300)
            s.close()
            page = page_extractor(s.text)
            if page == None:
                time.sleep(1.5)
                continue
            else:
                break
        except:
            time.sleep(1.5)
            continue
    
    return page

def page_extractor(page_content):
    pattern = r'<PRE id = "textblock">(.*?)</PRE>'
    match = re.search(pattern, page_content, re.DOTALL)

    if match:
        page_extracted = match.group(1)
        return page_extracted
    else:
        return None

def search(session, text):
    while True:
        try:
            payload = {"btnSubmit": "Search", "method":"x", "find": text}
            response = session.post("https://libraryofbabel.info/search.cgi", data=payload)
            result = re.findall("onclick = \"(.*?)\"",response.text)[0].replace("postform(", "").replace(")","").replace("'","").split(",")
            break
        except:
            time.sleep(0.1)
            continue


    return result


def upload_video(video_path, Email, Password):
	while True:
		try:
			driver = Driver(uc=True)
			driver.get("https://studio.youtube.com/")
			email= driver.find_element(By.XPATH,"""/html/body/div[1]/div[1]/div[2]/div/c-wiz/div/div[2]/div/div[1]/div/form/span/section/div/div/div[1]/div/div[1]/div/div[1]/input""")
			email.send_keys(Email)
			driver.implicitly_wait(10)
			driver.find_element(By.XPATH, """/html/body/div[1]/div[1]/div[2]/div/c-wiz/div/div[2]/div/div[2]/div/div[1]/div/div/button""").click()
			driver.implicitly_wait(20)
			password = driver.find_element(By.XPATH,"""/html/body/div[1]/div[1]/div[2]/div/c-wiz/div/div[2]/div/div[1]/div/form/span/section[2]/div/div/div[1]/div[1]/div/div/div/div/div[1]/div/div[1]/input""")
			password.send_keys(Password)
			WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH, """/html/body/div[1]/div[1]/div[2]/div/c-wiz/div/div[2]/div/div[2]/div/div[1]/div/div/button/span"""))).click()
			break		
		except Exception as e:
			print(e)
			try:
				driver.quit()
			except:
				pass
			continue

	driver.implicitly_wait(30)
	driver.find_element(By.XPATH,"""/html/body/ytcp-app/ytcp-entity-page/div/ytcp-header/header/div/ytcp-button""").click()
	driver.implicitly_wait(10)
	driver.find_element(By.XPATH,"""/html/body/ytcp-app/ytcp-entity-page/div/ytcp-header/header/div/ytcp-text-menu/tp-yt-paper-dialog/tp-yt-paper-listbox/tp-yt-paper-item[1]/ytcp-ve""").click()
	driver.implicitly_wait(10)
	driver.find_element(By.XPATH,"""/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-uploads-file-picker/div/input""").send_keys(video_path)
	driver.implicitly_wait(10)

	while driver.find_element(By.XPATH, """//*[@id="checks-badge"]""").value_of_css_property('color') != "rgba(96, 96, 96, 1)":
		continue

	driver.find_element(By.XPATH,"""/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[2]""").click()
	driver.implicitly_wait(10)
	driver.find_element(By.XPATH,"""/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-ve/ytcp-video-metadata-editor/div/ytcp-video-metadata-editor-basics/div[5]/ytkc-made-for-kids-select/div[4]/tp-yt-paper-radio-group/tp-yt-paper-radio-button[2]""").click()
	driver.implicitly_wait(10)

	for x in range(3):
		driver.find_element(By.XPATH,"""/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[2]""").click()
		driver.implicitly_wait(10)
	
	driver.find_element(By.XPATH, """/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[1]/ytcp-uploads-review/div[2]/div[1]/ytcp-video-visibility-select/div[2]/tp-yt-paper-radio-group/tp-yt-paper-radio-button[3]""").click()
	driver.implicitly_wait(10)
	driver.find_element(By.XPATH, """/html/body/ytcp-uploads-dialog/tp-yt-paper-dialog/div/ytcp-animatable[2]/div/div[2]/ytcp-button[3]""").click()
	link = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, """/html/body/ytcp-video-share-dialog/ytcp-dialog/tp-yt-paper-dialog/div[2]/div/div/div/a""")))
	rlink = link.text
	rlinksp = rlink.replace("https://youtu.be/","")
	time.sleep(2)
	driver.quit()

	return rlinksp

def returner(args):
	key, frame, count, sesssion = args
	frame_decoded = decode("temp\\"+frame)
	temp = []

	for char in reversed(key):
		if char != "w":
			temp.append(char)
		else:
			temp.append("w")
			wsvp = "".join(reversed(temp))
			keyswtheextra = key.replace(wsvp, "", 1)
			break

	mapping = recreate_the_mapping(keyswtheextra, frame_decoded)
	location = rebuild_string_from_mapping(mapping)

	wsvp = wsvp.replace("w","-w").replace("s","-s").replace("v","-v").replace("p",":")

	reconstructed_piece_of_text = retrieve(sesssion, location+wsvp).replace("\n","")
	reconstructed_piece_of_text = " ".join(reconstructed_piece_of_text.split())
	return count, reconstructed_piece_of_text

def store(filename, chars_replacement, email, password):
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

	try:
		with open("files.br", "rb") as f:
			decompressed = brotli.decompress(f.read())

		file_history = decompressed.decode("utf-8").splitlines()
		file_count = len(file_history)
	except:
		file_count = 0

	fileinfo = {"n": filename, "vn": file_count}

	if ".txt" in filename:
		with open(filename, "r", encoding='utf-8') as f:
			text = f.read()

		for key, value in chars_replacement.items():
			text = text.replace(key, value)
	else:
		with open(filename,"rb") as f:
			c_bytes = f.read()

		c_bytes1 = brotli.compress(c_bytes)
		b64c = base64.b64encode(c_bytes1)
		text = b64c.decode()

		for key, value in chars_replacement.items():
			text = text.replace(key, " "+value+" ")

	parts = [text[i:i+3200] for i in range(0, len(text), 3200)]

	sesssion = requests.Session()

	logging.info("Starting the retrieval of locations and the building of the number lists.")
	keys = [None]*len(parts)
	numbers_lists = [None]*len(parts)

	def loc(part, i):
		location = search(sesssion, part)
		frequency_key = calculate_character_frequency(location[0])
		keys[i] = frequency_key+"w"+location[1]+"s"+location[2]+"v"+location[3]+"p"+location[4]
		mapping = character_position_mapping(location[0])

		numbers_list = process_input_string(frequency_key, mapping)
		numbers_lists[i] = numbers_list

	with ThreadPoolExecutor(max_workers=44) as executor:
		executor.map(loc,parts, [i for i in range(len(parts))])

	parts.clear()
	key_of_all_keys = "aa".join(keys).strip("aa")
	freq_numbers_list = []
	keys = []
	

	while len(key_of_all_keys) > 4095:
		temp_split = [key_of_all_keys[i:i+3339] for i in range(0, len(key_of_all_keys), 3339)]
		for count, sp in enumerate(temp_split):
			frequency_key = calculate_character_frequency(sp)
			keys.append(frequency_key)
			mapping = character_position_mapping(sp)

			numbers_list = process_input_string(frequency_key, mapping)
			freq_numbers_list.insert(count, numbers_list)

		key_of_all_keys = "aa".join(keys).strip("aa")
		keys.clear()

	freqkfkoak = calculate_character_frequency(key_of_all_keys)
	fileinfo["k"] = freqkfkoak
	mapping = character_position_mapping(key_of_all_keys)
	numbers_list = process_input_string(freqkfkoak, mapping)


	freq_numbers_list1 = [numbers_list[i:i+3339] for i in range(0, len(numbers_list), 3339)]
	for count, elem in enumerate(freq_numbers_list1):
		freq_numbers_list.insert(count, elem)
	fileinfo["kf"] = len(freq_numbers_list1)
	fileinfo["kfc"] = len(freq_numbers_list) 
	freq_numbers_list.extend(numbers_lists)

	fileinfo["fr"] = len(freq_numbers_list) if len(freq_numbers_list) < 30 else 30
	numbers_lists.clear()
	keys.clear()
	logging.info("The retrieval of locations and the building of the number lists is done.")
	logging.info("Building the frames.")

	pool = get_context("spawn").Pool()
	n = 0
	for element in freq_numbers_list:
		pool.apply_async(create_im, args=(element,n,))
		n += 1
	pool.close()
	pool.join()
	logging.info("frames done.")
	logging.info("making and uploading the video.")

	if fileinfo["fr"] < 30:
		make_video(r"temp\\file "+str(file_count)+".avi")
		idofv = upload_video(os.getcwd()+"\\temp\\file "+str(file_count)+".avi", email, password)
	else:
		make_video(r"temp\\file "+str(file_count)+".mp4")
		idofv = upload_video(os.getcwd()+"\\temp\\file "+str(file_count)+".mp4", email, password)

	fileinfo["id"] = idofv
	logging.info("video uploaded.")

	if file_count == 0:
		with open("files.br","wb") as f:
			f.write(brotli.compress((str(fileinfo)+"\n").encode('utf-8')))
	else:
		file_history.append(fileinfo)
		filesinfo = ""
		for file in file_history:
			filesinfo += str(file)+"\n"

		with open("files.br","wb") as f:
			f.write(brotli.compress(filesinfo.encode('utf-8')))

	logging.info("The necessary information has been stored in your file records.")

	files = [file for file in os.listdir("temp") if os.path.isfile(os.path.join("temp", file))]

	for file in files:
		os.remove("temp\\"+file)

def retrieve_file(filename, chars_replacement):
	logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
	sesssion = requests.Session()
	manager = Manager()
	session = manager.Namespace()
	session.sesssion = sesssion

	try:
		with open("files.br", "rb") as f:
			decompressed = brotli.decompress(f.read())

		file_history = decompressed.decode("utf-8").splitlines()

		index_of_the_file = next((count for count, item in enumerate(file_history) if filename in item), None)
		if index_of_the_file == None:
			print("Check the written filename because it isn't in your file history.")
		else:
			pass

		

		file_dict = json.loads(file_history[index_of_the_file].replace("'","\""))
		while True:
			try:
				os.system("pytube https://youtu.be/"+file_dict["id"])
				break
			except:
				time.sleep(2)
				continue
		shutil.move("file "+str(file_dict["vn"])+".mp4", "temp\\file "+str(file_dict["vn"])+".mp4")

		videor = cv2.VideoCapture("temp\\file "+str(file_dict["vn"])+".mp4")
		fps= int(videor.get(cv2.CAP_PROP_FPS))
		if file_dict["fr"] < 8 and fps-file_dict["fr"]*2 != 0:
			frame_rate = file_dict["fr"]+(fps-file_dict["fr"]*2)
		else:
			frame_rate = file_dict["fr"]

		extract_frames("temp\\file "+str(file_dict["vn"])+".mp4", "temp", frame_rate)

		logging.info("Started the retrieval of keys.")
		frames_list = [file for file in os.listdir("temp") if os.path.join("temp", file).endswith(".jpg")]
		frames_list = ["frame_"+str(f) + ".jpg" for f in sorted([int(framz.replace("frame_", "").replace(".jpg", "")) for framz in frames_list])]
		key_frames = []
		for x in range(file_dict["kfc"]):
			key_frames.append(frames_list[0])
			del frames_list[0]

		key_frames_decoded = []
		for x in range(file_dict["kf"]):
			key_frames_decoded.extend(decode("temp\\"+key_frames[0]))
			del key_frames[0]

		mapping = recreate_the_mapping(file_dict["k"], key_frames_decoded)
		rebuiltkeys = rebuild_string_from_mapping(mapping)

		keys = rebuiltkeys.split("aa")
		temp_keys = []
		while len(key_frames) > 0:
			for key in keys:
				frame_decoded = decode("temp\\"+key_frames[0])
				mapping = recreate_the_mapping(key, frame_decoded)
				rebuilt = rebuild_string_from_mapping(mapping)
				temp_keys.append(rebuilt)
				del key_frames[0]

			keys.clear()
			keys = "".join(temp_keys).split("aa")
			temp_keys.clear()

		logging.info("Keys retrieved successfully.")


		reconstructed_text_list = [None]*len(frames_list)
		pool = get_context("spawn").Pool(processes=multiprocessing.cpu_count())
		input_data = [(key, frames_list[count], count, session.sesssion) for count, key in enumerate(keys)]
		results = list(tqdm(pool.imap(returner, input_data), total=len(keys), leave=False, unit="frames", desc="decoding frames"))
		pool.close()
		pool.join()

		for count, text in results:
			reconstructed_text_list[count] = text

		reconstructed_text = "".join(reconstructed_text_list)
		for char, value in chars_replacement.items():
			reconstructed_text = reconstructed_text.replace(value, char)

		if ".txt" in file_dict["n"]:
			with open(file_dict["n"],"w",encoding='utf-8') as f1:
				f1.write(reconstructed_text)
		else:
			reconstructed_text = "".join(reconstructed_text.split())
			with open(file_dict["n"],"wb") as f1:
				f1.write(brotli.decompress(base64.b64decode(reconstructed_text)))

		logging.info("The file {} has been retrieved successfully".format(file_dict["n"]))



	except:
		print("the file history is empty, please store something before proceeding with the retrieval.")


if __name__ == '__main__':
	if os.path.exists(r"temp\.gitignore"):
		os.remove(r"temp\.gitignore")
	else:
		pass
	chars_replacement_txt = {"\n":",b,", "S": ".s,", "?":".,.", "γ":",ff.", ":":". .", "0":",z,", "N": ".n,", "’":".m.", "2":",d,", "3":",t,", "4":",f,", "5":",p,", "6": ",s,", "7":",h,", "8":",e,", "9":",n,", ":":",c,", "'":",a,","@":".c.", "#":".n.", "$":".h.", "%":".p.", "&":".e.", ")":".f.", "-":".r.", "_":".l.", "=":".u.", "A": ".a,", "B": ".b,", "C": ".c,", "D": ".d,", "E": ".e,", "F": ".f,", "G": ".g,", "H": ".h,", "I": ".i,", "J": ".j,", "K": ".k,", "L": ".l,", "M": ".m,", "1":",o,", "O": ".o,", "P": ".p,", "Q": ".q,", "R": ".r,", "T": ".t,", "U": ".u,", "V": ".v,", "W": ".w,", "X": ".x,", "Y": ".y,", "Z": ".z,", "+":",g,", "*":",i,", "×":",j,", "/":",k,", "\\":",l,", "[":",m,", "]":",q,", "{":",r,", "}":",u,", "|": ",v,", "<":",w,", ">":",x,", "~":",y,", ";":".a.", "é":".b.", "è":".d.", "•":".gg.", "“":".i.", "”":".j.", "‘":".k.", "(":".s.", "©":".o.", "ñ":".q.", "€":".t.", "¥":".v.", "£":".w.", "^":".x.", "™":".y.", "α":".z.", "β":".,,", "!":",..", "δ":",a.", "ε":",b.", "ζ":",c.", "η":",d.", "θ":",e.", "ι":",f.", "κ":",g.", "λ":",h.", "μ":",i.", "ν":",j.", "ξ":",k.", "ο":",l.", "π":",m.", "ρ":",n.", "σ":",o.", "ς":",p.", "τ":",q.", "υ":",r.", "φ":",s.", "χ":",t.", "ψ":",u.", "ω":",v.", "ë":",w.", "±":",x.", "÷":",y.", "®":",z.", "\t":",aa,", "–":",bb,","—":",cc,", "\"":",dd,","`": ",ee,"}
	chars_replacement = {"S": ".s,", "0":",z,", "N": ".n,", "2":",d,", "3":",t,", "4":",f,", "5":",p,", "6": ",s,", "7":",h,", "8":",e,", "9":",n,", "=":".u.", "A": ".a,", "B": ".b,", "C": ".c,", "D": ".d,", "E": ".e,", "F": ".f,", "G": ".g,", "H": ".h,", "I": ".i,", "J": ".j,", "K": ".k,", "L": ".l,", "M": ".m,", "1":",o,", "O": ".o,", "P": ".p,", "Q": ".q,", "R": ".r,", "T": ".t,", "U": ".u,", "V": ".v,", "W": ".w,", "X": ".x,", "Y": ".y,", "Z": ".z,", "+":",g,", "/":",k,"}
	print("Welcome to Babelinkcrypt, an infinite storage system. The following list contains the commands you can execute:\n1. Store a file.\n2. Store multiple files.\n3. List existing files in the storage system.\n4. Retrieve a file.\n5. Exit the program.")

	while True:
		command = input("Please choose a command by writing its corresponding number in the list: ")

		if "1" in command:
			filename = input("Enter the filename that you want to store: ")
			if ".txt" in filename:
				chars_replacement = chars_replacement_txt
			else:
				chars_replacement = chars_replacement

			if os.stat("counter.save").st_size == 0:
				configure_deletion = input("Do you want to delete the original when it's stored?(yes or no): ")
				if "y" in configure_deletion:
					dele = "1"
					with open("counter.save","w") as delconf:
						delconf.write("1")
				elif "n" in configure_deletion:
					dele = "0"
					with open("counter.save","w") as delconf:
						delconf.write("0")

				perma = input("Is your decision permanent?(yes or no): ")
				if "y" in perma:
					with open("perma.save", "w") as perm:
						perm.write("1")
				elif "n" in perma:
					with open("perma.save", "w") as perm:
						perm.write("0")
			else:
				with open("perma.save", "r") as perm:
					perma = perm.read()

				if perma == "0":
					configure_deletion = input("Do you want to delete the original when it's stored?(yes or no): ")
					if "y" in configure_deletion:
						dele = "1"
						with open("counter.save","w") as delconf:
							delconf.write("1")
					elif "n" in configure_deletion:
						dele = "0"
						with open("counter.save","w") as delconf:
							delconf.write("0")

					perma = input("Is your decision permanent?(yes or no): ")
					if "y" in perma:
						with open("perma.save", "w") as perm:
							perm.write("1")
					elif "n" in perma:
						with open("perma.save", "w") as perm:
							perm.write("0")
				elif perma == "1":
					with open("counter.save","r") as delconf:
							dele = delconf.read()

			if os.stat("perma1.save").st_size == 0:
				configure_email = input("Do you want to use one of your emails?(yes or no): ")
				if "y" in configure_email:
					email = input("Enter your email: ")
					password = input("Enter your password: ")
					with open("user.env","w") as userenv:
						userenv.write(f"EMAIL={email}\nPASSWORD={password}")

					load_dotenv(dotenv_path="user.env")
				elif "n" in configure_email:
					load_dotenv(dotenv_path="default.env")

				perma = input("Is your decision permanent?(yes or no): ")
				if "y" in perma:
					with open("perma1.save", "w") as perm:
						perm.write("1")
				elif "n" in perma:
					with open("perma1.save", "w") as perm:
						perm.write("0")
			else:
				with open("perma1.save","r") as perm1:
					perma1 = perm1.read()

				if perma1 == "0":
					configure_email = input("Do you want to use one of your emails or the default one?(yes or no): ")
					if "y" in configure_email:
						email = input("Enter your email: ")
						password = input("Enter your password: ")
						with open("user.env","w") as userenv:
							userenv.write(f"EMAIL={email}\nPASSWORD={password}")

						load_dotenv(dotenv_path="user.env")
					elif "n" in configure_deletion:
						load_dotenv(dotenv_path="default.env")

					perma = input("Is your decision permanent?(yes or no): ")
					if "y" in perma:
						with open("perma1.save", "w") as perm:
							perm.write("1")
					elif "n" in perma:
						with open("perma1.save", "w") as perm:
							perm.write("0")
				elif perma1 == "1":
					if os.stat("user.env").st_size == 0:
						load_dotenv(dotenv_path="default.env")
					else:
						load_dotenv(dotenv_path="user.env")

			email = os.getenv('EMAIL')
			password = os.getenv('PASSWORD')
			store(filename, chars_replacement, email , password)
			if dele == "1":
				os.remove(filename)
			elif dele == "0":
				pass

		elif "2" in command:
			directorypath = input("Enter the full directory that contains only the files that you want to store: ")
			files = [file for file in os.listdir(directorypath) if os.path.isfile(os.path.join(directorypath, file))]

			if os.stat("counter.save").st_size == 0:
				configure_deletion = input("Do you want to delete the originals when it's stored?(yes or no): ")
				if "y" in configure_deletion:
					dele = "1"
					with open("counter.save","w") as delconf:
						delconf.write("1")
				elif "n" in configure_deletion:
					dele = "0"
					with open("counter.save","w") as delconf:
						delconf.write("0")

				perma = input("Is your decision permanent?(yes or no): ")
				if "y" in perma:
					with open("perma.save", "w") as perm:
						perm.write("1")
				elif "n" in perma:
					with open("perma.save", "w") as perm:
						perm.write("0")
			else:
				with open("perma.save", "r") as perm:
					perma = perm.read()

				if perma == "0":
					configure_deletion = input("Do you want to delete the originals when it's stored?(yes or no): ")
					if "y" in configure_deletion:
						dele = "1"
						with open("counter.save","w") as delconf:
							delconf.write("1")
					elif "n" in configure_deletion:
						dele = "0"
						with open("counter.save","w") as delconf:
							delconf.write("0")

					perma = input("Is your decision permanent?(yes or no): ")
					if "y" in perma:
						with open("perma.save", "w") as perm:
							perm.write("1")
					elif "n" in perma:
						with open("perma.save", "w") as perm:
							perm.write("0")
				elif perma == "1":
					with open("counter.save","r") as delconf:
							dele = delconf.read()

			if os.stat("perma1.save").st_size == 0:
				configure_email = input("Do you want to use one of your emails?(yes or no): ")
				if "y" in configure_email:
					email = input("Enter your email: ")
					password = input("Enter your password: ")
					with open("user.env","w") as userenv:
						userenv.write(f"EMAIL={email}\nPASSWORD={password}")

					load_dotenv(dotenv_path="user.env")
				elif "n" in configure_email:
					load_dotenv(dotenv_path="default.env")

				perma = input("Is your decision permanent?(yes or no): ")
				if "y" in perma:
					with open("perma1.save", "w") as perm:
						perm.write("1")
				elif "n" in perma:
					with open("perma1.save", "w") as perm:
						perm.write("0")
			else:
				with open("perma1.save","r") as perm1:
					perma1 = perm1.read()

				if perma1 == "0":
					configure_email = input("Do you want to use one of your emails or the default one?(yes or no): ")
					if "y" in configure_email:
						email = input("Enter your email: ")
						password = input("Enter your password: ")
						with open("user.env","w") as userenv:
							userenv.write(f"EMAIL={email}\nPASSWORD={password}")

						load_dotenv(dotenv_path="user.env")
					elif "n" in configure_deletion:
						load_dotenv(dotenv_path="default.env")

					perma = input("Is your decision permanent?(yes or no): ")
					if "y" in perma:
						with open("perma1.save", "w") as perm:
							perm.write("1")
					elif "n" in perma:
						with open("perma1.save", "w") as perm:
							perm.write("0")
				elif perma1 == "1":
					if os.stat("user.env").st_size == 0:
						load_dotenv(dotenv_path="default.env")
					else:
						load_dotenv(dotenv_path="user.env")

			email = os.getenv('EMAIL')
			password = os.getenv('PASSWORD')

			for file in files:
				if ".txt" in file:
					chars_replacement = chars_replacement_txt
				else:
					chars_replacement = chars_replacement
				
				store(os.path.join(directorypath,file), chars_replacement, email, password)
				if dele == "1":
					os.remove(os.path.join(directorypath,file))
				elif dele == "0":
					pass
		elif "3" in command:
			try:
				with open("files.br", "rb") as f:
					decompressed = brotli.decompress(f.read())

				file_history = decompressed.decode("utf-8").splitlines()
				for file in file_history:
					file_dict = json.loads(file.replace("'","\""))
					print(file_dict["n"])
			except:
				print("No file exists in your file records.")
		elif "4" in command:
			filename = input("Enter the filename that you want to retrieve: ")
			if ".txt" in filename:
				chars_replacement = chars_replacement_txt
			else:
				chars_replacement = chars_replacement

			retrieve_file(filename, chars_replacement)
			files = [file for file in os.listdir("temp") if os.path.isfile(os.path.join("temp", file))]
			for file in files:
				os.remove("temp\\"+file)
		elif "5" in command:
			print("I hope you enjoyed the experience.")
			break

