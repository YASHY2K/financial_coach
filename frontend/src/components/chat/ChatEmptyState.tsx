import { Suggestion } from '@/components/ai-elements/suggestion';
import { Sparkles, TrendingUp, PiggyBank, Target } from 'lucide-react';

interface ChatEmptyStateProps {
  onSuggestionClick: (suggestion: string) => void;
}

const suggestions = [
  { 
    text: 'What are my spending patterns this month?', 
    icon: TrendingUp,
    color: 'text-blue-500'
  },
  { 
    text: 'How can I save more money?', 
    icon: PiggyBank,
    color: 'text-emerald-500'
  },
  { 
    text: 'Analyze my budget', 
    icon: Sparkles,
    color: 'text-amber-500'
  },
  { 
    text: 'Review my financial goals', 
    icon: Target,
    color: 'text-rose-500'
  },
];

export const ChatEmptyState = ({ onSuggestionClick }: ChatEmptyStateProps) => {
  return (
    <div className="flex flex-col items-center justify-center h-full max-w-3xl mx-auto px-4 animate-in fade-in duration-500">
      {/* Greeting Section */}
      <div className="text-center space-y-2 mb-12">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight bg-gradient-to-r from-blue-600 via-indigo-500 to-purple-600 bg-clip-text text-transparent">
          Hello, Yash
        </h1>
        <p className="text-xl text-muted-foreground font-light">
          How can I help you manage your finances today?
        </p>
      </div>

      {/* Suggestions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full">
        {suggestions.map((item) => (
          <button
            key={item.text}
            onClick={() => onSuggestionClick(item.text)}
            className="flex items-center gap-4 p-4 text-left bg-muted/30 hover:bg-muted/60 border border-transparent hover:border-border rounded-xl transition-all duration-200 group"
          >
            <div className={`p-2 rounded-lg bg-background shadow-sm group-hover:shadow-md transition-shadow ${item.color}`}>
              <item.icon className="h-5 w-5" />
            </div>
            <span className="text-sm font-medium text-foreground/80 group-hover:text-foreground">
              {item.text}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
};
