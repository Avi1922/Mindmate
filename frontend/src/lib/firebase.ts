import { initializeApp } from 'firebase/app'
import { getAuth } from 'firebase/auth'

type FirebaseEnvironmentVariable =
  | 'VITE_FIREBASE_API_KEY'
  | 'VITE_FIREBASE_AUTH_DOMAIN'
  | 'VITE_FIREBASE_PROJECT_ID'
  | 'VITE_FIREBASE_STORAGE_BUCKET'
  | 'VITE_FIREBASE_MESSAGING_SENDER_ID'
  | 'VITE_FIREBASE_APP_ID'

function requireEnvironmentVariable(name: FirebaseEnvironmentVariable): string {
  const value = import.meta.env[name]
  if (!value || value.startsWith('replace-') || value.startsWith('your-')) {
    throw new Error(`Missing required frontend environment variable: ${name}`)
  }
  return value
}

const firebaseConfig = {
  apiKey: requireEnvironmentVariable('VITE_FIREBASE_API_KEY'),
  authDomain: requireEnvironmentVariable('VITE_FIREBASE_AUTH_DOMAIN'),
  projectId: requireEnvironmentVariable('VITE_FIREBASE_PROJECT_ID'),
  storageBucket: requireEnvironmentVariable('VITE_FIREBASE_STORAGE_BUCKET'),
  messagingSenderId: requireEnvironmentVariable('VITE_FIREBASE_MESSAGING_SENDER_ID'),
  appId: requireEnvironmentVariable('VITE_FIREBASE_APP_ID'),
}

export const firebaseApp = initializeApp(firebaseConfig)
export const firebaseAuth = getAuth(firebaseApp)
