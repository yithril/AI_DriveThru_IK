'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SpeakerContextType {
  isAISpeaking: boolean;
  isUserSpeaking: boolean;
  isAPIProcessing: boolean;
  setAISpeaking: (speaking: boolean) => void;
  setUserSpeaking: (speaking: boolean) => void;
  setAPIProcessing: (processing: boolean) => void;
}

const SpeakerContext = createContext<SpeakerContextType | undefined>(undefined);

export function SpeakerProvider({ children }: { children: ReactNode }) {
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);
  const [isAPIProcessing, setIsAPIProcessing] = useState(false);

  const setAISpeaking = (speaking: boolean) => {
    console.log(`DEBUG: setAISpeaking called with: ${speaking}, current state: ${isAISpeaking}`);
    console.trace('setAISpeaking call stack');
    setIsAISpeaking(speaking);
  };

  const setUserSpeaking = (speaking: boolean) => {
    setIsUserSpeaking(speaking);
  };

  const setAPIProcessing = (processing: boolean) => {
    setIsAPIProcessing(processing);
  };

  return (
    <SpeakerContext.Provider value={{
      isAISpeaking,
      isUserSpeaking,
      isAPIProcessing,
      setAISpeaking,
      setUserSpeaking,
      setAPIProcessing
    }}>
      {children}
    </SpeakerContext.Provider>
  );
}

export function useSpeaker() {
  const context = useContext(SpeakerContext);
  if (context === undefined) {
    throw new Error('useSpeaker must be used within a SpeakerProvider');
  }
  return context;
}
