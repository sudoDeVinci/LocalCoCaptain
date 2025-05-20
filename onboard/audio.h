#pragma once
#ifndef AUDIO_H
#define AUDIO_H

#include "io.h"

/**
 * Audio file class for WAV files.
 */
struct WAVFile {
    // WAV header fields
    char chunkID[4] = {'R', 'I', 'F', 'F'};
    uint32_t chunkSize = 36; // Will be updated after writing data
    char format[4] = {'W', 'A', 'V', 'E'};
    char subChunk1ID[4] = {'f', 'm', 't', ' '};
    uint32_t subChunk1Size = 16;
    uint16_t audioFormat = 1; // PCM = 1
    uint16_t numChannels = 1; // Mono = 1
    uint32_t sampleRate = 16000; // Common for voice recording
    uint32_t byteRate; // Calculated in constructor
    uint16_t blockAlign; // Calculated in constructor
    uint16_t bitsPerSample = 16; // 16-bit samples
    char subChunk2ID[4] = {'d', 'a', 't', 'a'};
    uint32_t subChunk2Size = 0; // Will be calculated based on actual data

    struct WaveForm {
        int16_t* data = nullptr;
        size_t size = 0; // Number of samples
    } waveForm;

    WAVFile() {
        // Calculate dependent values
        blockAlign = numChannels * bitsPerSample / 8;
        byteRate = sampleRate * blockAlign;
    }

    // Method to set sample rate
    void setSampleRate(uint32_t rate) {
        sampleRate = rate;
        byteRate = sampleRate * blockAlign;
    }

    // Method to allocate buffer for recording
    bool allocateBuffer(size_t numSamples) {
        if (waveForm.data != nullptr) {
            free(waveForm.data);
        }
        waveForm.data = (int16_t*)malloc(numSamples * sizeof(int16_t));
        if (waveForm.data == nullptr) {
            return false;
        }
        waveForm.size = numSamples;
        return true;
    }

    void write(fs::FS &filesystem, String filename) {
        // Check if the waveForm data is not null
        if (waveForm.data == nullptr || waveForm.size == 0) {
            debugln("Waveform data is null or empty");
            return;
        }

        // Calculate actual data size in bytes
        subChunk2Size = waveForm.size * blockAlign;
        chunkSize = 36 + subChunk2Size;

        File wavFile = filesystem.open(filename, FILE_WRITE);
        if (!wavFile) {
            debugln("Failed to open file for writing");
            return;
        }

        // Write the headers
        wavFile.write(chunkID, 4);
        wavFile.write((byte*)&chunkSize, 4);
        wavFile.write(format, 4);
        wavFile.write(subChunk1ID, 4);
        wavFile.write((byte*)&subChunk1Size, 4);
        wavFile.write((byte*)&audioFormat, 2);
        wavFile.write((byte*)&numChannels, 2);
        wavFile.write((byte*)&sampleRate, 4);
        wavFile.write((byte*)&byteRate, 4);
        wavFile.write((byte*)&blockAlign, 2);
        wavFile.write((byte*)&bitsPerSample, 2);
        wavFile.write(subChunk2ID, 4);
        wavFile.write((byte*)&subChunk2Size, 4);

        // Write the actual audio data
        for (size_t i = 0; i < waveForm.size; i++) {
            // Convert ADC value to WAV sample (-32768 to 32767)
            int16_t sampleValue = map(waveForm.data[i], 0, 4095, -32768, 32767);
            wavFile.write((byte*)&sampleValue, 2);
        }
        
        wavFile.close();
        debugln("WAV file written successfully");
    }
    
    // Free the buffer when done
    void freeBuffer() {
        if (waveForm.data != nullptr) {
            free(waveForm.data);
            waveForm.data = nullptr;
            waveForm.size = 0;
        }
    }
    
    ~WAVFile() {
        freeBuffer();
    }
};

#endif




