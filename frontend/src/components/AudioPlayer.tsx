'use client';

import React, { useRef, useEffect } from 'react';

interface AudioPlayerProps {
  audioUrl?: string | null;
  autoPlay?: boolean;
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
  onError?: (error: string) => void;
}

export default function AudioPlayer({ 
  audioUrl, 
  autoPlay = true, 
  onPlayStart, 
  onPlayEnd, 
  onError 
}: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !audioUrl) return;

    const handlePlay = () => {
      onPlayStart?.();
    };

    const handleEnded = () => {
      onPlayEnd?.();
    };

    const handleError = () => {
      const error = audio.error?.message || 'Audio playback failed';
      onError?.(error);
    };

    audio.addEventListener('play', handlePlay);
    audio.addEventListener('ended', handleEnded);
    audio.addEventListener('error', handleError);

    // Auto-play if enabled
    if (autoPlay && audioUrl) {
      audio.play().catch(err => {
        onError?.(err.message);
      });
    }

    return () => {
      audio.removeEventListener('play', handlePlay);
      audio.removeEventListener('ended', handleEnded);
      audio.removeEventListener('error', handleError);
    };
  }, [audioUrl, autoPlay, onPlayStart, onPlayEnd, onError]);

  // Don't render anything if no audio URL
  if (!audioUrl) {
    return null;
  }

  return (
    <audio
      ref={audioRef}
      src={audioUrl}
      preload="auto"
      style={{ display: 'none' }}
    />
  );
}
