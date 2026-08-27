import { useEffect, useState } from 'react'

// 와이파이를 끄는 등 네트워크 인터페이스 자체가 끊기면 브라우저가 즉시
// 'offline' 이벤트를 쏴준다 — API 호출 실패를 기다릴 필요 없이 바로 감지 가능하다.
export function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(() => navigator.onLine)

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  return isOnline
}
