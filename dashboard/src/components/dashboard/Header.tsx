import { Bell, User, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

const Header = () => {
  const currentDate = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "long",
  });

  const currentTime = new Date().toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <header className="h-16 border-b border-border bg-card/50 backdrop-blur-sm px-6 flex items-center justify-between">
      {/* Left Section */}
      <div className="flex items-center gap-4">
        <div>
          <h2 className="text-xl font-bold text-foreground">Dashboard</h2>
          <p className="text-sm text-muted-foreground">실시간 매장 현황</p>
        </div>
      </div>

      {/* Center Section - Date/Time */}
      <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-muted/30 border border-border">
        <Calendar className="w-4 h-4 text-primary" />
        <span className="text-sm text-muted-foreground">{currentDate}</span>
        <span className="text-sm font-medium text-foreground">{currentTime}</span>
      </div>

      {/* Right Section */}
      <div className="flex items-center gap-4">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative hover:bg-muted">
          <Bell className="w-5 h-5 text-muted-foreground" />
          <Badge className="absolute -top-1 -right-1 w-5 h-5 flex items-center justify-center p-0 bg-destructive text-destructive-foreground text-xs">
            3
          </Badge>
        </Button>

        {/* User Profile */}
        <div className="flex items-center gap-3 px-3 py-2 rounded-xl bg-muted/30 border border-border hover:bg-muted/50 cursor-pointer transition-colors">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
            <User className="w-4 h-4 text-primary-foreground" />
          </div>
          <div className="hidden md:block">
            <p className="text-sm font-medium text-foreground">관리자</p>
            <p className="text-xs text-muted-foreground">Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
