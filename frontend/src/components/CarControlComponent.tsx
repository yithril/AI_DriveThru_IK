'use client';

import React, { useState } from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { useSpeaker } from '@/contexts/SpeakerContext';
import { useData } from '@/contexts/DataContext';
import { useSession } from '@/contexts/SessionContext';
import LoadingSpinner from '@/components/LoadingSpinner';
import AudioPlayer from '@/components/AudioPlayer';

interface NewCarResponse {
  success: boolean;
  message: string;
  data: {
    session: unknown;
    greeting_audio_url?: string;
  };
}

export default function CarControlComponent() {
  const { theme } = useTheme();
  const { isAISpeaking, setAISpeaking } = useSpeaker();
  const { restaurant } = useData();
  const { sessionId, createSession, clearSession, greetingAudioUrl } = useSession();
  const [currentCar, setCurrentCar] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shouldPlayGreeting, setShouldPlayGreeting] = useState(false);

  const handleNewCar = async () => {
    setIsProcessing(true);
    setError(null);
    
    try {
      // Use the SessionContext to create a new session
      await createSession(restaurant?.id || 1);
      
      // Set the current car number and trigger greeting audio
      setCurrentCar(Math.floor(Math.random() * 100) + 1);
      setShouldPlayGreeting(true);
      
    } catch (error) {
      console.error('Error creating new car session:', error);
      setError(error instanceof Error ? error.message : 'Failed to create new car session');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCarArrived = async () => {
    if (currentCar) {
      setIsProcessing(true);
      try {
        // Use the SessionContext to clear the session
        await clearSession();
        
        console.log(`Car ${currentCar} has arrived and order is ready`);
        setCurrentCar(null);
        setShouldPlayGreeting(false);
        
      } catch (error) {
        console.error('Error handling next car:', error);
        setError(error instanceof Error ? error.message : 'Failed to handle next car');
      } finally {
        setIsProcessing(false);
      }
    }
  };

  const handleAudioPlayStart = () => {
    console.log('Greeting audio started playing');
    setAISpeaking(true);
  };

  const handleAudioPlayEnd = () => {
    console.log('Greeting audio finished playing');
    setAISpeaking(false);
    setShouldPlayGreeting(false); // Stop playing after it ends
  };

  const handleAudioError = (error: string) => {
    console.error('Audio playback error:', error);
    setAISpeaking(false);
    setError(`Audio playback failed: ${error}`);
    setShouldPlayGreeting(false); // Stop trying to play on error
  };

  return (
    <div className="space-y-4">
      <h3 
        className="text-lg font-semibold"
        style={{ color: theme.text.primary }}
      >
        Car Control
      </h3>
      
      {/* Audio Player - Hidden, plays greeting audio only when shouldPlayGreeting is true */}
      <AudioPlayer
        audioUrl={shouldPlayGreeting ? greetingAudioUrl : null}
        autoPlay={true}
        onPlayStart={handleAudioPlayStart}
        onPlayEnd={handleAudioPlayEnd}
        onError={handleAudioError}
      />
      
      {/* Error Display */}
      {error && (
        <div 
          className="p-3 rounded-lg text-sm"
          style={{ 
            backgroundColor: theme.error?.background || '#fee2e2',
            color: theme.error?.text || '#dc2626',
            border: `1px solid ${theme.error?.border || '#fca5a5'}`
          }}
        >
          {error}
        </div>
      )}
      
      {currentCar ? (
        <div 
          className="rounded-lg p-4"
          style={{ 
            backgroundColor: theme.surface,
            border: `1px solid ${theme.border.primary}`
          }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p 
                className="font-medium"
                style={{ color: theme.text.primary }}
              >
                Car #{currentCar} Active
              </p>
              <p 
                className="text-sm"
                style={{ color: theme.text.secondary }}
              >
                Order in progress
              </p>
            </div>
            <button
              onClick={handleCarArrived}
              disabled={isProcessing || isAISpeaking}
              className="text-white font-medium py-2 px-4 rounded-lg transition-all duration-300 flex items-center gap-2 disabled:cursor-not-allowed shadow-lg hover:shadow-xl"
              style={{ 
                background: (isProcessing || isAISpeaking) ? theme.button.secondary : theme.button.primary,
              }}
              onMouseEnter={(e) => {
                if (!isProcessing && !isAISpeaking) {
                  e.currentTarget.style.background = theme.button.primaryHover;
                  e.currentTarget.style.transform = 'translateY(-1px)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isProcessing && !isAISpeaking) {
                  e.currentTarget.style.background = theme.button.primary;
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
            >
              {isProcessing && <LoadingSpinner size="sm" color="text-white" />}
              {isProcessing ? 'Processing...' : isAISpeaking ? 'AI Speaking...' : 'Next Customer'}
            </button>
          </div>
        </div>
      ) : (
        <button
          onClick={handleNewCar}
          disabled={isProcessing || isAISpeaking}
          className="w-full py-3 px-4 rounded-lg font-medium transition-all duration-300 text-white shadow-lg hover:shadow-xl disabled:cursor-not-allowed flex items-center justify-center gap-2"
          style={{ 
            background: (isProcessing || isAISpeaking) ? theme.button.secondary : theme.button.primary 
          }}
          onMouseEnter={(e) => {
            if (!isProcessing && !isAISpeaking) {
              e.currentTarget.style.background = theme.button.primaryHover;
              e.currentTarget.style.transform = 'translateY(-2px)';
            }
          }}
          onMouseLeave={(e) => {
            if (!isProcessing && !isAISpeaking) {
              e.currentTarget.style.background = theme.button.primary;
              e.currentTarget.style.transform = 'translateY(0)';
            }
          }}
        >
          {isProcessing && <LoadingSpinner size="sm" color="text-white" />}
          {isProcessing ? 'Creating Session...' : isAISpeaking ? 'AI Speaking...' : 'New Car'}
        </button>
      )}
      
      <div 
        className="text-xs text-center"
        style={{ color: theme.text.muted }}
      >
        {currentCar 
          ? `Managing order for Car #${currentCar}`
          : 'Click "New Car" to start a new order'
        }
      </div>
    </div>
  );
}
