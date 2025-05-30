"use client"

import type React from "react"
import { useState } from "react"

interface LoginFormProps {
  onLogin: (user: { id: string; name: string; score: number }) => void
  t: any
}

export default function LoginForm({ onLogin, t }: LoginFormProps) {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // Simulate API call delay
    setTimeout(() => {
      // Mock user data - in a real app, this would come from your backend
      const mockUser = {
        id: "user-123",
        name: username,
        score: 3,
      }

      onLogin(mockUser)
      setIsLoading(false)
    }, 1000)
  }

  const handleSkip = () => {
    onLogin({
      id: "guest",
      name: "Guest User",
      score: 0,
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 pt-4">
      <div className="space-y-2">
        <label htmlFor="username" className="block text-sm font-medium text-label" style={{ color: 'var(--label-color)', opacity: 1 }}>
          {t('username')}
        </label>
        <input
          id="username"
          type="text"
          autoComplete="username"
          className="w-full rounded-md border border-custom px-2 py-1.5 text-sm bg-[var(--input-bg)] text-[var(--input-text)] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors placeholder-[color:var(--foreground)] placeholder-opacity-70"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          style={{ color: 'var(--input-text)', background: 'var(--input-bg)' }}
          required
        />
      </div>
      <div className="space-y-2 mt-4">
        <label htmlFor="password" className="block text-sm font-medium text-label" style={{ color: 'var(--label-color)', opacity: 1 }}>
          {t('password')}
        </label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          className="w-full rounded-md border border-custom px-2 py-1.5 text-sm bg-[var(--input-bg)] text-[var(--input-text)] focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors placeholder-[color:var(--foreground)] placeholder-opacity-70"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder={t('enterPassword')}
          style={{ color: 'var(--input-text)', background: 'var(--input-bg)' }}
          required
        />
      </div>
      <div className="flex flex-col space-y-2">
        <button
          type="submit"
          disabled={isLoading}
          className="w-full px-4 py-2 rounded-md transition-colors bg-[var(--button-bg)] text-[var(--button-text)] hover:bg-[var(--button-hover-bg)] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? t('login') + '...' : t('login')}
        </button>
        <button
          type="button"
          onClick={handleSkip}
          className="w-full border border-custom px-4 py-2 rounded-md hover:bg-secondary transition-colors"
        >
          {t('continueAsGuest')}
        </button>
      </div>
    </form>
  )
}