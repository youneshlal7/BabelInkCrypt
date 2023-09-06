# BabelInkCrypt
BabelInkCrypt is an open-source project that combines encryption, the library of Babel, and video-making to create a secure infinite storage system.

# How it works

BabelInkCrypt is a Python project designed to handle various file operations, including storing, retrieving, and managing multiple files simultaneously.

For the storing function, it first checks the file's extension. If the file is a text file, it reads it directly. If it's not a text file, it compresses the file using the Brotli compression algorithm and then encodes it in base64. Depending on the file type, it may also replace certain characters using a specific dictionary. Text files use an extended character set, adding 113 characters to the standard 29 characters. Another dictionary adds an additional 39 characters required for base64 encoding.

After character replacement, the text is split into parts, each containing 3200 characters. This specific length is chosen because Babel's library contains every combination of 3200 characters using a character set of 29 characters. The algorithm searches for each part's location in the library.

Upon retrieving all locations, you'll have a list, with each element representing a location. The first element is a 3254-character hexagon made up of 36 characters, followed by the wall number, shelf, volume, and page. The hexagon's characters are analyzed for frequency, and the results include letters followed by their frequencies. For numbers, we represent them using the first two letters of their names phonetically.

The wall, shelf, volume, and page information is added to the frequency key. Simultaneously, a mapping dictionary is created, linking letters to their positions in the text. Multithreading is employed to expedite this process.

The list of keys is then combined into a single string, with keys separated by "aa." If the resulting string is less than 4095 characters, a final key is created and stored in your file records (files.br).However, instead of adding this key as the first element in the list, the first element of the list receives the number list resulting from the processing of the character positions in the text. If the string exceeds 4095 characters, the process is repeated with 3339-character segments until the combined keys fit within the limit.

Next, the list of key frames and content frames is used to generate images, each with dimensions of 1280 by 720 pixels. Each image represents the entire list of numbers from 1 to 3254 (or 1 to 3339) with each number represented by 12 bits. To enhance video compression on platforms like YouTube, each bit of the 12 bits is redundantly repeated 22 times.

This process is repeated for each element in the outside list, utilizing multiprocessing to make use of all available CPU cores. The frames are saved in a temporary folder(temp).

Once frame creation is complete, a video is generated with an FPS determined by the number of frames (If the number of frames exceeds 30, the default frame rate is set to 30 FPS). The video is then uploaded to YouTube using SeleniumBase, a library that automates Google Chrome without detection.

You have two options for uploading: using one of your accounts or the default one, though the default account may have upload restrictions due to frequent use. After uploading, the Chrome window is closed, and the file records are updated with information about the file name , the video name , the key, key frames, key frame count, video ID on YouTube, and frame rate.

This information is stored in a dictionary, and if you've previously stored data in the file records or written directly to it, the file is compressed using the Brotli compression algorithm. The resulting dictionary typically does not exceed 197 bytes, even for large files. The algorithm's speed may vary depending on your PC's specifications, including CPU cores, RAM, disk writing speed, and internet speed.

At the end of the process, the files in the temporary folder are then deleted. Additionally, you have the option to delete your original file directly after completion if you choose to do so when prompted at the beginning of your experience.

The retrieval function is essentially the reversal function of the store function. It is designed to retrieve your stored files from the file records and restore them to their original locations, but with a caveat. The retrieval function can successfully recover files only if they exist in the file records.

For text files, it's important to note that there might be some loss in cases where characters used in the original text file are outside the character set used during the storing process. These characters may not be accurately recovered, so it's recommended to consider this limitation when using the retrieval function.

# How To install and use:

To install the program in your system first clone the repository, running the following command in the cmd:
```
git clone https://github.com/youneshlal7/BabelInkCrypt.git
```
then change the directory to the folder where the code exists
```
cd BabelInkCrypt
```
after that install the requirements to run the script
```
pip install -r requirements.txt
```
delete the .gitignore file in the temp folder and run the following command:
```
python main.py
```

