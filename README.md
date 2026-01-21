># 🥐 [Bake Sight] 
**Vision-Based Smart Bakery Operations Platform**

**딥러닝 프로젝트 3조 - 비전 기반 스마트 베이커리 운영 및 통합 관리 시스템**

## 📋 목차
1. [주제 선정](#01.주제-선정)
2. [프로젝트 설계](#02.프로젝트-설계)
3. [기술 시연 및 소개](#03.기술-시연-및-소개)
4. [빵 스캐너 주요 기술](#04.빵-스캐너-주요-기술)
5. [Trouble Shooting](#05.Trouble-Shooting)




더 자세한 내용은 ppt에서 보실수 있습니다..click ->>[**🥐🥐🥐** ](https://www.canva.com/design/DAG8-Zmcdlo/UDOH503owk026jmjTULwXA/view?utm_content=DAG8-Zmcdlo&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h0223e34169)

---

## 01.주제 선정

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-34-53" src="https://github.com/user-attachments/assets/06465ea7-68ea-4f6e-890b-d83eedbdf4db" />


‘**빵지순례**’라는 말이 생길 정도로

사람들은 일상 속에서 맛있는 음식을 찾아다니는 문화에 익숙해졌습니다.

하지만 방문객 수에 비해 매장 규모와 **인력**이 **부족**한 경우가 많아,

**피크타임**에는 1~2시간 이상 대기하며 주문하는 장면도 흔히 볼 수 있습니다.
<img width="1920" height="1080" alt="Screenshot from 2026-01-20 09-37-38" src="https://github.com/user-attachments/assets/ac4a1f37-f7b4-48cd-b90a-c9d9f5000c6f" />



이러한 **대기 시간**은

고객에게는 **불편함**을,

업주에게는 **매출 손실**로 이어질 수 있습니다.
<img width="1920" height="1080" alt="Screenshot from 2026-01-20 09-37-52" src="https://github.com/user-attachments/assets/250c7823-8dba-4c0f-8547-e9a147e770fc" />


계산 대기 줄을 줄이기 위해 인력을 추가로 채용하려 해도,

대형 베이커리의 경우 빵 종류가 **많아**

직원 교육에 **많은 시간**과 **비용**이 필요합니다.

또한 무작정 인원을 늘리는 것 역시 현실적인 해결책이 아닙니다.

더불어 계산 업무에 인력이 집중되면서 매장 내 **도난, 혼잡, 고객 안전** 등과 같은 이상 상황에 즉각 대응할 수 있는 인원이 부족해지는 문제도 함께 발생하고 있습니다.

<img width="1920" height="1080" alt="Screenshot from 2026-01-20 09-37-58" src="https://github.com/user-attachments/assets/dd2e1c7f-eb1a-4628-a614-ee95ae017f39" />


이에 저희는 **비전 기술**을 활용한 **빵 스캐너**를 제안합니다.

이 시스템은 진열된 빵을 **자동**으로 **탐지**하고 **분류**하여 계산 과정을 단순화하고

또한 CCTV 기반으로 매장 상황을 실시간 모니터링하여

이상 행동을 사전에 감지할 수 있도록 설계되었습니다.

<img width="1920" height="1080" alt="Screenshot from 2026-01-20 17-15-33" src="https://github.com/user-attachments/assets/dd94eb1b-885c-4bb6-8eda-570984dc8688" />


이를 통해 대기 시간을 줄이고,

**매장 운영 효율**과 **고객 만족도**를 동시에 **향상**시키고자 합니다.

## 02.프로젝트 설계
### 고객 요구 기능
<img width="1165" height="489" alt="Screenshot from 2026-01-20 17-18-00" src="https://github.com/user-attachments/assets/26c54fec-a16f-4ee1-b208-90ba34904c64" />

### 빵스캐너 요구기능
<img width="1165" height="403" alt="Screenshot from 2026-01-20 17-18-35" src="https://github.com/user-attachments/assets/0de1d68f-c242-43ca-9a20-0c6b2e13f288" />

### CCTV 요구기능
<img width="1165" height="403" alt="Screenshot from 2026-01-20 17-18-40" src="https://github.com/user-attachments/assets/51c190d1-15dc-4a5e-a24c-eae9e5a2daf5" />

### 대시보드 요구기능
<img width="1165" height="403" alt="Screenshot from 2026-01-20 17-18-42" src="https://github.com/user-attachments/assets/99ed2b61-7ba5-45a4-8427-07f4d20067e5" />



## 03.기술 시연 및 소개
### 테스트 환경
<img width="1154" height="490" alt="Screenshot from 2026-01-20 17-22-06" src="https://github.com/user-attachments/assets/064b1c10-ec8c-4a0f-909a-af28b777b33a" />

### 빵 결제 시연 

![정상결제시연](https://github.com/user-attachments/assets/d0b1dd1b-42e8-4a79-92ab-7e29f29c637d)


### 빵 스캔 플로우 차트
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-30" src="https://github.com/user-attachments/assets/78650a8f-b88c-48d2-a433-0bdd8e6bd894" />

### CCTV 감지 시연 

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-38" src="https://github.com/user-attachments/assets/6554aa49-0bbb-4941-922f-12af7d9cb67d" />

## 넘어짐 감지 모델

![넘어짐감지](https://github.com/user-attachments/assets/9406f0bf-4e06-4f3d-ab89-cb775ef3ffd2)

## 폭행 감지 모델

![폭행시연](https://github.com/user-attachments/assets/b19198f4-a58e-44eb-b72f-cab206852695)
  


## 이동약자 감지 모델 

![202601211308-ezgif com-video-to-gif-converter (1)](https://github.com/user-attachments/assets/ac23a2cb-0c0e-46c0-9fbf-ac9f0b20af48)



## 04.빵 스캐너 주요 기술
## 05.Trouble Shooting














개발환경 (사용 기술 스택)
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-46" src="https://github.com/user-attachments/assets/f5be026b-7e9a-429f-b00c-f02d7033128a" />
Hardware Architecture
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-38-01" src="https://github.com/user-attachments/assets/5d8fd099-b777-4b37-b5c1-1fd59288ebc0" />
ERD
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-38-27" src="https://github.com/user-attachments/assets/45c1b30f-5c29-4ba8-8afb-57980ddce04b" />

빵 분류방식 
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-41-13" src="https://github.com/user-attachments/assets/ee80b5ac-6340-4009-b73f-c0b1ebf2de60" />
빵 분류방식 2
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-41-16" src="https://github.com/user-attachments/assets/c6fd7649-525d-4754-9e28-a7c4812aa88d" />
빵 분류방식 3
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-41-45" src="https://github.com/user-attachments/assets/5a817aae-2b86-4028-bced-6900cfe700c2" />




빵스 개선사항
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-43-07" src="https://github.com/user-attachments/assets/00439a55-b3c0-4b2c-b3d6-ee41f186bee6" />


전체 화면 구성 대시보드 
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-43" src="https://github.com/user-attachments/assets/09386074-0e5c-4f97-80de-8f862bddd1d3" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-44" src="https://github.com/user-attachments/assets/790de5b7-989b-41e9-ad3b-288a14a4f508" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-46" src="https://github.com/user-attachments/assets/4d338294-2a3e-4f79-8dd0-9a6cfae6ac46" />
빵 데이터 감지 모델 
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-54" src="https://github.com/user-attachments/assets/372156c6-12a4-47b8-b005-8e5f80bec7eb" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-55" src="https://github.com/user-attachments/assets/b0ea052d-3805-4907-b402-9ae394b6263d" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-52-57" src="https://github.com/user-attachments/assets/833645d2-b2ce-422b-99c5-11fe63972454" />
cvat 라벨링 협업툴 
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-09" src="https://github.com/user-attachments/assets/4e14a0fe-f47e-41af-99e9-0607b52ceeb7" />
빵스 주요기술 


<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-39" src="https://github.com/user-attachments/assets/d49bc835-0e07-4423-a7c5-9918ceee5bac" />
트러블 슈팅 

빵분류
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-45" src="https://github.com/user-attachments/assets/b84a35cd-dc72-45d6-bfed-e93bc167e39a" />
넘어짐
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-49" src="https://github.com/user-attachments/assets/301cc69d-3f85-4223-bc2d-2e8a49e18046" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-50" src="https://github.com/user-attachments/assets/eb6a9506-dde1-4483-bf1d-c52218673b60" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-51" src="https://github.com/user-attachments/assets/95f955ef-acf1-4479-84ea-0a314fcc0282" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-52" src="https://github.com/user-attachments/assets/ec2fad35-4d4a-4300-a997-66aa4a74e90f" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-54" src="https://github.com/user-attachments/assets/f0f01eba-c9a0-4bc6-9327-11c71053be3c" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-55" src="https://github.com/user-attachments/assets/7114258f-7aa1-48c7-ab75-61d50226b74e" />
이동약자
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-53-58" src="https://github.com/user-attachments/assets/c68ec49f-c595-4d4a-9dd4-f36f870650d6" />
폭행감지
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-01" src="https://github.com/user-attachments/assets/6195575e-b1f7-4d1c-a23d-af627e5bb10b" />
협업툴
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-18" src="https://github.com/user-attachments/assets/8cfb0b63-9a8d-4fd8-8601-97b5af6efc12" />
기대효과
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-05" src="https://github.com/user-attachments/assets/41d2c85a-4cc0-4cd6-bafd-d28196fd3f15" />
협업툴
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-09" src="https://github.com/user-attachments/assets/f8cfcd1e-267c-4720-ae3e-74a7715ae355" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-10" src="https://github.com/user-attachments/assets/cb092f1e-41e6-42ff-9abe-49d53a44938e" />







<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-18" src="https://github.com/user-attachments/assets/023a8e7b-c4c5-46f6-8e90-f93284f5f2ba" />

팀원소개 


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
