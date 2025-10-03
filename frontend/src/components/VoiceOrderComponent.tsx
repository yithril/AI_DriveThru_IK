'use client';

import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSession } from '@/contexts/SessionContext';
import { useSpeaker } from '@/contexts/SpeakerContext';
import { apiClient } from '@/lib/api';
import VoiceRecorder from './VoiceRecorder';
import TextToSpeech from './TextToSpeech';

interface VoiceOrderComponentProps {
  onOrderReceived?: (orderText: string) => void;
  onOrderChanged?: () => void; // Callback to refresh order display
}

export default function VoiceOrderComponent({ onOrderReceived, onOrderChanged }: VoiceOrderComponentProps) {
  const { theme } = useTheme();
  const { sessionId, restaurantId, createSession, error: sessionError } = useSession();
  const { isAISpeaking, isUserSpeaking, setAISpeaking, setUserSpeaking } = useSpeaker();
  const [orderText, setOrderText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [responseText, setResponseText] = useState('');
  const [orderStateChanged, setOrderStateChanged] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRecordingComplete = async (audioBlob: Blob) => {
    if (!sessionId || !restaurantId) {
      console.error('No active session. Please create a session first.');
      return;
    }

    setIsProcessing(true);
    setError(null);
    
    try {
      // Convert Blob to File
      const audioFile = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
      
      // Send to backend for processing
      const response = await apiClient.processAudio(audioFile, sessionId, restaurantId, 'en');
      
      if (response.success) {
        setResponseText(response.response_text);
        setAudioUrl(response.audio_url);
        setOrderStateChanged(response.order_state_changed);
        
        // If we got a response, show it as the order text
        if (response.response_text) {
          setOrderText(response.response_text);
          onOrderReceived?.(response.response_text);
        }
        
        // If the order changed, trigger a refresh of the order display
        if (response.order_state_changed) {
          onOrderChanged?.();
        }
        
        console.log('Audio processed successfully:', response);
      } else {
        throw new Error('Failed to process audio');
      }
      
    } catch (error) {
      console.error('Error processing voice order:', error);
      setError(error instanceof Error ? error.message : 'Failed to process audio');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleRecordingStart = () => {
    setIsListening(true);
    setUserSpeaking(true);
  };

  const handleRecordingStop = () => {
    setIsListening(false);
    setUserSpeaking(false);
  };

  const speakOrder = () => {
    if (orderText) {
      // This will trigger the TextToSpeech component
    }
  };

  // Show waiting message if no session
  if (!sessionId || !restaurantId) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <div 
            className="w-20 h-20 mx-auto mb-4 rounded-full flex items-center justify-center"
            style={{ backgroundColor: theme.surface }}
          >
            <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ color: theme.text.muted }}>
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <h3 
            className="text-xl font-semibold mb-2"
            style={{ color: theme.text.primary }}
          >
            Voice Order Ready
          </h3>
          <p 
            className="text-sm mb-4"
            style={{ color: theme.text.secondary }}
          >
            Click "New Car" above to start a new session and enable voice ordering
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h3 
          className="text-xl font-semibold mb-2"
          style={{ color: theme.text.primary }}
        >
          Voice Order
        </h3>
        <p 
          className="text-sm"
          style={{ color: theme.text.secondary }}
        >
          Session: {sessionId?.slice(0, 8)}... | Restaurant: {restaurantId}
        </p>
      </div>

      {/* Voice Recorder */}
      <div 
        className="rounded-lg p-4"
        style={{ 
          backgroundColor: theme.surface,
          border: `1px solid ${theme.border.primary}`
        }}
      >
        <VoiceRecorder
          onRecordingComplete={handleRecordingComplete}
          onRecordingStart={handleRecordingStart}
          onRecordingStop={handleRecordingStop}
          disabled={isAISpeaking || isProcessing}
        />
      </div>

      {/* Error Display */}
      {error && (
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg" style={{ backgroundColor: '#fef2f2', border: '1px solid #fecaca' }}>
            <span style={{ color: '#dc2626' }}>❌ {error}</span>
          </div>
        </div>
      )}

      {/* Processing Status */}
      {isProcessing && (
        <div className="text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-lg" style={{ backgroundColor: theme.surface }}>
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-transparent border-t-current" style={{ color: theme.button.primary }}></div>
            <span style={{ color: theme.text.secondary }}>Processing your order...</span>
          </div>
        </div>
      )}

      {/* Audio Response */}
      {audioUrl && (
        <div 
          className="rounded-lg p-4"
          style={{ 
            backgroundColor: theme.surface,
            border: `1px solid ${theme.border.primary}`
          }}
        >
          <h4 
            className="font-medium mb-2"
            style={{ color: theme.text.primary }}
          >
            AI Response:
          </h4>
          <p 
            className="text-sm mb-3"
            style={{ color: theme.text.secondary }}
          >
            {responseText}
          </p>
          <audio 
            controls 
            className="w-full"
            src={audioUrl}
            autoPlay
            onPlay={() => setAISpeaking(true)}
            onEnded={() => setAISpeaking(false)}
            onPause={() => setAISpeaking(false)}
          >
            Your browser does not support the audio element.
          </audio>
          {orderStateChanged && (
            <p className="text-xs mt-2" style={{ color: theme.button.primary }}>
              📝 Order updated - please refresh to see changes
            </p>
          )}
        </div>
      )}

      {/* Order Text Display */}
      {orderText && (
        <div 
          className="rounded-lg p-4"
          style={{ 
            backgroundColor: theme.surface,
            border: `1px solid ${theme.border.primary}`
          }}
        >
          <h4 
            className="font-medium mb-2"
            style={{ color: theme.text.primary }}
          >
            Your Order:
          </h4>
          <p 
            className="text-sm mb-3"
            style={{ color: theme.text.secondary }}
          >
            {orderText}
          </p>
          <button
            onClick={speakOrder}
            className="px-4 py-2 rounded-lg font-medium transition-colors"
            style={{ 
              backgroundColor: theme.button.primary,
              color: 'white'
            }}
          >
            🔊 Read Order
          </button>
        </div>
      )}

      {/* Text-to-Speech for Menu Items */}
      <div 
        className="rounded-lg p-4"
        style={{ 
          backgroundColor: theme.surface,
          border: `1px solid ${theme.border.primary}`
        }}
      >
        <h4 
          className="font-medium mb-3"
          style={{ color: theme.text.primary }}
        >
          Menu Announcements
        </h4>
        <TextToSpeech 
          text="Welcome to our drive-thru! Please take a look at our menu and let us know what you'd like to order."
          autoPlay={false}
        />
      </div>

      {/* Quick Menu Announcements */}
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => {
            // This would trigger the TextToSpeech component
          }}
          className="p-3 rounded-lg font-medium text-sm transition-colors"
          style={{ 
            backgroundColor: theme.button.secondary,
            color: 'white'
          }}
        >
          🌟 Specials
        </button>
        <button
          onClick={() => {
            // This would trigger the TextToSpeech component
          }}
          className="p-3 rounded-lg font-medium text-sm transition-colors"
          style={{ 
            backgroundColor: theme.button.secondary,
            color: 'white'
          }}
        >
          🌱 Vegetarian
        </button>
      </div>
    </div>
  );
}


