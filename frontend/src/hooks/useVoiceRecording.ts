'use client';

import React, { useState, useRef, useCallback } from 'react';

interface AudioRecordingState {
  isRecording: boolean;
  isSupported: boolean;
  transcript: string;
  error: string | null;
  isProcessing: boolean;
}

interface AudioRecordingActions {
  startRecording: () => void;
  stopRecording: () => void;
  clearTranscript: () => void;
}

export function useAudioRecording(): AudioRecordingState & AudioRecordingActions {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Check for browser support
  const checkSupport = useCallback(() => {
    const hasMediaRecorder = typeof MediaRecorder !== 'undefined';
    const hasGetUserMedia = navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function';
    
    console.log('Checking audio recording support:', { 
      MediaRecorder: hasMediaRecorder, 
      getUserMedia: !!hasGetUserMedia 
    });
    
    if (hasMediaRecorder && hasGetUserMedia) {
      setIsSupported(true);
      return true;
    }
    setIsSupported(false);
    setError('Audio recording is not supported in this browser');
    return false;
  }, []);

  // Check support on mount
  React.useEffect(() => {
    checkSupport();
  }, [checkSupport]);

  const startRecording = useCallback(async () => {
    setError(null);
    setTranscript('');
    
    if (!checkSupport()) {
      console.log('Audio recording not available');
      return;
    }

    try {
      console.log('Starting audio recording...');
      
      // Get microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });
      
      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        console.log('Audio recording stopped, processing...');
        
        // Create audio blob
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        console.log('Audio blob created:', audioBlob.size, 'bytes');
        
        // Send to backend for processing
        await processAudioFile(audioBlob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event);
        setError('Audio recording failed');
        setIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      };

      // Start recording
      mediaRecorder.start(1000); // Collect data every second
      setIsRecording(true);
      console.log('Audio recording started');
      
    } catch (err) {
      console.error('Error starting audio recording:', err);
      setError('Failed to start audio recording - check microphone permissions');
    }
  }, [checkSupport]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
  }, [isRecording]);

  const processAudioFile = async (audioBlob: Blob) => {
    setIsProcessing(true);
    
    try {
      // Create FormData for file upload
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('restaurant_id', '1'); // TODO: Get from context
      formData.append('language', 'en');
      
      console.log('Sending audio to backend...');
      
      // Send to backend
      const apiBaseUrl = ''; // Use relative URLs with Next.js rewrite
      const response = await fetch(`${apiBaseUrl}/api/ai/process-audio`, {
        method: 'POST',
        body: formData,
        // Don't set Content-Type, let browser set it with boundary
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      console.log('Backend response:', result);
      
      // Extract transcript from response
      if (result.success && result.data && result.data.transcript) {
        setTranscript(result.data.transcript);
        console.log('Transcript received:', result.data.transcript);
      } else {
        setError('No transcript received from backend');
      }
      
    } catch (err) {
      console.error('Error processing audio:', err);
      setError('Failed to process audio - check backend connection');
    } finally {
      setIsProcessing(false);
    }
  };

  const clearTranscript = useCallback(() => {
    setTranscript('');
    setError(null);
  }, []);

  return {
    isRecording,
    isSupported,
    transcript,
    error,
    isProcessing,
    startRecording,
    stopRecording,
    clearTranscript,
  };
}
