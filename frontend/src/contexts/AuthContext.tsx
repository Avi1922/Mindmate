import {
  createUserWithEmailAndPassword,
  onAuthStateChanged,
  setPersistence,
  signInWithEmailAndPassword,
  signOut,
  browserLocalPersistence,
  type User,
} from 'firebase/auth'
import { useEffect, useMemo, useState, type ReactNode } from 'react'

import { firebaseAuth } from '../lib/firebase'
import { AuthContext, type AuthContextValue } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true

    void setPersistence(firebaseAuth, browserLocalPersistence).catch(() => {
      // Firebase still falls back to its available persistence mechanism.
    })

    const unsubscribe = onAuthStateChanged(firebaseAuth, (nextUser) => {
      if (active) {
        setUser(nextUser)
        setLoading(false)
      }
    })

    return () => {
      active = false
      unsubscribe()
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      register: async (email, password) => {
        await createUserWithEmailAndPassword(firebaseAuth, email, password)
      },
      login: async (email, password) => {
        await signInWithEmailAndPassword(firebaseAuth, email, password)
      },
      logout: async () => {
        await signOut(firebaseAuth)
      },
      getIdToken: async () => {
        if (!firebaseAuth.currentUser) {
          throw new Error('Authentication required')
        }
        return firebaseAuth.currentUser.getIdToken()
      },
    }),
    [loading, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
