<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-43-01" src="https://github.com/user-attachments/assets/1e093841-9656-4203-86f1-d52dbed8ffea" /># 🥐 [Bake Sight] Vision-Based Smart Bakery Operations Platform

**딥러닝 프로젝트 3조 - 비전 기반 스마트 베이커리 운영 및 통합 관리 시스템**

## 📋 목차
1. [프로젝트 설명](#프로젝트-개요)
2. [설계](#시스템-아키텍처)
3. [데이터 전처리와 모델 학습](#폴더-구조)
4. [시연](#설치-및-실행)
5. [향후 개선 사항](#주요-기능)
6. [API 엔드포인트](#api-엔드포인트)
7. [데이터베이스 스키마](#데이터베이스-스키마)
8. [개발 가이드](#개발-가이드)
9. [배포 가이드 (DEPLOYMENT.md)](#배포-가이드)

---

## 프로젝트 개요



-  다양하고 많은 빵 종류:
유사한 외형을 가진 다품종 베이커리 메뉴의 특성상, 육안 식별 한계로 인한 계산 실수와 결제 시간 지연이 발생함.

-  피크타임의 처리 지연:
특정 시간대 주문 폭주 시 대면 결제 라인에 병목 현상이 발생하여, 대기 시간 증가 및 매장 회전율 저하를 초래함.

-  실시간 인력 지원 불가:
계산대에 묶인 고정 인력만으로는 매장 내 이동약자 지원이나 이상 상황 발생 시 즉각적이고 유연한 현장 대응이 불가능함.

## 프로젝트 목표




- 트레이 위 상품 자동 탐지/분류:
  딥러닝 객체 탐지 모델을 통해 트레이 위 다중 상품을 실시간으로 정확히 식별하여 계산 대기 없는 무인 결제 시스템 구축.

- 폭행, 이동약자 감지, 넘어짐 등 이벤트 감지:
  CCTV 영상을 분석하여 폭행·낙상 등 안전사고와 이동약자(휠체어 등) 방문을 즉각 포착, 골든타임 내 능동적 인력 투입 지원.

- 통합 대시보드로 운영지표 시각화:
  실시간 매출 현황과 매장 내 이상 징후 알림을 시각화된 대시보드로 제공하여 효율적인 매장 관리 및 신속한 의사결정 지원. 

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-34-53" src="https://github.com/user-attachments/assets/06465ea7-68ea-4f6e-890b-d83eedbdf4db" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-36-22" src="https://github.com/user-attachments/assets/a36b5c57-9596-4291-8c68-f9cf25a6087a" />


<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-36-35" src="https://github.com/user-attachments/assets/a300ca33-c802-41c6-a6f6-cb4925eece38" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-36-43" src="https://github.com/user-attachments/assets/422b6c0b-87c7-4413-8fe3-2b269c89b51d" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-00" src="https://github.com/user-attachments/assets/b26eaa5b-3cdb-43b8-8e93-fb292450ff36" />


<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-06" src="https://github.com/user-attachments/assets/7f5fc40f-2529-4215-bd62-5e9ab95b0eb5" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-12" src="https://github.com/user-attachments/assets/e49c18e2-5fd6-4424-bd46-a381aec4124b" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-23" src="https://github.com/user-attachments/assets/4fbf32f0-e027-47b3-880e-a0da412505b3" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-30" src="https://github.com/user-attachments/assets/78650a8f-b88c-48d2-a433-0bdd8e6bd894" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-38" src="https://github.com/user-attachments/assets/6554aa49-0bbb-4941-922f-12af7d9cb67d" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-46" src="https://github.com/user-attachments/assets/f5be026b-7e9a-429f-b00c-f02d7033128a" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-38-01" src="https://github.com/user-attachments/assets/5d8fd099-b777-4b37-b5c1-1fd59288ebc0" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-38-27" src="https://github.com/user-attachments/assets/45c1b30f-5c29-4ba8-8afb-57980ddce04b" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-38-48" src="https://github.com/user-attachments/assets/fd230aa8-081c-4b05-9a96-cebc3a4f3bca" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-40-24" src="https://github.com/user-attachments/assets/3fd363d1-8b04-47ee-8c1b-19532d182432" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-41-13" src="https://github.com/user-attachments/assets/ee80b5ac-6340-4009-b73f-c0b1ebf2de60" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-41-16" src="https://github.com/user-attachments/assets/c6fd7649-525d-4754-9e28-a7c4812aa88d" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-41-45" src="https://github.com/user-attachments/assets/5a817aae-2b86-4028-bced-6900cfe700c2" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-42-03" src="https://github.com/user-attachments/assets/caa774ef-b5bb-4d42-a247-3e8484644a8f" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-42-09" src="https://github.com/user-attachments/assets/cf49fbef-1617-41ce-b42e-59f3dfe43c0e" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-42-16" src="https://github.com/user-attachments/assets/1948db0b-7250-4101-82d6-118159ca3a5c" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-43-01" src="https://github.com/user-attachments/assets/549b04c9-1d3f-43ff-b271-da027a07dd93" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-43-07" src="https://github.com/user-attachments/assets/00439a55-b3c0-4b2c-b3d6-ee41f186bee6" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-46-31" src="https://github.com/user-attachments/assets/3870f1ba-af77-491b-99fe-d0ae913bf0d7" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-49-57" src="https://github.com/user-attachments/assets/de75eb18-353e-471c-9484-aaa813ffa1e4" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-51-42" src="https://github.com/user-attachments/assets/eafecbd2-8146-4644-b74c-6f3940930eb6" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-51-57" src="https://github.com/user-attachments/assets/020ae66d-6b52-4592-9847-70ee025ad782" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-01" src="https://github.com/user-attachments/assets/a9808fef-ef4f-43f9-9299-2651f8994d10" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-04" src="https://github.com/user-attachments/assets/ac40d521-131d-42b2-a77a-12d3f82e4ffd" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-10" src="https://github.com/user-attachments/assets/647b8392-4d3d-4caa-b801-9111bc252295" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-12" src="https://github.com/user-attachments/assets/cd8b6490-5f2d-47be-9329-49aa198c1325" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-13" src="https://github.com/user-attachments/assets/28fb3caa-5095-4fd9-93df-d420e992e296" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-26" src="https://github.com/user-attachments/assets/f7a8d622-b5e0-464f-ad6e-cd130603c015" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-28" src="https://github.com/user-attachments/assets/6e0d2878-fd03-4b48-bd10-9a1b6224460f" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-30" src="https://github.com/user-attachments/assets/df392d25-ca92-470c-bb46-c1cb1149dcb8" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-36" src="https://github.com/user-attachments/assets/316ae642-fe07-4e12-a1aa-75c77678e63f" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-43" src="https://github.com/user-attachments/assets/09386074-0e5c-4f97-80de-8f862bddd1d3" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-44" src="https://github.com/user-attachments/assets/790de5b7-989b-41e9-ad3b-288a14a4f508" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-46" src="https://github.com/user-attachments/assets/4d338294-2a3e-4f79-8dd0-9a6cfae6ac46" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-54" src="https://github.com/user-attachments/assets/372156c6-12a4-47b8-b005-8e5f80bec7eb" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-55" src="https://github.com/user-attachments/assets/b0ea052d-3805-4907-b402-9ae394b6263d" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-57" src="https://github.com/user-attachments/assets/833645d2-b2ce-422b-99c5-11fe63972454" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-09" src="https://github.com/user-attachments/assets/4e14a0fe-f47e-41af-99e9-0607b52ceeb7" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-12" src="https://github.com/user-attachments/assets/d496f3fd-0645-4394-b29d-0ac573c24e42" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-13" src="https://github.com/user-attachments/assets/275ec30d-518d-4178-9f7d-fd5a056a309f" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-15" src="https://github.com/user-attachments/assets/64193f6f-f07d-4dc7-a533-0c92590e8168" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-16" src="https://github.com/user-attachments/assets/adf947f8-35c0-40ec-af37-f2f8f3d0694f" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-17" src="https://github.com/user-attachments/assets/dbf2731b-a6ba-4ead-8784-7e15fad1418c" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-17-1" src="https://github.com/user-attachments/assets/cd56c80a-7343-4b3c-9615-92aa5dd0681d" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-18" src="https://github.com/user-attachments/assets/526729a4-9faf-40d2-8469-d822ce0c0d1d" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-39" src="https://github.com/user-attachments/assets/d49bc835-0e07-4423-a7c5-9918ceee5bac" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-43" src="https://github.com/user-attachments/assets/0593e5c1-ea3d-4a8c-af46-f7ae66434470" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-45" src="https://github.com/user-attachments/assets/b84a35cd-dc72-45d6-bfed-e93bc167e39a" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-49" src="https://github.com/user-attachments/assets/301cc69d-3f85-4223-bc2d-2e8a49e18046" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-50" src="https://github.com/user-attachments/assets/eb6a9506-dde1-4483-bf1d-c52218673b60" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-51" src="https://github.com/user-attachments/assets/95f955ef-acf1-4479-84ea-0a314fcc0282" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-52" src="https://github.com/user-attachments/assets/ec2fad35-4d4a-4300-a997-66aa4a74e90f" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-54" src="https://github.com/user-attachments/assets/f0f01eba-c9a0-4bc6-9327-11c71053be3c" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-55" src="https://github.com/user-attachments/assets/7114258f-7aa1-48c7-ab75-61d50226b74e" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-58" src="https://github.com/user-attachments/assets/c68ec49f-c595-4d4a-9dd4-f36f870650d6" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-59" src="https://github.com/user-attachments/assets/4dba86b0-247d-4981-974e-b771bf46a5ca" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-01" src="https://github.com/user-attachments/assets/6195575e-b1f7-4d1c-a23d-af627e5bb10b" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-18" src="https://github.com/user-attachments/assets/8cfb0b63-9a8d-4fd8-8601-97b5af6efc12" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-05" src="https://github.com/user-attachments/assets/41d2c85a-4cc0-4cd6-bafd-d28196fd3f15" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-09" src="https://github.com/user-attachments/assets/f8cfcd1e-267c-4720-ae3e-74a7715ae355" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-10" src="https://github.com/user-attachments/assets/cb092f1e-41e6-42ff-9abe-49d53a44938e" />







<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-18" src="https://github.com/user-attachments/assets/023a8e7b-c4c5-46f6-8e90-f93284f5f2ba" />


<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-41" src="https://github.com/user-attachments/assets/7e9a9563-ce2c-4486-ba9f-674885a6e17a" />











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
