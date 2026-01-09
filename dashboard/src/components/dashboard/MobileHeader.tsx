import { Bell, Menu } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { useState } from "react";

interface MobileHeaderProps {
  onMenuClick?: () => void;
}

const MobileHeader = ({ onMenuClick }: MobileHeaderProps) => {
  const [isOpen, setIsOpen] = useState(false);
  
  const currentTime = new Date().toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <header className="sticky top-0 z-40 bg-background/95 backdrop-blur-lg border-b border-border safe-area-top">
      <div className="flex items-center justify-between h-14 px-4">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center shadow-glow">
            <span className="text-base">🍞</span>
          </div>
          <div>
            <h1 className="text-base font-bold text-foreground leading-tight">Bake Sight</h1>
            <p className="text-[10px] text-muted-foreground">by 빵끗</p>
          </div>
        </div>

        {/* Time & Actions */}
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground hidden sm:block">{currentTime}</span>
          
          {/* Notifications */}
          <Button variant="ghost" size="icon" className="relative h-9 w-9">
            <Bell className="w-4 h-4 text-muted-foreground" />
            <Badge className="absolute -top-0.5 -right-0.5 w-4 h-4 flex items-center justify-center p-0 bg-destructive text-destructive-foreground text-[9px]">
              3
            </Badge>
          </Button>

          {/* Menu Sheet */}
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="h-9 w-9">
                <Menu className="w-4 h-4 text-muted-foreground" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[280px] bg-card border-border">
              <SheetHeader>
                <SheetTitle className="text-foreground">설정</SheetTitle>
              </SheetHeader>
              <div className="mt-6 space-y-4">
                <div className="p-4 rounded-xl bg-muted/30 border border-border">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                      <span className="text-lg">👤</span>
                    </div>
                    <div>
                      <p className="font-medium text-foreground">관리자</p>
                      <p className="text-xs text-muted-foreground">admin@bakesight.com</p>
                    </div>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <button className="w-full p-3 rounded-xl text-left text-sm text-foreground hover:bg-muted/50 transition-colors">
                    ⚙️ 매장 설정
                  </button>
                  <button className="w-full p-3 rounded-xl text-left text-sm text-foreground hover:bg-muted/50 transition-colors">
                    📊 리포트 생성
                  </button>
                  <button className="w-full p-3 rounded-xl text-left text-sm text-foreground hover:bg-muted/50 transition-colors">
                    🔔 알림 설정
                  </button>
                  <button className="w-full p-3 rounded-xl text-left text-sm text-foreground hover:bg-muted/50 transition-colors">
                    ❓ 도움말
                  </button>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
};

export default MobileHeader;
