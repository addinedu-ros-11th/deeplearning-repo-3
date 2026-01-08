# 🥐 [Bake Sight] Vision-Based Smart Bakery Operations Platform

**딥러닝 프로젝트 3조 - 비전 기반 스마트 베이커리 운영 및 통합 관리 시스템**

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [폴더 구조](#폴더-구조)
4. [설치 및 실행](#설치-및-실행)
5. [주요 기능](#주요-기능)
6. [API 엔드포인트](#api-엔드포인트)
7. [데이터베이스 스키마](#데이터베이스-스키마)
8. [개발 가이드](#개발-가이드)
9. [배포 가이드 (DEPLOYMENT.md)](#배포-가이드)

---

## 프로젝트 개요

### 기술 스택
* **AI / Vision:** PyTorch, YOLOv8/v11, OpenCV
* **Backend API:** FastAPI + Uvicorn (Cloud Run)
* **Inference Server:** Python (Compute Engine GPU VM)
* **Database:** MySQL or PostgreSQL
* **Cloud:** Google Cloud Platform (GCP)
* **Frontend:** (선택 시 기입: PyQt6, React, etc.)

### 주요 특징
* **캐셔리스 결제:** 탑뷰 카메라 기반 상품 탐지·세분류 및 가격 DB 자동 매칭
* **매장 관제 분석:** CCTV 영상을 통한 인원수, 대기열, 테이블 회전율 실시간 트래킹
* **보안 및 안전:** 미결제 반출 탐지 및 매장 내 이상 행동(넘어짐 등) 감지 이벤트화
* **통합 대시보드:** 매출 통계, 실시간 재고 추정 및 운영 지표 시각화

---

## 시스템 아키텍처

```text
┌────────────────────────┐      ┌───────────────────────────┐
│   Inference Server     │      │       Central API         │
│ (GCP Compute Engine)   │      │    (GCP Cloud Run)        │
│ ┌──────────────────┐   │      │  ┌─────────────────────┐  │
│ │ AI Model (YOLO)  │   │ HTTP │  │ Business Logic      │  │
│ │ CCTV/Tray Stream │◄──┼──────┼─►│ Database Management  │  │
│ └──────────────────┘   │      │  └──────────┬──────────┘  │
└────────────────────────┘      └─────────────┼─────────────┘
                                              ▼
┌────────────────────────┐      ┌───────────────────────────┐
│      Frontend UI       │      │      Cloud Database       │
│  (Admin Dashboard)     │◄─────┤     (SQL Instances)       │
└────────────────────────┘      └───────────────────────────┘
