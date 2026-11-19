import { useEffect, useState } from 'react'
import { getHealth } from '../api/indicators'

export function useApiHealth(intervalMs = 45_000): boolean | null {
  const [connected, setConnected] = useState<boolean | null>(null)
  useEffect(() => {
    let active = true
    const check = () => getHealth().then(() => { if (active) setConnected(true) }).catch(() => { if (active) setConnected(false) })
    void check()
    const interval = window.setInterval(check, intervalMs)
    return () => { active = false; window.clearInterval(interval) }
  }, [intervalMs])
  return connected
}
