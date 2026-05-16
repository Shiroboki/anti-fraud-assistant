import request from './request'

export const forgotPassword = (email) =>
  request.post('/api/v1/auth/forgot-password', { email })

export const resetPassword = (token, newPassword) =>
  request.post('/api/v1/auth/reset-password', { token, newPassword })

export const verifyEmail = (token) =>
  request.post('/api/v1/auth/verify-email', { token })

export const resendVerification = (email) =>
  request.post('/api/v1/auth/resend-verification', { email })
