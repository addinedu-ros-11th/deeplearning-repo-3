import { 
  Home, 
  CreditCard, 
  Store, 
  BarChart3, 
  Bell
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  icon: React.ElementType;
  label: string;
  id: string;
}

const navItems: NavItem[] = [
  { icon: Home, label: "홈", id: "dashboard" },
  { icon: CreditCard, label: "결제", id: "payment" },
  { icon: Store, label: "매장", id: "store" },
  { icon: BarChart3, label: "분석", id: "analytics" },
  { icon: Bell, label: "알림", id: "alerts" },
];

interface BottomNavigationProps {
  activeTab: string;
  onTabChange: (id: string) => void;
}

const BottomNavigation = ({ activeTab, onTabChange }: BottomNavigationProps) => {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-card/95 backdrop-blur-lg border-t border-border safe-area-bottom">
      <div className="flex items-center justify-around h-16 px-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              className={cn(
                "flex flex-col items-center justify-center gap-1 py-2 px-4 rounded-xl transition-all duration-200 min-w-[64px]",
                "active:scale-95 touch-manipulation",
                isActive 
                  ? "text-primary" 
                  : "text-muted-foreground"
              )}
            >
              <div className={cn(
                "relative p-1.5 rounded-xl transition-all duration-200",
                isActive && "bg-primary/20"
              )}>
                <Icon className={cn(
                  "w-5 h-5 transition-transform",
                  isActive && "scale-110"
                )} />
                {item.id === "alerts" && (
                  <span className="absolute -top-1 -right-1 w-4 h-4 bg-destructive text-destructive-foreground text-[10px] font-bold rounded-full flex items-center justify-center">
                    3
                  </span>
                )}
              </div>
              <span className={cn(
                "text-[10px] font-medium transition-colors",
                isActive ? "text-primary" : "text-muted-foreground"
              )}>
                {item.label}
              </span>
              {isActive && (
                <div className="absolute bottom-1 w-1 h-1 bg-primary rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNavigation;
