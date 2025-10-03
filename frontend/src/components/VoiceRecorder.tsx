'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';

interface VoiceRecorderProps {
  onRecordingComplete: (audioBlob: Blob) => void;
  onRecordingStart?: () => void;
  onRecordingStop?: () => void;
  disabled?: boolean;
}

export default function VoiceRecorder({ 
  onRecordingComplete, 
  onRecordingStart, 
  onRecordingStop,
  disabled = false
}: VoiceRecorderProps) {
  const { theme } = useTheme();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Check for microphone permission on component mount
    checkMicrophonePermission();
  }, []);

  const checkMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      setHasPermission(true);
    } catch (error) {
      console.error('Microphone permission denied:', error);
      setHasPermission(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        onRecordingComplete(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      onRecordingStart?.();

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Error starting recording:', error);
      setHasPermission(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      onRecordingStop?.();
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (hasPermission === false) {
    return (
      <div className="text-center p-4">
        <div className="mb-4">
          <div className="w-16 h-16 mx-auto mb-2 rounded-full flex items-center justify-center" style={{ backgroundColor: theme.surface }}>
            <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: theme.text.muted }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <p style={{ color: theme.text.secondary }}>Microphone access required</p>
          <p className="text-sm" style={{ color: theme.text.muted }}>
            Please allow microphone access to record voice orders
          </p>
        </div>
        <button
          onClick={checkMicrophonePermission}
          className="px-4 py-2 rounded-lg font-medium transition-colors"
          style={{ 
            backgroundColor: theme.button.secondary,
            color: 'white'
          }}
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="text-center p-4 relative">
      {/* Floating "Press and hold" tooltip */}
      {!isRecording && !disabled && (
        <div className="absolute -top-12 left-1/2 transform -translate-x-1/2 z-10">
          <div 
            className="px-3 py-1 rounded-lg text-xs font-medium shadow-lg"
            style={{ 
              backgroundColor: theme.surface,
              border: `1px solid ${theme.border.primary}`,
              color: theme.text.primary
            }}
          >
            Press and hold
          </div>
          <div 
            className="w-2 h-2 transform rotate-45 mx-auto -mt-1"
            style={{ backgroundColor: theme.surface }}
          ></div>
        </div>
      )}
      
      <div className="mb-4">
        <div 
          className={`w-20 h-20 mx-auto mb-3 rounded-full flex items-center justify-center transition-all duration-300 ${
            isRecording ? 'animate-pulse' : ''
          }`}
          style={{ 
            backgroundColor: isRecording ? '#ef4444' : theme.button.primary,
            background: isRecording ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' : theme.button.primary
          }}
        >
          <svg className="w-10 h-10 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
            <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
          </svg>
        </div>
        
        {isRecording && (
          <div className="mb-2">
            <p className="text-2xl font-bold" style={{ color: theme.text.primary }}>
              {formatTime(recordingTime)}
            </p>
            <p className="text-sm" style={{ color: theme.text.secondary }}>
              Recording...
            </p>
          </div>
        )}
        
        {!isRecording && (
          <div>
            <p className="text-lg font-semibold mb-1" style={{ color: theme.text.primary }}>
              Voice Order
            </p>
            <p className="text-sm" style={{ color: theme.text.secondary }}>
              {disabled ? 'AI is speaking...' : 'Click to start recording your order'}
            </p>
          </div>
        )}
      </div>

      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={disabled}
        className={`px-6 py-3 rounded-lg font-medium transition-all duration-300 ${
          isRecording ? 'hover:shadow-lg' : 'hover:shadow-xl'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
        style={{ 
          background: isRecording ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' : 
                     disabled ? theme.text.muted : theme.button.primary,
          color: 'white'
        }}
        onMouseEnter={(e) => {
          if (!isRecording && !disabled) {
            e.currentTarget.style.background = theme.button.primaryHover;
            e.currentTarget.style.transform = 'translateY(-2px)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isRecording && !disabled) {
            e.currentTarget.style.background = theme.button.primary;
            e.currentTarget.style.transform = 'translateY(0)';
          }
        }}
      >
        {isRecording ? 'Stop Recording' : disabled ? 'AI is Speaking...' : 'Start Recording'}
      </button>
    </div>
  );
}


