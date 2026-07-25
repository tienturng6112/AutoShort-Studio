# AutoShort Studio - Sprint 10 Voice Engine Architecture

This document describes the architectural design, workflows, and diagrams of the Voice Synthesis Engine.

---

## 1. Voice Engine Architecture

The Voice Synthesis Engine sits between the Timeline Alignment Engine and the Subtitle Engine:

```
[Alignment Engine] -> [Voice Synthesis Engine] -> [Subtitle Engine] -> [Render Engine]
```

It takes aligned segments and generates speech files, placing them at their respective start times and inserting silence clips in the timeline gaps.

---

## 2. Module Dependency Diagram

The voice engine modules cooperate to synthesize audio files:

```
[VoiceService]
   │
   ├──> [BaseTTSProvider] (EdgeTTSProvider)
   ├──> [VoiceCache]
   ├──> [SilenceGenerator] (ffmpeg)
   ├──> [AudioMerger]      (ffmpeg concat)
   └──> [AudioNormalizer]  (ffmpeg loudnorm)
```

---

## 3. Class Diagram

The class diagram below shows the relationships between our voice synthesis classes:

```mermaid
classDiagram
    class BaseTTSProvider {
        <<interface>>
        +list_voices() List*
        +generate(text, voice_name, output_path) Tuple*
        +preview(text, voice_name) bytes*
    }

    class EdgeTTSProvider {
        +list_voices() List
        +generate(text, voice_name, output_path) Tuple
        +preview(text, voice_name) bytes
    }

    class VoiceManager {
        -providers: Dict
        +register_provider(name, provider)
        +list_voices(language, gender, provider_name) List
    }

    class VoiceCache {
        -cache_dir: string
        +get(text, voice_name) string
        +set(text, voice_name, source_path) string
        +clear()
    }

    class SilenceGenerator {
        +generate_silence(duration, output_path, sample_rate, channels) string
    }

    class AudioMerger {
        +merge_audio_files(file_list, output_path) string
    }

    class AudioNormalizer {
        +normalize_audio(input_path, output_path, sample_rate, channels, target_loudness) string
    }

    class VoiceService {
        -provider: BaseTTSProvider
        -cache: VoiceCache
        -temp_dir: string
        +synthesize_transcript(transcript, voice_name, output_dir) Tuple
    }

    BaseTTSProvider <|-- EdgeTTSProvider
    VoiceService --> BaseTTSProvider
    VoiceService --> VoiceCache
    VoiceService --> SilenceGenerator
    VoiceService --> AudioMerger
    VoiceService --> AudioNormalizer
```

---

## 4. Sequence Diagram

This trace maps the voice synthesis process from the initial call to caching, silence gap generation, audio merging, and loudness normalization.

```mermaid
sequenceDiagram
    autonumber
    actor Client as Workflow Orchestrator
    participant VS as VoiceService
    participant VC as VoiceCache
    participant EP as EdgeTTSProvider
    participant SG as SilenceGenerator
    participant AM as AudioMerger
    participant AN as AudioNormalizer

    Client->>VS: synthesize_transcript(transcript, "en-US-GuyNeural", "output/")
    
    alt Initial silence gap exists
        VS->>SG: generate_silence(start_gap, "silence_init.wav")
        SG-->>VS: "silence_init.wav"
    end
    
    loop For each Segment
        VS->>VC: get(segment_text, "en-US-GuyNeural")
        alt Cache Hit
            VC-->>VS: "cached_file.wav"
        else Cache Miss
            VS->>EP: generate(segment_text, "en-US-GuyNeural", "seg_x.wav")
            EP-->>VS: "seg_x.wav", word_boundaries
            VS->>VC: set(segment_text, "en-US-GuyNeural", "seg_x.wav")
            VC-->>VS: "cached_file.wav"
        end
        
        alt Gap exists between current and next segment
            VS->>SG: generate_silence(gap_duration, "silence_gap.wav")
            SG-->>VS: "silence_gap.wav"
        end
    end
    
    VS->>AM: merge_audio_files(audio_segments_list, "merged_raw.wav")
    AM->>AM: Run FFmpeg concat demuxer
    AM-->>VS: "merged_raw.wav"
    
    VS->>AN: normalize_audio("merged_raw.wav", "voice.wav")
    AN->>AN: Run FFmpeg loudnorm (EBU R128 standard)
    AN-->>VS: "voice.wav"
    
    VS->>AN: normalize_audio("merged_raw.wav", "voice.mp3")
    AN->>AN: Run FFmpeg loudnorm + MP3 encoder
    AN-->>VS: "voice.mp3"
    
    VS-->>Client: "voice.wav", "voice.mp3", benchmark_data
```

---

## 5. Workflows & Subsystem Designs

### Voice Generation Workflow
- Takes aligned segments and loops through them to synthesize speech.
- Calls registered providers to generate speech files for each segment.

### Cache Workflow
- Performs an MD5 hash check using: `voice_name:segment_text`.
- If a cached file is found in the cache directory, it is reused, avoiding redundant provider calls.
- If not found, a new speech file is synthesized and saved to the cache.

### Silence Generation Workflow
- Runs FFmpeg's `anullsrc` virtual filter to generate silence clips matching the target sample rate and channels.
- These silence clips are used to fill timeline gaps between segments.

### Audio Merge Workflow
- Writes the list of audio clips (speech segments and silence gaps) to a temporary text file.
- Runs FFmpeg's `concat` demuxer with stream copy parameters (`-c copy`) to merge the clips without re-encoding them.

### Audio Normalization Workflow
- Runs FFmpeg's `loudnorm` filter (EBU R128 standard) to normalize the volume of the merged audio track.
- Resamples the audio to 16kHz and downmixes it to mono.

---

## 6. Extension Points & Future Compatibility

* **Additional TTS Providers**: Implement `BaseTTSProvider` to support cloud-based providers (e.g. ElevenLabs, OpenAI TTS, AWS Polly).
* **Multi-Voice Transcripts**: Support using different voices for different segments within a single transcript.
* **Variable Speech Rates**: Add support for speed rate configuration parameters (e.g. speeding up speech to fit segment durations).
