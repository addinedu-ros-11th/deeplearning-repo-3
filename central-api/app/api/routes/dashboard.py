from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_admin_key
from app.db.models import Store, OrderHdr, TraySession, Review, OrderStatus
from app.schemas.dashboard import (
    TopMenuRow, KPIRow, HourlyRevenueRow,
    WeeklyDataRow, HourlyCustomersRow, CategoryDataRow, AnalyticsStatRow
)

router = APIRouter(dependencies=[Depends(require_admin_key)])

@router.get("/dashboards/top-menu", response_model=list[TopMenuRow])
def top_menu(
    store_code: str,
    from_: datetime,
    to: datetime,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    sql = text("""
        SELECT
          ol.item_id AS item_id,
          mi.name_kor AS name,
          SUM(ol.qty) AS qty,
          SUM(ol.line_amount_won) AS amount_won
        FROM order_hdr oh
        JOIN order_line ol ON ol.order_id = oh.order_id
        JOIN menu_item mi ON mi.item_id = ol.item_id
        WHERE oh.store_id = :store_id
          AND oh.status = 'PAID'
          AND oh.created_at >= :from_
          AND oh.created_at < :to_
        GROUP BY ol.item_id, mi.name_kor
        ORDER BY qty DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"store_id": store.store_id, "from_": from_, "to_": to, "limit": limit}).mappings().all()
    return [TopMenuRow(**dict(r)) for r in rows]


@router.get("/dashboards/kpis", response_model=list[KPIRow])
def get_kpis(
    store_code: str,
    db: Session = Depends(get_db),
):
    """오늘의 KPI 데이터 조회"""
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    # 오늘 날짜 범위
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    # 1. 오늘 매출
    today_revenue = db.query(func.coalesce(func.sum(OrderHdr.total_amount_won), 0)).filter(
        OrderHdr.store_id == store.store_id,
        OrderHdr.status == "PAID",
        OrderHdr.created_at >= today,
        OrderHdr.created_at < tomorrow,
    ).scalar()

    # 어제 매출 (비교용)
    yesterday_revenue = db.query(func.coalesce(func.sum(OrderHdr.total_amount_won), 0)).filter(
        OrderHdr.store_id == store.store_id,
        OrderHdr.status == "PAID",
        OrderHdr.created_at >= yesterday,
        OrderHdr.created_at < today,
    ).scalar()

    revenue_trend = "up" if today_revenue > yesterday_revenue else ("down" if today_revenue < yesterday_revenue else "neutral")
    revenue_diff = today_revenue - yesterday_revenue
    revenue_diff_str = f"+{revenue_diff:,}원" if revenue_diff >= 0 else f"{revenue_diff:,}원"

    # 2. 오늘 고객 수 (세션 수)
    today_customers = db.query(func.count(TraySession.session_id)).filter(
        TraySession.store_id == store.store_id,
        TraySession.created_at >= today,
        TraySession.created_at < tomorrow,
    ).scalar()

    yesterday_customers = db.query(func.count(TraySession.session_id)).filter(
        TraySession.store_id == store.store_id,
        TraySession.created_at >= yesterday,
        TraySession.created_at < today,
    ).scalar()

    customers_trend = "up" if today_customers > yesterday_customers else ("down" if today_customers < yesterday_customers else "neutral")
    customers_diff = today_customers - yesterday_customers
    customers_diff_str = f"+{customers_diff}명" if customers_diff >= 0 else f"{customers_diff}명"

    # 3. 현재 테이블 점유율 (활성 세션 / 전체 테이블 수)
    active_sessions = db.query(func.count(TraySession.session_id)).filter(
        TraySession.store_id == store.store_id,
        TraySession.status == "ACTIVE",
    ).scalar()

    # 테이블 수는 하드코딩 (실제로는 store 설정에서 가져와야 함)
    total_tables = 20
    occupancy_rate = round((active_sessions / total_tables) * 100) if total_tables > 0 else 0

    # 4. 오늘 리뷰 필요 건수
    open_reviews = db.query(func.count(Review.review_id)).filter(
        Review.status == "OPEN",
    ).scalar()

    return [
        KPIRow(
            icon="revenue",
            title="오늘 매출",
            value=f"₩{today_revenue:,}",
            subtitle=f"전일 대비 {revenue_diff_str}",
            trend=revenue_trend,
            variant="revenue",
        ),
        KPIRow(
            icon="customers",
            title="오늘 고객",
            value=f"{today_customers}명",
            subtitle=f"전일 대비 {customers_diff_str}",
            trend=customers_trend,
            variant="customers",
        ),
        KPIRow(
            icon="occupancy",
            title="테이블 점유율",
            value=f"{occupancy_rate}%",
            subtitle=f"{active_sessions}/{total_tables} 테이블 사용중",
            trend="neutral",
            variant="occupancy",
        ),
        KPIRow(
            icon="alerts",
            title="검토 필요",
            value=f"{open_reviews}건",
            subtitle="미처리 리뷰",
            trend="up" if open_reviews > 0 else "neutral",
            variant="alerts",
        ),
    ]


@router.get("/dashboards/hourly-revenue", response_model=list[HourlyRevenueRow])
def get_hourly_revenue(
    store_code: str,
    db: Session = Depends(get_db),
):
    """오늘의 시간대별 매출 조회"""
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    # 오늘 날짜 범위
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    # 시간대별 매출 집계
    sql = text("""
        SELECT
          HOUR(created_at) AS hour,
          COALESCE(SUM(total_amount_won), 0) AS revenue
        FROM order_hdr
        WHERE store_id = :store_id
          AND status = 'PAID'
          AND created_at >= :today
          AND created_at < :tomorrow
        GROUP BY HOUR(created_at)
        ORDER BY hour
    """)

    rows = db.execute(sql, {
        "store_id": store.store_id,
        "today": today,
        "tomorrow": tomorrow,
    }).mappings().all()

    # 시간대별 매출 맵 생성
    hourly_map = {row["hour"]: int(row["revenue"]) for row in rows}

    # 전체 시간대 (0-23시) 반환
    result = []
    for hour in range(24):
        time_str = f"{hour:02d}:00"
        revenue = hourly_map.get(hour, 0)
        result.append(HourlyRevenueRow(time=time_str, revenue=revenue))

    return result


# ============================================
# Analytics API
# ============================================

@router.get("/dashboards/analytics/weekly", response_model=list[WeeklyDataRow])
def get_weekly_data(
    store_code: str,
    db: Session = Depends(get_db),
):
    """최근 7일간 일별 매출 및 고객 수 조회"""
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    # 이번 주 일요일부터 토요일까지 (달력 순서)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # 이번 주 일요일 찾기 (isoweekday: 1=월, 7=일)
    days_since_sunday = today.isoweekday() % 7  # 일요일=0, 월요일=1, ..., 토요일=6
    week_start = today - timedelta(days=days_since_sunday)  # 이번 주 일요일

    days = ["일", "월", "화", "수", "목", "금", "토"]
    result = []

    for i in range(7):  # 일요일부터 토요일까지
        day_start = week_start + timedelta(days=i)
        day_end = day_start + timedelta(days=1)

        # 매출 조회
        revenue = db.query(func.coalesce(func.sum(OrderHdr.total_amount_won), 0)).filter(
            OrderHdr.store_id == store.store_id,
            OrderHdr.status == OrderStatus.PAID,
            OrderHdr.created_at >= day_start,
            OrderHdr.created_at < day_end,
        ).scalar()

        # 고객 수 조회
        customers = db.query(func.count(TraySession.session_id)).filter(
            TraySession.store_id == store.store_id,
            TraySession.created_at >= day_start,
            TraySession.created_at < day_end,
        ).scalar()

        result.append(WeeklyDataRow(
            day=days[i],
            revenue=int(revenue),
            customers=int(customers),
        ))

    return result


@router.get("/dashboards/analytics/hourly-customers", response_model=list[HourlyCustomersRow])
def get_hourly_customers(
    store_code: str,
    db: Session = Depends(get_db),
):
    """오늘의 시간대별 고객 수 조회"""
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    # 오늘 날짜 범위
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    # ORM으로 오늘의 모든 세션 가져오기
    sessions = db.query(TraySession).filter(
        TraySession.store_id == store.store_id,
        TraySession.created_at >= today,
        TraySession.created_at < tomorrow,
    ).all()

    # Python에서 시간대별로 그룹화
    hourly_map = {}
    print(f"\n=== HOURLY DEBUG ===")
    for session in sessions:
        hour = session.created_at.hour
        print(f"Session {session.session_id}: created_at={session.created_at}, hour={hour}")
        hourly_map[hour] = hourly_map.get(hour, 0) + 1
    print(f"Hourly map: {hourly_map}")
    print(f"=== END DEBUG ===\n")

    # 전체 시간대 (0-23시) 반환
    result = []
    for hour in range(24):
        result.append(HourlyCustomersRow(
            hour=f"{hour:02d}",
            customers=hourly_map.get(hour, 0),
        ))

    return result


@router.get("/dashboards/analytics/categories", response_model=list[CategoryDataRow])
def get_category_data(
    store_code: str,
    db: Session = Depends(get_db),
):
    """카테고리별 판매 비율 조회 (최근 7일)"""
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)

    # 카테고리별 판매량 집계
    sql = text("""
        SELECT
          COALESCE(ci.name, '기타') AS category,
          SUM(ol.qty) AS total_qty
        FROM order_hdr oh
        JOIN order_line ol ON ol.order_id = oh.order_id
        JOIN menu_item mi ON mi.item_id = ol.item_id
        JOIN category ci ON ci.category_id = mi.category_id
        WHERE oh.store_id = :store_id
          AND oh.status = 'PAID'
          AND oh.created_at >= :week_ago
          AND oh.created_at < :today
        GROUP BY mi.category_id
        ORDER BY total_qty DESC
    """)

    rows = db.execute(sql, {
        "store_id": store.store_id,
        "week_ago": week_ago,
        "today": today + timedelta(days=1),
    }).mappings().all()

    # 전체 수량
    total = sum(row["total_qty"] for row in rows) if rows else 0

    # 색상 팔레트
    colors = [
        "hsl(var(--primary))",
        "hsl(var(--accent))",
        "hsl(var(--secondary))",
        "hsl(var(--warning))",
        "hsl(var(--muted-foreground))",
    ]

    result = []
    for i, row in enumerate(rows[:5]):  # 최대 5개 카테고리
        percentage = round((row["total_qty"] / total) * 100) if total > 0 else 0
        result.append(CategoryDataRow(
            name=row["category"],
            value=percentage,
            color=colors[i % len(colors)],
        ))

    return result


@router.get("/dashboards/analytics/stats", response_model=list[AnalyticsStatRow])
def get_analytics_stats(
    store_code: str,
    db: Session = Depends(get_db),
):
    """주간 분석 통계 조회"""
    store = db.query(Store).filter(Store.store_code == store_code).first()
    if not store:
        raise HTTPException(status_code=404, detail="store not found")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    this_week_start = today - timedelta(days=today.weekday())
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end = this_week_start

    # 이번 주 매출
    this_week_revenue = db.query(func.coalesce(func.sum(OrderHdr.total_amount_won), 0)).filter(
        OrderHdr.store_id == store.store_id,
        OrderHdr.status == "PAID",
        OrderHdr.created_at >= this_week_start,
        OrderHdr.created_at < today + timedelta(days=1),
    ).scalar()

    # 지난 주 매출
    last_week_revenue = db.query(func.coalesce(func.sum(OrderHdr.total_amount_won), 0)).filter(
        OrderHdr.store_id == store.store_id,
        OrderHdr.status == "PAID",
        OrderHdr.created_at >= last_week_start,
        OrderHdr.created_at < last_week_end,
    ).scalar()

    revenue_change = ((this_week_revenue - last_week_revenue) / last_week_revenue * 100) if last_week_revenue > 0 else 0

    # 이번 주 방문객
    this_week_customers = db.query(func.count(TraySession.session_id)).filter(
        TraySession.store_id == store.store_id,
        TraySession.created_at >= this_week_start,
        TraySession.created_at < today + timedelta(days=1),
    ).scalar()

    # 지난 주 방문객
    last_week_customers = db.query(func.count(TraySession.session_id)).filter(
        TraySession.store_id == store.store_id,
        TraySession.created_at >= last_week_start,
        TraySession.created_at < last_week_end,
    ).scalar()

    customers_change = ((this_week_customers - last_week_customers) / last_week_customers * 100) if last_week_customers > 0 else 0

    # 평균 객단가
    avg_order_this_week = this_week_revenue / this_week_customers if this_week_customers > 0 else 0
    avg_order_last_week = last_week_revenue / last_week_customers if last_week_customers > 0 else 0
    avg_order_change = ((avg_order_this_week - avg_order_last_week) / avg_order_last_week * 100) if avg_order_last_week > 0 else 0

    # 평균 체류시간 (분)
    avg_stay_sql = text("""
        SELECT AVG(TIMESTAMPDIFF(MINUTE, started_at, ended_at)) AS avg_minutes
        FROM tray_session
        WHERE store_id = :store_id
          AND status = 'ENDED'
          AND ended_at IS NOT NULL
          AND created_at >= :week_start
          AND created_at < :today
    """)

    this_week_stay = db.execute(avg_stay_sql, {
        "store_id": store.store_id,
        "week_start": this_week_start,
        "today": today + timedelta(days=1),
    }).scalar() or 0

    last_week_stay = db.execute(avg_stay_sql, {
        "store_id": store.store_id,
        "week_start": last_week_start,
        "today": last_week_end,
    }).scalar() or 0

    stay_change = ((this_week_stay - last_week_stay) / last_week_stay * 100) if last_week_stay > 0 else 0

    return [
        AnalyticsStatRow(
            label="주간 총 매출",
            value=f"₩{int(this_week_revenue):,}",
            change=f"{revenue_change:+.1f}%",
            trend="up" if revenue_change >= 0 else "down",
            iconType="trending",
        ),
        AnalyticsStatRow(
            label="주간 방문객",
            value=f"{this_week_customers:,}명",
            change=f"{customers_change:+.1f}%",
            trend="up" if customers_change >= 0 else "down",
            iconType="users",
        ),
        AnalyticsStatRow(
            label="평균 객단가",
            value=f"₩{int(avg_order_this_week):,}",
            change=f"{avg_order_change:+.1f}%",
            trend="up" if avg_order_change >= 0 else "down",
            iconType="shopping",
        ),
        AnalyticsStatRow(
            label="평균 체류시간",
            value=f"{int(this_week_stay)}분",
            change=f"{stay_change:+.1f}%",
            trend="up" if stay_change >= 0 else "down",
            iconType="clock",
        ),
    ]
