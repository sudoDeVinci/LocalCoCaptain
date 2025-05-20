#include "io.h"

/**
 * Attempt to initialize the sdcard file system. 
 * @return True if the sdcard was successfully mounted, false otherwise.
 */
bool sdmmcInit(){
  SD_MMC.setPins(SD_MMC_CLK, SD_MMC_CMD, SD_MMC_D0);
  if (!SD_MMC.begin("/sdcard", true, true, SDMMC_FREQ_DEFAULT, 5)) {
    debugln("Card Mount Failed");
    return false;
  }
  uint8_t cardType = SD_MMC.cardType();
  if(cardType == CARD_NONE){
      debugln("No SD_MMC card attached");
      return false;
  }

  uint64_t cardSize = SD_MMC.cardSize() / (1024 * 1024);
  debugf("SD_MMC Card Size: %lluMB\n", cardSize);  
  debugf("Total space: %lluMB\r\n", SD_MMC.totalBytes() / (1024 * 1024));
  debugf("Used space: %lluMB\r\n", SD_MMC.usedBytes() / (1024 * 1024));
  return true;
}

/**
 * Determine the file system to use for IO.
 * If we can't use the sdcard, use the local file system.
 * @return The file system reference to use for IO. 
 */
fs::FS* DetermineFileSystem() {
  if(sdmmcInit()) {
    debugln("SD_MMC mounted");
    return &SD_MMC;
  }
  if(LittleFS.begin(true)) {
    debugln("LittleFS mounted");
    return &LittleFS;
  }
  debugln("Failed to mount any file system");
  return nullptr;
}


/**
 * Format the timestamp as MySQL DATETIME.
 * If the year is 1970, return "None".
 * WARNING: Allocating new char[40] every time this function is called.
 * 
 * @param timeinfo: tm struct containing the time information.
 * 
 * @return char*: timestamp in MySQL DATETIME format.
 */
char* formattime(tm* now) {
  char *timestamp = new char[30];
  strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", now);
  return timestamp;
}


/**
 * Initialize the log file.
 * @param fs: The file system reference to use for the log file. 
 */
void initLogFile (fs::FS &fs) {
  // Check if the log file exists, if not create it.
  if(fs.exists(LOG_FILE)) return;
  File file = fs.open(LOG_FILE, FILE_WRITE, true);
  if(!file){
    debugln("Failed to open log file for writing");
    return;
  }
  JsonDocument doc;
  doc.createNestedArray("WARNINGS");
  doc.createNestedArray("ERRORS");
  if( serializeJson(doc, file) == 0) debugln("Failed to write to log file");
  else debugln("Log file Initialised");
  file.close();
}

/**
 * Read the conf file and return a dynamically allocated const char*.
 * WARNING: Dynamically allocated char array for file output.
 * @param fs: The file system reference to use for the cache.
 * @param path: The path to the file to read.
 * 
 * @return The contents of the file as a char array.
 */
const char* readFile(fs::FS &fs, const char * path) {
  debugf("\n>> Reading file: %s\r\n", path);

  String output;
  File file = fs.open(path);

  if (!file || file.isDirectory()) {
    debugf("- failed to open %s for reading\r\n", path);
    return nullptr;  // Return nullptr on failure
  }

  while (file.available()) {
    output.concat((char)file.read());
  }

  file.close();

  // Dynamically allocate memory to hold the return string
  char* result = new char[output.length() + 1];
  strcpy(result, output.c_str());
  return result;  // Return the dynamically allocated memory
}

