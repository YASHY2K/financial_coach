import { Link, Outlet, useLocation } from 'react-router-dom';
import { LayoutDashboard, MessageSquare, Settings, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DashboardLayout() {
  const location = useLocation();

  const navItems = [
    { href: '/', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/chat', label: 'Financial Coach', icon: MessageSquare },
  ];

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r bg-muted/20 hidden md:flex flex-col">
        <div className="h-14 flex items-center px-6 border-b">
          <div className="flex items-center gap-2 font-bold text-lg text-primary">
            <div className="size-6 rounded-full bg-primary" />
            FinCoach
          </div>
        </div>
        
        <div className="flex-1 py-6 px-4 space-y-1">
          {navItems.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link key={item.href} to={item.href}>
                <Button
                  variant={isActive ? "secondary" : "ghost"}
                  className={`w-full justify-start gap-3 ${isActive ? 'bg-primary/10 text-primary hover:bg-primary/20' : 'text-muted-foreground'}`}
                >
                  <item.icon className="size-4" />
                  {item.label}
                </Button>
              </Link>
            );
          })}
        </div>

        <div className="p-4 border-t space-y-2">
            <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground">
                <Settings className="size-4" />
                Settings
            </Button>
            <Button variant="ghost" className="w-full justify-start gap-3 text-muted-foreground hover:text-destructive hover:bg-destructive/10">
                <LogOut className="size-4" />
                Log Out
            </Button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Mobile Header (TODO) */}
        <header className="md:hidden h-14 flex items-center px-4 border-b bg-background">
             <div className="font-bold">FinCoach</div>
        </header>

        <div className="flex-1 overflow-auto bg-background">
          <Outlet />
        </div>
      </main>
    </div>
  );
}