import useEmblaCarousel from "embla-carousel-react";
import { useCallback, useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import KPICard from "./KPICard";

interface KPIData {
  icon: string;
  title: string;
  value: string;
  subtitle: string;
  trend: "up" | "down" | "neutral";
  variant: "revenue" | "customers" | "occupancy" | "alerts";
}

const kpiData: KPIData[] = [
  {
    icon: "📈",
    title: "Real-time Revenue",
    value: "₩2,450,000",
    subtitle: "↑ +12.5% 어제 대비",
    trend: "up",
    variant: "revenue",
  },
  {
    icon: "👥",
    title: "Current Customers",
    value: "28명",
    subtitle: "8/10 테이블 사용중",
    trend: "neutral",
    variant: "customers",
  },
  {
    icon: "🪑",
    title: "Table Occupancy",
    value: "80%",
    subtitle: "8개 테이블 점유",
    trend: "up",
    variant: "occupancy",
  },
  {
    icon: "🚨",
    title: "Pending Alerts",
    value: "3건",
    subtitle: "1건 긴급",
    trend: "down",
    variant: "alerts",
  },
];

const SwipeableKPICards = () => {
  const [emblaRef, emblaApi] = useEmblaCarousel({
    align: "start",
    containScroll: "trimSnaps",
    dragFree: true,
  });
  const [selectedIndex, setSelectedIndex] = useState(0);

  const onSelect = useCallback(() => {
    if (!emblaApi) return;
    setSelectedIndex(emblaApi.selectedScrollSnap());
  }, [emblaApi]);

  useEffect(() => {
    if (!emblaApi) return;
    emblaApi.on("select", onSelect);
    onSelect();
  }, [emblaApi, onSelect]);

  return (
    <div className="w-full">
      <div className="overflow-hidden" ref={emblaRef}>
        <div className="flex gap-3 touch-pan-y">
          {kpiData.map((kpi, index) => (
            <div
              key={kpi.variant}
              className="flex-none w-[75%] min-w-0 first:ml-4 last:mr-4 sm:w-[45%] md:w-[30%]"
            >
              <KPICard
                icon={kpi.icon}
                title={kpi.title}
                value={kpi.value}
                subtitle={kpi.subtitle}
                trend={kpi.trend}
                variant={kpi.variant}
                delay={index * 100}
              />
            </div>
          ))}
        </div>
      </div>
      
      {/* Dot Indicators */}
      <div className="flex justify-center gap-2 mt-4 md:hidden">
        {kpiData.map((_, index) => (
          <button
            key={index}
            onClick={() => emblaApi?.scrollTo(index)}
            className={cn(
              "w-2 h-2 rounded-full transition-all duration-200",
              selectedIndex === index 
                ? "bg-primary w-4" 
                : "bg-muted-foreground/30"
            )}
          />
        ))}
      </div>
    </div>
  );
};

export default SwipeableKPICards;
