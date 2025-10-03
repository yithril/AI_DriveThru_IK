'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface SpeakerContextType {
  isAISpeaking: boolean;
  isUserSpeaking: boolean;
  setAISpeaking: (speaking: boolean) => void;
  setUserSpeaking: (speaking: boolean) => void;
}

const SpeakerContext = createContext<SpeakerContextType | undefined>(undefined);

export function SpeakerProvider({ children }: { children: ReactNode }) {
  const [isAISpeaking, setIsAISpeaking] = useState(false);
  const [isUserSpeaking, setIsUserSpeaking] = useState(false);

  const setAISpeaking = (speaking: boolean) => {
    setIsAISpeaking(speaking);
  };

  const setUserSpeaking = (speaking: boolean) => {
    setIsUserSpeaking(speaking);
  };

  return (
    <SpeakerContext.Provider value={{
      isAISpeaking,
      isUserSpeaking,
      setAISpeaking,
      setUserSpeaking
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
