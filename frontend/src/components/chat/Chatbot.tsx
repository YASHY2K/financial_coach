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
import { Suggestion, Suggestions } from '@/components/ai-elements/suggestion';
import { useCallback, useState } from 'react';
import { toast } from 'sonner';
import { Loader2 } from 'lucide-react';

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

const suggestions = [
  'What are my spending patterns this month?',
  'How can I save more money?',
  'Analyze my budget',
  'Give me financial advice',
  'What are my biggest expenses?',
  'Help me create a savings plan',
  'Review my financial goals',
  'Suggest ways to reduce spending',
];

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
    <div className="flex h-full flex-col w-full">
      <Conversation className="w-full max-w-4xl mx-auto px-4">
        <ConversationContent className="pb-4">
          {messages.length === 0 && (
             <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4">
                <div className="bg-primary/10 p-4 rounded-full">
                    <div className="size-8 rounded-full bg-primary animate-pulse" />
                </div>
                <h2 className="text-2xl font-bold tracking-tight">How can I help you today?</h2>
                <p className="text-muted-foreground max-w-md">
                    I can help you analyze your finances, track spending, and plan for the future.
                </p>
             </div>
          )}
          
          {messages.map(({ versions, ...message }) => (
            <MessageBranch defaultBranch={0} key={message.key} className="w-full">
              <MessageBranchContent>
                {versions.map((version) => (
                  <Message from={message.from} key={`${message.key}-${version.id}`}>
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
                    <MessageContent className={message.from === 'user' ? '!bg-primary !text-primary-foreground' : '!bg-muted/50'}>
                      <MessageResponse>{version.content}</MessageResponse>
                    </MessageContent>
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
            <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          )}
        </ConversationContent>
        <ConversationScrollButton />
      </Conversation>

      <div className="w-full bg-background border-t p-4 pb-6">
        <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && (
                <Suggestions className="justify-center">
                {suggestions.slice(0, 4).map((suggestion) => (
                    <Suggestion
                    key={suggestion}
                    suggestion={suggestion}
                    onClick={handleSuggestionClick}
                    variant="outline"
                    className="hover:bg-accent transition-colors"
                    />
                ))}
                </Suggestions>
            )}

            <div className="relative rounded-2xl border bg-muted/30 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all">
                <PromptInput 
                    globalDrop 
                    multiple 
                    onSubmit={handleSubmit}
                    className="rounded-2xl overflow-hidden"
                >
                    <PromptInputHeader>
                    <PromptInputAttachmentsDisplay />
                    </PromptInputHeader>
                    <PromptInputBody>
                    <PromptInputTextarea
                        onChange={(event) => setText(event.target.value)}
                        value={text}
                        placeholder="Ask about your finances..."
                        className="bg-transparent border-0 focus-visible:ring-0 px-4 py-3 min-h-[60px]"
                    />
                    </PromptInputBody>
                    <PromptInputFooter className="px-4 pb-3">
                    <PromptInputSubmit
                        disabled={!text.trim() && status !== 'streaming'}
                        status={status}
                        className="ml-auto"
                    />
                    </PromptInputFooter>
                </PromptInput>
            </div>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;