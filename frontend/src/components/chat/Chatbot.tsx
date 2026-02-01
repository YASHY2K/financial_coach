import {
  Attachment,
  AttachmentPreview,
  AttachmentRemove,
  Attachments,
} from '@/components/ai-elements/attachments';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import {
  Message,
  MessageBranch,
  MessageBranchContent,
  MessageBranchNext,
  MessageBranchPage,
  MessageBranchPrevious,
  MessageBranchSelector,
  MessageContent,
  MessageResponse,
} from '@/components/ai-elements/message';
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputHeader,
  type PromptInputMessage,
  PromptInputSubmit,
  PromptInputTextarea,
  usePromptInputAttachments,
} from '@/components/ai-elements/prompt-input';
import {
  Reasoning,
  ReasoningContent,
  ReasoningTrigger,
} from '@/components/ai-elements/reasoning';
import {
  Source,
  Sources,
  SourcesContent,
  SourcesTrigger,
} from '@/components/ai-elements/sources';
import { useCallback, useState } from 'react';
import { toast } from 'sonner';
import { Loader2, Bot } from 'lucide-react';
import { ChatEmptyState } from './ChatEmptyState';

interface MessageType {
  key: string;
  from: 'user' | 'assistant';
  sources?: {
    href: string;
    title: string;
  }[];
  versions: {
    id: string;
    content: string;
  }[];
  reasoning?: {
    content: string;
    duration: number;
  };
}

const initialMessages: MessageType[] = [];

const PromptInputAttachmentsDisplay = () => {
  const attachments = usePromptInputAttachments();

  if (attachments.files.length === 0) {
    return null;
  }

  return (
    <Attachments variant="inline">
      {attachments.files.map((attachment) => (
        <Attachment
          data={attachment}
          key={attachment.id}
          onRemove={() => attachments.remove(attachment.id)}
        >
          <AttachmentPreview />
          <AttachmentRemove />
        </Attachment>
      ))}
    </Attachments>
  );
};

const Chatbot = () => {
  const [text, setText] = useState<string>('');
  const [status, setStatus] = useState<'submitted' | 'streaming' | 'ready' | 'error'>('ready');
  const [messages, setMessages] = useState<MessageType[]>(initialMessages);
  const [threadId] = useState<string>(`session-${Date.now()}`);


  const addUserMessage = useCallback(
    async (content: string) => {
      const userMessage: MessageType = {
        key: `user-${Date.now()}`,
        from: 'user',
        versions: [{ id: `user-${Date.now()}`, content }],
      };

      setMessages((prev) => [...prev, userMessage]);
      setStatus('submitted');

      try {
        const response = await fetch('http://localhost:8000/chat', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: content,
            thread_id: threadId,
            conversation_history: null,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        const assistantMessage: MessageType = {
          key: `assistant-${Date.now()}`,
          from: 'assistant',
          versions: [
            {
              id: `assistant-${Date.now()}`,
              content: data.response,
            },
          ],
        };

        setMessages((prev) => [...prev, assistantMessage]);
        setStatus('ready');
      } catch (error) {
        console.error('Error calling backend:', error);
        toast.error('Failed to get response from server');
        
        const errorMessage: MessageType = {
          key: `assistant-${Date.now()}`,
          from: 'assistant',
          versions: [
            {
              id: `assistant-${Date.now()}`,
              content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please make sure the backend server is running.`,
            },
          ],
        };
        
        setMessages((prev) => [...prev, errorMessage]);
        setStatus('error');
      }
    },
    [threadId]
  );

  const handleSubmit = (message: PromptInputMessage) => {
    const hasText = Boolean(message.text);
    const hasAttachments = Boolean(message.files?.length);

    if (!(hasText || hasAttachments)) {
      return;
    }

    if (message.files?.length) {
      toast.success('Files attached', {
        description: `${message.files.length} files attached to message`,
      });
    }

    addUserMessage(message.text || 'Sent with attachments');
    setText('');
  };

  const handleSuggestionClick = (suggestion: string) => {
    setStatus('submitted');
    addUserMessage(suggestion);
  };

  return (
    <div className="flex h-full flex-col w-full bg-background/50">
      <Conversation className="w-full mx-auto px-4 pb-32">
        <ConversationContent className="max-w-4xl mx-auto w-full pb-4">
          {messages.length === 0 && (
             <ChatEmptyState onSuggestionClick={handleSuggestionClick} />
          )}
          
          {messages.map(({ versions, ...message }) => (
            <MessageBranch defaultBranch={0} key={message.key} className="w-full mb-6">
              <MessageBranchContent>
                {versions.map((version) => (
                  <Message from={message.from} key={`${message.key}-${version.id}`} className="gap-4">
                    {message.from === 'assistant' && (
                        <div className="size-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0 mt-1">
                            <Bot className="size-5 text-primary" />
                        </div>
                    )}
                    
                    <div className="flex-1 min-w-0">
                        {message.sources?.length && (
                        <Sources>
                            <SourcesTrigger count={message.sources.length} />
                            <SourcesContent>
                            {message.sources.map((source) => (
                                <Source
                                href={source.href}
                                key={source.href}
                                title={source.title}
                                />
                            ))}
                            </SourcesContent>
                        </Sources>
                        )}
                        {message.reasoning && (
                        <Reasoning duration={message.reasoning.duration}>
                            <ReasoningTrigger />
                            <ReasoningContent>{message.reasoning.content}</ReasoningContent>
                        </Reasoning>
                        )}
                        <MessageContent 
                            className={
                                message.from === 'user' 
                                ? '!bg-secondary/80 !text-secondary-foreground rounded-2xl px-5 py-3 shadow-sm' 
                                : '!bg-transparent !text-foreground !p-0'
                            }
                        >
                        <MessageResponse>{version.content}</MessageResponse>
                        </MessageContent>
                    </div>
                  </Message>
                ))}
              </MessageBranchContent>
              {versions.length > 1 && (
                <MessageBranchSelector from={message.from}>
                  <MessageBranchPrevious />
                  <MessageBranchPage />
                  <MessageBranchNext />
                </MessageBranchSelector>
              )}
            </MessageBranch>
          ))}
          {status === 'submitted' && (
            <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground ml-12">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}
        </ConversationContent>
        <ConversationScrollButton className="mb-24" />
      </Conversation>

      {/* Floating Input Area */}
      <div className="fixed bottom-0 w-full bg-gradient-to-t from-background via-background to-transparent pt-10 pb-6 px-4 z-10">
        <div className="max-w-3xl mx-auto">
            <div className="relative rounded-[2rem] border bg-background shadow-lg focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all hover:shadow-xl">
                <PromptInput 
                    globalDrop 
                    multiple 
                    onSubmit={handleSubmit}
                    className="rounded-[2rem] overflow-hidden"
                >
                    <PromptInputHeader>
                    <PromptInputAttachmentsDisplay />
                    </PromptInputHeader>
                    <PromptInputBody>
                    <PromptInputTextarea
                        onChange={(event) => setText(event.target.value)}
                        value={text}
                        placeholder="Ask about your finances..."
                        className="bg-transparent border-0 focus-visible:ring-0 px-6 py-4 min-h-[52px] max-h-[200px] resize-none"
                    />
                    </PromptInputBody>
                    <PromptInputFooter className="px-4 pb-3">
                    <PromptInputSubmit
                        disabled={!text.trim() && status !== 'streaming'}
                        status={status}
                        className="ml-auto rounded-full size-8"
                    />
                    </PromptInputFooter>
                </PromptInput>
            </div>
            <p className="text-[10px] text-center text-muted-foreground mt-3">
                AI Financial Coach can make mistakes. Please verify important information.
            </p>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;