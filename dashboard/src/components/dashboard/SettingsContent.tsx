import { Settings, User, Bell, Shield, Palette, Monitor, Globe } from "lucide-react";
import { cn } from "@/lib/utils";

const SettingsContent = () => {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-foreground flex items-center gap-2">
          <Settings className="w-7 h-7 text-primary" />
          설정
        </h2>
        <p className="text-muted-foreground mt-1">Settings</p>
      </div>

      {/* Settings Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Profile Settings */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-primary/20">
              <User className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">프로필 설정</h3>
              <p className="text-sm text-muted-foreground">계정 정보 관리</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground">이름</label>
              <input
                type="text"
                defaultValue="관리자"
                className="w-full mt-1 px-4 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">이메일</label>
              <input
                type="email"
                defaultValue="admin@bakesight.com"
                className="w-full mt-1 px-4 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">역할</label>
              <input
                type="text"
                defaultValue="매장 관리자"
                disabled
                className="w-full mt-1 px-4 py-2 bg-muted border border-border rounded-lg text-muted-foreground"
              />
            </div>
          </div>
        </div>

        {/* Notification Settings */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-accent/20">
              <Bell className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">알림 설정</h3>
              <p className="text-sm text-muted-foreground">알림 수신 관리</p>
            </div>
          </div>
          <div className="space-y-4">
            {[
              { label: "긴급 알림", description: "낙상, 비정상 행동 등", defaultChecked: true },
              { label: "결제 알림", description: "REVIEW, ERROR 거래", defaultChecked: true },
              { label: "보안 알림", description: "디바이스 상태 변화", defaultChecked: true },
              { label: "일일 리포트", description: "매일 22:00 발송", defaultChecked: false },
            ].map((item, index) => (
              <div key={index} className="flex items-center justify-between py-2">
                <div>
                  <p className="text-foreground font-medium">{item.label}</p>
                  <p className="text-sm text-muted-foreground">{item.description}</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input type="checkbox" defaultChecked={item.defaultChecked} className="sr-only peer" />
                  <div className="w-11 h-6 bg-muted rounded-full peer peer-checked:bg-primary transition-colors after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full" />
                </label>
              </div>
            ))}
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-success/20">
              <Shield className="w-5 h-5 text-success" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">보안 설정</h3>
              <p className="text-sm text-muted-foreground">계정 보안 관리</p>
            </div>
          </div>
          <div className="space-y-4">
            <button className="w-full px-4 py-3 bg-background border border-border rounded-lg text-left hover:bg-muted/50 transition-colors">
              <p className="text-foreground font-medium">비밀번호 변경</p>
              <p className="text-sm text-muted-foreground">마지막 변경: 30일 전</p>
            </button>
            <button className="w-full px-4 py-3 bg-background border border-border rounded-lg text-left hover:bg-muted/50 transition-colors">
              <p className="text-foreground font-medium">2단계 인증</p>
              <p className="text-sm text-muted-foreground">현재: 비활성화</p>
            </button>
            <button className="w-full px-4 py-3 bg-background border border-border rounded-lg text-left hover:bg-muted/50 transition-colors">
              <p className="text-foreground font-medium">로그인 기록</p>
              <p className="text-sm text-muted-foreground">최근 로그인 확인</p>
            </button>
          </div>
        </div>

        {/* Display Settings */}
        <div className="bg-card rounded-2xl p-6 border border-border">
          <div className="flex items-center gap-3 mb-6">
            <div className="p-2 rounded-lg bg-warning/20">
              <Palette className="w-5 h-5 text-warning" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-foreground">디스플레이 설정</h3>
              <p className="text-sm text-muted-foreground">화면 표시 관리</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-muted-foreground">테마</label>
              <div className="flex gap-2 mt-2">
                <button className="flex-1 px-4 py-2 bg-primary text-primary-foreground rounded-lg text-sm font-medium">
                  다크 모드
                </button>
                <button className="flex-1 px-4 py-2 bg-background border border-border text-muted-foreground rounded-lg text-sm font-medium hover:text-foreground transition-colors">
                  라이트 모드
                </button>
              </div>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">언어</label>
              <select className="w-full mt-1 px-4 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50">
                <option value="ko">한국어</option>
                <option value="en">English</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-muted-foreground">시간대</label>
              <select className="w-full mt-1 px-4 py-2 bg-background border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-primary/50">
                <option value="Asia/Seoul">Asia/Seoul (KST)</option>
                <option value="UTC">UTC</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button className="px-6 py-3 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-colors shadow-glow">
          변경사항 저장
        </button>
      </div>
    </div>
  );
};

export default SettingsContent;
