'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSession } from '@/contexts/SessionContext';
import { useSpeaker } from '@/contexts/SpeakerContext';
import { apiClient } from '@/lib/api';

interface FloatingMicrophoneProps {
  orderComponentRef?: React.RefObject<{ refreshOrder: () => void }>;
}

export default function FloatingMicrophone({ orderComponentRef }: FloatingMicrophoneProps) {
  const { theme } = useTheme();
  const { sessionId, restaurantId } = useSession();
  const { isAISpeaking, isAPIProcessing, setAISpeaking, setUserSpeaking, setAPIProcessing } = useSpeaker();
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [responseText, setResponseText] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
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
    if (!sessionId || !restaurantId || hasPermission === false || isAISpeaking || isAPIProcessing) return;

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

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        stream.getTracks().forEach(track => track.stop());
        setIsRecording(false);
        setUserSpeaking(false);
        console.log('🔍 [DEBUG] FloatingMicrophone - setting isAPIProcessing to true');
        setAPIProcessing(true);

        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }

        try {
          const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
          const response = await apiClient.processAudio(audioFile, sessionId, restaurantId, 'en');
          
          if (response.success) {
            setResponseText(response.response_text);
            setAudioUrl(response.audio_url);
            
            // Trigger TTS for AI response
            if (response.audio_url) {
              setAISpeaking(true);
            } else {
              // Ensure AI speaking state is reset even when no audio
              setAISpeaking(false);
            }
            
            // Refresh order if it changed
            if (response.order_state_changed && orderComponentRef?.current) {
              orderComponentRef.current.refreshOrder();
            }
          } else {
            console.error('Failed to process audio:', response.response_text);
            setResponseText(response.response_text || 'Failed to process audio.');
          }
        } catch (error) {
          console.error('Error processing voice order:', error);
          setResponseText('Error processing voice order.');
        } finally {
          console.log('🔍 [DEBUG] FloatingMicrophone - setting isAPIProcessing to false');
          setAPIProcessing(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setUserSpeaking(true);
      setRecordingTime(0);

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
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = () => {
    if (!sessionId || !restaurantId) return theme.text.muted;
    if (hasPermission === false) return '#ef4444';
    if (isRecording) return '#ef4444';
    if (isAPIProcessing) return '#f59e0b';
    if (isAISpeaking) return '#10b981';
    return theme.primary;
  };

  // Don't render if no permission and can't get it
  if (hasPermission === false && !sessionId) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      {/* Floating Microphone Button */}
      <button
        onClick={isRecording ? stopRecording : startRecording}
        disabled={isAISpeaking || isAPIProcessing || hasPermission === false || !sessionId || !restaurantId}
        className={`w-16 h-16 rounded-full shadow-lg transition-all duration-300 flex items-center justify-center ${
          isRecording ? 'animate-pulse scale-110' : 'hover:scale-105'
        } ${(isAISpeaking || isAPIProcessing || hasPermission === false || !sessionId || !restaurantId) ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        style={{
          backgroundColor: isRecording ? '#ef4444' : 
                          isAISpeaking ? '#10b981' :
                          isAPIProcessing ? '#f59e0b' : theme.primary,
          background: isRecording ? 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' :
                      isAISpeaking ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)' :
                      isAPIProcessing ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' : theme.primary,
          boxShadow: isRecording ? '0 0 20px rgba(239, 68, 68, 0.5)' : 
                      isAISpeaking ? '0 0 20px rgba(16, 185, 129, 0.5)' :
                      isAPIProcessing ? '0 0 20px rgba(245, 158, 11, 0.5)' : '0 4px 12px rgba(0, 0, 0, 0.15)'
        }}
      >
        {/* Microphone Icon */}
        <svg 
          className="w-8 h-8 text-white" 
          fill="currentColor" 
          viewBox="0 0 24 24"
        >
          {isRecording ? (
            // Recording state - square icon
            <rect x="9" y="9" width="6" height="6" rx="1"/>
          ) : isAISpeaking ? (
            // AI speaking - speaker icon
            <>
              <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
            </>
          ) : isAPIProcessing ? (
            // Processing - loading spinner
            <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" strokeDasharray="31.416" strokeDashoffset="31.416">
              <animate attributeName="stroke-dasharray" dur="2s" values="0 31.416;15.708 15.708;0 31.416" repeatCount="indefinite"/>
              <animate attributeName="stroke-dashoffset" dur="2s" values="0;-15.708;-31.416" repeatCount="indefinite"/>
            </circle>
          ) : (
            // Default - microphone icon
            <>
              <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
              <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </>
          )}
        </svg>
      </button>

      {/* Audio Response */}
      {audioUrl && (
        <audio 
          src={audioUrl}
          autoPlay
          onPlay={() => setAISpeaking(true)}
          onEnded={() => setAISpeaking(false)}
          onPause={() => setAISpeaking(false)}
          className="hidden"
        />
      )}
    </div>
  );
}
