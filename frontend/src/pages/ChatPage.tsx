import Chatbot from '@/components/chat/Chatbot';

export default function ChatPage() {
  return (
    <div className="h-full w-full flex flex-col p-4">
        <div className="flex-1 overflow-hidden border rounded-xl bg-background/50 backdrop-blur-sm shadow-sm">
            <Chatbot />
        </div>
    </div>
  );
}