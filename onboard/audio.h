#pragma once
#ifndef AUDIO_H
#define AUDIO_H

#include "io.h"


struct WAVFile {
   /// The first 4 byte of a wav file should be the characters "RIFF" */
    char chunkID[4] = {'R', 'I', 'F', 'F'};
    /// 36 + SubChunk2Size
    uint32_t chunkSize = 36; // You Don't know this until you write your data but at a minimum it is 36 for an empty file
    /// "should be characters "WAVE"
    char format[4] = {'W', 'A', 'V', 'E'};
    /// " This should be the letters "fmt ", note the space character
    char subChunk1ID[4] = {'f', 'm', 't', ' '};
    ///: For PCM == 16, since audioFormat == uint16_t
    uint32_t subChunk1Size = 16;
    ///: For PCM this is 1, other values indicate compression
    uint16_t audioFormat = 1;
    ///: Mono = 1, Stereo = 2, etc.
    uint16_t numChannels = 1;
    ///: Sample Rate of file
    uint32_t sampleRate = 44100;
    ///: SampleRate * NumChannels * BitsPerSample/8
    uint32_t byteRate = 44100 * 2;
    ///: The number of byte for one frame NumChannels * BitsPerSample/8
    uint16_t blockAlign = 2;
    ///: 8 bits = 8, 16 bits = 16
    uint16_t bitsPerSample = 16;
    ///: Contains the letters "data"
    char subChunk2ID[4] = {'d', 'a', 't', 'a'};
    ///: == NumSamples * NumChannels * BitsPerSample/8  i.e. number of byte in the data.
    uint32_t subChunk2Size = 2116800; // You Don't know this until you write your data 

    int16_t* data = nullptr; // Pointer to the data buffer
}


#endif




