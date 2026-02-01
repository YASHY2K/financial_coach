import Chatbot from './components/chat/Chatbot'
import { Toaster } from 'sonner';
import './App.css'

function App() {
  return (
    // Force dark mode for high contrast as requested. 
    // In a real app, this would be a ThemeProvider.
    <div className="dark h-full w-full bg-background text-foreground antialiased selection:bg-primary selection:text-primary-foreground">
      <div className="flex h-full flex-col overflow-hidden">
        <header className="flex h-14 items-center border-b px-6 shrink-0 bg-muted/20 backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <div className="size-6 rounded-full bg-primary" />
            <h1 className="text-lg font-semibold tracking-tight">Financial Coach</h1>
          </div>
        </header>
        <main className="flex-1 overflow-hidden relative">
          <Chatbot />
        </main>
      </div>
      <Toaster />
    </div>
  )
}

export default App