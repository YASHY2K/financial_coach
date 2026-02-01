import Chatbot from './components/chat/Chatbot'
import { Toaster } from 'sonner';
import './App.css'

function App() {
  return (
    <div className="App bg-background text-foreground flex flex-col h-full">
      <header className="p-4 border-b">
        <h1 className="text-xl font-bold">Financial Coach</h1>
      </header>
      <div className="flex-1 overflow-hidden">
        <Chatbot />
      </div>
      <Toaster />
    </div>
  )
}


export default App
