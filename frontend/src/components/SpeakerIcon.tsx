'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSpeaker } from '@/contexts/SpeakerContext';
import { useSession } from '@/contexts/SessionContext';
import { useOrder } from '@/contexts/OrderContext';
import { apiClient } from '@/lib/api';
import { playCannedPhrase } from '@/lib/s3-utils';

interface SpeakerIconProps {
  isActive?: boolean;
  isDisabled?: boolean;
  onOrderChanged?: () => void; // Callback to refresh order display
}

export default function SpeakerIcon({ isActive = false, isDisabled = false }: SpeakerIconProps) {
  const { theme } = useTheme();
  const { isAISpeaking, isUserSpeaking, setUserSpeaking, setAISpeaking } = useSpeaker();
  const { sessionId, restaurantId } = useSession();
  const { triggerOrderRefresh } = useOrder();
  const [isHovered, setIsHovered] = useState(false);
  const [isMouseDown, setIsMouseDown] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [error, setError] = useState<string | null>(null);
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
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        processRecording(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);
      setUserSpeaking(true);

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
      setUserSpeaking(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const processRecording = async (audioBlob: Blob) => {
    if (!sessionId || !restaurantId) {
      console.error('No active session. Please create a session first.');
      return;
    }

    setIsProcessing(true);
    setError(null);
    
    try {
      // Convert Blob to File
      const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
      
      // Send to backend for processing with session ID
      const response = await apiClient.processAudio(audioFile, sessionId, restaurantId, 'en');
      
      if (response.success) {
        // If we got an audio response, play it
        if (response.audio_url) {
          const audio = new Audio(response.audio_url);
          audio.play();
          setAISpeaking(true);
          audio.onended = () => setAISpeaking(false);
        } else {
          // Ensure AI speaking state is reset even when no audio
          setAISpeaking(false);
        }
        
        // Check if order state changed and trigger refresh
        if (response.order_state_changed) {
          triggerOrderRefresh();
        }
        
        console.log('Audio processed successfully:', response);
      } else {
        throw new Error('Failed to process audio');
      }
      
    } catch (error) {
      console.error('Error processing voice order:', error);
      setError(error instanceof Error ? error.message : 'Failed to process audio');
      
      // Play "come again" audio on error
      try {
        await playCannedPhrase('come_again', restaurantId);
        setAISpeaking(true);
        // Reset AI speaking state after a short delay
        setTimeout(() => setAISpeaking(false), 3000);
      } catch (audioError) {
        console.error('Failed to play error audio:', audioError);
      }
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle mouse down (start recording)
  const handleMouseDown = () => {
    if (isDisabled) {
      console.log('Recording disabled - no session or AI speaking');
      return;
    }
    if (isProcessing) {
      console.log('Cannot record while processing previous request');
      return;
    }
    if (!hasPermission) {
      console.error('Microphone permission denied');
      return;
    }
    if (isAISpeaking) {
      console.log('Cannot record while AI is speaking');
      return;
    }
    setIsMouseDown(true);
    startRecording();
  };

  // Handle mouse up (stop recording)
  const handleMouseUp = () => {
    setIsMouseDown(false);
    stopRecording();
  };

  // Handle mouse leave (stop recording if mouse leaves while recording)
  const handleMouseLeave = () => {
    if (isMouseDown) {
      setIsMouseDown(false);
      stopRecording();
    }
  };

  // Combine both speaking states for visual indication
  const isSpeaking = isAISpeaking || isUserSpeaking;

  // Determine speaker state and color
  const getSpeakerState = () => {
    if (isDisabled && !isAISpeaking) return { color: theme.text.muted, label: 'No active session - click "New Car" to start' };
    if (isDisabled && isAISpeaking) return { color: theme.button.primary, label: 'AI Speaking...' };
    if (isAISpeaking) return { color: theme.button.primary, label: 'AI Speaking...' };
    if (isProcessing) return { color: '#f59e0b', label: 'Processing audio...' };
    if (isRecording) return { color: '#ef4444', label: 'Recording... Release to send' };
    if (isUserSpeaking) return { color: theme.secondary, label: 'Customer Speaking...' };
    return { color: theme.button.secondary, label: 'Hold down and speak' };
  };

  const speakerState = getSpeakerState();

  // Show permission error if microphone access is denied
  if (hasPermission === false) {
    return (
      <div className="fixed bottom-6 right-6 z-50">
        <div 
          className="w-20 h-20 rounded-full flex items-center justify-center shadow-lg bg-gray-400 cursor-not-allowed"
          title="Microphone access required - please allow microphone access"
        >
          <svg 
            className="w-10 h-10 text-white" 
            fill="currentColor" 
            viewBox="0 0 24 24"
          >
            <path d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
          </svg>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div 
        className={`w-20 h-20 rounded-full flex items-center justify-center shadow-lg transition-all duration-300 ${
          isSpeaking ? 'animate-pulse' : ''
        } ${(isDisabled || isProcessing) ? 'cursor-not-allowed opacity-60' : 'cursor-pointer hover:shadow-xl'} select-none`}
        style={{ 
          backgroundColor: speakerState.color,
          transform: isHovered && !isDisabled && !isProcessing ? 'scale(1.1)' : 'scale(1)',
          boxShadow: isSpeaking ? `0 0 20px ${speakerState.color}` : undefined
        }}
        title={speakerState.label}
        onMouseEnter={() => !isDisabled && !isProcessing && setIsHovered(true)}
        onMouseLeave={handleMouseLeave}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onTouchStart={handleMouseDown}
        onTouchEnd={handleMouseUp}
      >
        <svg 
          className="w-10 h-10 text-white" 
          fill="currentColor" 
          viewBox="0 0 24 24"
        >
          <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
        </svg>
      </div>
      
      {/* Show recording timer */}
      {isRecording && (
        <div 
          className="absolute bottom-24 right-0 bg-black bg-opacity-80 text-white p-3 rounded-lg max-w-xs text-sm"
          style={{ zIndex: 60 }}
        >
          <div className="font-semibold mb-1">Recording:</div>
          <div>{Math.floor(recordingTime / 60)}:{(recordingTime % 60).toString().padStart(2, '0')}</div>
        </div>
      )}
      
      {/* Show ready message when speaker is available and not disabled */}
      {!isDisabled && !isAISpeaking && !isRecording && !isProcessing && hasPermission !== false && (
        <div 
          className="absolute bottom-24 right-0 bg-green-600 text-white p-3 rounded-lg max-w-xs text-sm animate-pulse"
          style={{ zIndex: 60 }}
        >
          <div className="font-semibold mb-1">🎤 Ready!</div>
          <div>Hold down and speak your order</div>
        </div>
      )}
      
      {/* Show error message */}
      {error && (
        <div 
          className="absolute bottom-24 right-0 bg-red-600 text-white p-3 rounded-lg max-w-xs text-sm"
          style={{ zIndex: 60 }}
        >
          <div className="font-semibold mb-1">Error:</div>
          <div>{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-2 text-xs text-gray-300 hover:text-white underline"
          >
            Reload Page
          </button>
        </div>
      )}
    </div>
  );
}
