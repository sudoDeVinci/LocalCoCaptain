#pragma once
#ifndef IO_H
#define IO_H

#include "FS.h"
#include <LittleFS.h>
#include "SD_MMC.h"

#define DEBUG 1

#if DEBUG == 1
#define debug(...) Serial.print(__VA_ARGS__)
#define debugln(...) Serial.println(__VA_ARGS__)
#define debugf(...) Serial.printf(__VA_ARGS__)
#else
#define debug(...)
#define debugln(...)
#define debugf(...)
#endif


#define LOG_FILE "/log.json"
#define MAX_PATH_LENGTH 32

#define SD_MMC_CMD  38 //Please do not modify it.
#define SD_MMC_CLK  39 //Please do not modify it. 
#define SD_MMC_D0   40 //Please do not modify it.



/**
 * Attempt to initialize the sdcard file system. 
 * @return True if the sdcard was successfully mounted, false otherwise.
 */
bool sdmmcInit(void);

/**
 * Determine the file system to use for IO.
 * If we can't use the sdcard, use the local file system.
 * @return The file system reference to use for IO. 
 */
fs::FS* DetermineFileSystem(void);

/**
 * Initialize the log file.
 * @param fs: The file system reference to use for the log file. 
 */
void initLogFile (fs::FS &fs);

/**
 * Read the conf file and return a dynamically allocated const char*.
 * WARNING: Dynamically allocated char array for file output.
 * @param fs: The file system reference to use for the cache.
 * @param path: The path to the file to read.
 * 
 * @return The contents of the file as a char array.
 */
const char* readFile (fs::FS &fs, const char * path);

/**
 * Format the timestamp as MySQL DATETIME.
 * If the year is 1970, return "None".
 * WARNING: Allocating new char[40] every time this function is called.
 * @param timeinfo: tm struct within global Network struct to store the time information.
 * 
 * @return char*: timestamp in MySQL DATETIME format.
 */
char* formattime(tm* now);


#endif