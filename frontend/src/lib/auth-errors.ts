import { FirebaseError } from 'firebase/app'

const friendlyMessages: Record<string, string> = {
  'auth/email-already-in-use': 'An account already exists for this email address.',
  'auth/invalid-credential': 'The email or password is incorrect.',
  'auth/invalid-email': 'Enter a valid email address.',
  'auth/network-request-failed': 'The network request failed. Check your connection and try again.',
  'auth/operation-not-allowed': 'Email and password sign-in is not enabled for this project.',
  'auth/too-many-requests': 'Too many attempts. Wait a moment before trying again.',
  'auth/user-disabled': 'This account has been disabled.',
  'auth/weak-password': 'Choose a stronger password with at least eight characters.',
}

export function getAuthenticationErrorMessage(error: unknown): string {
  if (error instanceof FirebaseError) {
    return friendlyMessages[error.code] ?? 'Authentication failed. Please try again.'
  }
  return 'Authentication failed. Please try again.'
}
