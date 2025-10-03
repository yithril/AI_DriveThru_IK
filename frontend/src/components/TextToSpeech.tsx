'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useTheme } from '@/contexts/ThemeContext';

interface TextToSpeechProps {
  text: string;
  autoPlay?: boolean;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
  onSpeechError?: (error: string) => void;
}

export default function TextToSpeech({ 
  text, 
  autoPlay = false, 
  onSpeechStart, 
  onSpeechEnd, 
  onSpeechError 
}: TextToSpeechProps) {
  const { theme } = useTheme();
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [rate, setRate] = useState(1);
  const [pitch, setPitch] = useState(1);
  const [volume, setVolume] = useState(1);

  useEffect(() => {
    // Load available voices
    const loadVoices = () => {
      const availableVoices = speechSynthesis.getVoices();
      setVoices(availableVoices);
      
      // Try to find a good default voice (prefer English, female)
      const defaultVoice = availableVoices.find(voice => 
        voice.lang.startsWith('en') && voice.name.includes('Female')
      ) || availableVoices.find(voice => 
        voice.lang.startsWith('en')
      ) || availableVoices[0];
      
      if (defaultVoice) {
        setSelectedVoice(defaultVoice);
      }
    };

    loadVoices();
    speechSynthesis.addEventListener('voiceschanged', loadVoices);

    return () => {
      speechSynthesis.removeEventListener('voiceschanged', loadVoices);
    };
  }, []);

  const speak = useCallback(() => {
    if (!text) return;

    // Stop any current speech
    speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    
    utterance.rate = rate;
    utterance.pitch = pitch;
    utterance.volume = volume;

    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
      onSpeechStart?.();
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      onSpeechEnd?.();
    };

    utterance.onerror = (event) => {
      console.error('Speech synthesis error:', event);
      setIsSpeaking(false);
      setIsPaused(false);
      onSpeechError?.(event.error);
    };

    speechSynthesis.speak(utterance);
  }, [text, selectedVoice, rate, pitch, onSpeechStart, onSpeechEnd]);

  useEffect(() => {
    if (autoPlay && text) {
      speak();
    }
  }, [autoPlay, text, speak]);

  const pause = () => {
    if (isSpeaking && !isPaused) {
      speechSynthesis.pause();
      setIsPaused(true);
    }
  };

  const resume = () => {
    if (isPaused) {
      speechSynthesis.resume();
      setIsPaused(false);
    }
  };

  const stop = () => {
    speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
  };

  return (
    <div className="space-y-4">
      {/* Voice Selection */}
      <div>
        <label className="block text-sm font-medium mb-2" style={{ color: theme.text.primary }}>
          Voice
        </label>
        <select
          value={selectedVoice?.name || ''}
          onChange={(e) => {
            const voice = voices.find(v => v.name === e.target.value);
            setSelectedVoice(voice || null);
          }}
          className="w-full p-2 rounded-lg border"
          style={{ 
            backgroundColor: theme.surface,
            borderColor: theme.border.primary,
            color: theme.text.primary
          }}
        >
          {voices.map((voice, index) => (
            <option key={index} value={voice.name}>
              {voice.name} ({voice.lang})
            </option>
          ))}
        </select>
      </div>

      {/* Controls */}
      <div className="flex gap-2">
        <button
          onClick={speak}
          disabled={isSpeaking && !isPaused}
          className="flex-1 py-2 px-4 rounded-lg font-medium transition-all duration-300 disabled:opacity-50"
          style={{ 
            backgroundColor: theme.button.primary,
            color: 'white'
          }}
        >
          {isSpeaking && !isPaused ? 'Speaking...' : 'Speak'}
        </button>

        {isSpeaking && (
          <>
            <button
              onClick={isPaused ? resume : pause}
              className="px-4 py-2 rounded-lg font-medium transition-colors"
              style={{ 
                backgroundColor: theme.button.secondary,
                color: 'white'
              }}
            >
              {isPaused ? 'Resume' : 'Pause'}
            </button>
            <button
              onClick={stop}
              className="px-4 py-2 rounded-lg font-medium transition-colors"
              style={{ 
                backgroundColor: '#ef4444',
                color: 'white'
              }}
            >
              Stop
            </button>
          </>
        )}
      </div>

      {/* Settings */}
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: theme.text.primary }}>
            Rate: {rate.toFixed(1)}
          </label>
          <input
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={rate}
            onChange={(e) => setRate(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: theme.text.primary }}>
            Pitch: {pitch.toFixed(1)}
          </label>
          <input
            type="range"
            min="0.5"
            max="2"
            step="0.1"
            value={pitch}
            onChange={(e) => setPitch(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1" style={{ color: theme.text.primary }}>
            Volume: {Math.round(volume * 100)}%
          </label>
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={(e) => setVolume(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>
      </div>
    </div>
  );
}


