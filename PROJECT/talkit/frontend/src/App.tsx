import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { HomePage } from '@/pages/HomePage'
import { ChatPage } from '@/pages/ChatPage'
import { AdminPage } from '@/pages/AdminPage'
import { TopicPage } from '@/pages/TopicPage'
import { RoleplayPage } from '@/pages/RoleplayPage'
import { TutorTopicSelectPage } from '@/pages/TutorTopicSelectPage'
import { ModeSelectPage } from '@/pages/ModeSelectPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { OfflineBanner } from '@/components/common/OfflineBanner'

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <OfflineBanner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route
            path="/tutor"
            element={<ModeSelectPage nextPath="/tutor/topics" headerTitle="AI 튜터" />}
          />
          <Route path="/tutor/topics" element={<TutorTopicSelectPage />} />
          <Route path="/topics" element={<TopicPage />} />
          <Route
            path="/roleplay"
            element={<ModeSelectPage nextPath="/roleplay/scenarios" headerTitle="AI 롤플레이" />}
          />
          <Route path="/roleplay/scenarios" element={<RoleplayPage />} />
          <Route path="/admin" element={<AdminPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
