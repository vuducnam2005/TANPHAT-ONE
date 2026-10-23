import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'quiet'
type StatusTone = 'ready' | 'pending' | 'neutral'

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
}

export function Button({ variant = 'primary', className = '', ...props }: ButtonProps) {
  return <button className={`button button--${variant} ${className}`.trim()} {...props} />
}

export function StatusBadge({
  tone,
  children,
}: {
  tone: StatusTone
  children: ReactNode
}) {
  return <span className={`status-badge status-badge--${tone}`}>{children}</span>
}
