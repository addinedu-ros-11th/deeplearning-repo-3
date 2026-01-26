# 🥐 [Bake Sight] 
**Vision-Based Smart Bakery Operations Platform**

**딥러닝 프로젝트 3조 - 비전 기반 스마트 베이커리 운영 및 통합 관리 시스템**

## 📋 목차
1. [주제 선정](#01주제-선정)
2. [프로젝트 설계](#02프로젝트-설계)
3. [기술 시연 및 소개](#03기술-시연-및-소개)
4. [빵 스캐너 주요 기술](#04빵-스캐너-주요-기술)
5. [Trouble Shooting](#05trouble-shooting)
6. [향후 개선 과제](#06향후-개선-과제)



더 자세한 내용을 ppt로 보실수 있습니다..click ->>[**🥐🥐🥐** ](https://www.canva.com/design/DAG8-Zmcdlo/UDOH503owk026jmjTULwXA/view?utm_content=DAG8-Zmcdlo&utm_campaign=designshare&utm_medium=link2&utm_source=uniquelinks&utlId=h0223e34169)

---

## 01.주제 선정

<img width="1133" height="477" alt="Screenshot from 2026-01-26 18-30-09" src="https://github.com/user-attachments/assets/17e7f3bd-e1bc-4514-a295-72b9b9e7f964" />




      
빵지순례' 문화로 방문객은 급증했지만, 매장의 처리 속도는 이를 따라가지 못합니다. 

* 고객: 맛있는 빵을 눈앞에 두고 1~2시간 대기하는 불편함
* 점주: 피크타임 회전율 저하로 인한 매출 손실 


이에 저희는 **비전 기술**을 활용한 **빵 스캐너**로 해결하고자 합니다.

<img width="1140" height="402" alt="Screenshot from 2026-01-26 18-31-16" src="https://github.com/user-attachments/assets/298b39c2-c1d4-4661-ad9b-d13a46a325e1" />

<img width="1140" height="403" alt="Screenshot from 2026-01-26 18-31-50" src="https://github.com/user-attachments/assets/a2d09406-327c-4e09-998c-7ab06781c62b" />




- 또한 빵 스캐너로 결제 대기열을 해소함과 동시에, **Vision AI 기반 CCTV 시스템**으로 매장 내 사각지대를 메웠습니다.

<img width="1140" height="523" alt="Screenshot from 2026-01-26 18-33-43" src="https://github.com/user-attachments/assets/b8abeefc-8335-47ae-8efe-a953a7ab7232" />


### 프로젝트 목표

<img width="1129" height="400" alt="Screenshot from 2026-01-26 18-35-13" src="https://github.com/user-attachments/assets/e1e2d773-6de0-4d95-bf66-6e417c3b0c72" />


                                       

## 02.프로젝트 설계

### 주요 특징
* **캐셔리스 결제:** 탑뷰 카메라 기반 상품 탐지·세분류 및 가격 DB 자동 매칭
* **매장 관제 분석:** CCTV 영상을 통한 인원수, 대기열, 테이블 회전율 실시간 트래킹
* **보안 및 안전:** 미결제 반출 탐지 및 매장 내 이상 행동(넘어짐 등) 감지 이벤트화
* **통합 대시보드:** 매출 통계, 실시간 재고 추정 및 운영 지표 시각화

---

### 시스템 아키텍처
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-38-01" src="https://github.com/user-attachments/assets/5d8fd099-b777-4b37-b5c1-1fd59288ebc0" />



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

<img width="1092" height="560" alt="Screenshot from 2026-01-26 18-36-36" src="https://github.com/user-attachments/assets/5700f5cc-c0e5-49c3-9241-b8b4993d702d" />


### 빵 분류 방법

<img width="1924" height="966" alt="Screenshot from 2026-01-26 13-16-56" src="https://github.com/user-attachments/assets/09a44344-2cc2-47c7-8009-326fba25b10d" />

<img width="1924" height="966" alt="Screenshot from 2026-01-26 13-17-07" src="https://github.com/user-attachments/assets/1151d691-b11c-4a11-a677-3aa278579156" />

<img width="1924" height="966" alt="Screenshot from 2026-01-26 13-17-00" src="https://github.com/user-attachments/assets/7b4c315c-d053-4d2d-9166-937d7d8eed51" />


### CCTV 감지 시연 

<img width="1085" height="539" alt="Screenshot from 2026-01-26 19-02-11" src="https://github.com/user-attachments/assets/bdd33c72-9690-451e-9fee-61b4947657fe" />


## 넘어짐 감지 모델

![넘어짐감지](https://github.com/user-attachments/assets/9406f0bf-4e06-4f3d-ab89-cb775ef3ffd2)

*Pose + LSTM*

<img width="463" height="76" alt="Screenshot from 2026-01-26 19-04-47" src="https://github.com/user-attachments/assets/9a25b55d-aabc-4cf5-a845-1e61bb4f663f" />


## 폭행 감지 모델

![폭행시연](https://github.com/user-attachments/assets/b19198f4-a58e-44eb-b72f-cab206852695)

<img width="611" height="281" alt="Screenshot from 2026-01-26 19-06-05" src="https://github.com/user-attachments/assets/13b1c7a0-4a5a-4d50-9646-9b40c90aa03f" />





## 이동약자 감지 모델 

![202601211308-ezgif com-video-to-gif-converter (1)](https://github.com/user-attachments/assets/ac23a2cb-0c0e-46c0-9fbf-ac9f0b20af48)

*YOLO8s*

<img width="387" height="485" alt="Screenshot from 2026-01-26 19-07-31" src="https://github.com/user-attachments/assets/144a947e-02d3-4316-89f7-386e3b4567df"/>
<img width="583" height="570" alt="Screenshot from 2026-01-26 19-07-14" src="https://github.com/user-attachments/assets/d341c635-fcc3-49c6-aba6-f1e2afc85a70" />

## 관리자 대시 보드



## 04.빵 스캐너 주요 기술

### 04-1.DETECTION
<img width="1159" height="571" alt="Screenshot from 2026-01-26 13-26-39" src="https://github.com/user-attachments/assets/19813f7d-908a-4541-bbd7-bb589c5589eb" />
<img width="1159" height="541" alt="Screenshot from 2026-01-26 13-27-27" src="https://github.com/user-attachments/assets/fbac1ba0-9f2d-4441-a763-a637d3d8f7de" />

### 빵 감지 모델지표

<img width="1853" height="644" alt="Screenshot from 2026-01-26 18-37-48" src="https://github.com/user-attachments/assets/3bca050e-66b0-4343-92b4-c617c0476bf2" />

### 04-2.CLASSIFICATION
<img width="1159" height="295" alt="Screenshot from 2026-01-26 13-29-02" src="https://github.com/user-attachments/assets/3641d098-8152-4fe6-b556-e9b23d30945f" />

#### 이 프로세스는 YOLO로 *'영역'*을 찾고, ResNet으로 *'특징'*을 뽑아, kNN으로 *'정답'*을 매칭하는 구조입니다.

1. 기준 임베딩 DB 구축 (Prototype Preparation)

목적
시스템이 분류할 수 있는 메뉴별 기준점을 생성하는 단계입니다.

과정
프로토타입 빵 이미지를 ResNet50 모델에 통과시켜 고유한
 *임베딩 벡터*를 생성합니다.

결과
생성된 벡터들은 메뉴별 디지털 지문 역할을 하며,
향후 비교를 위한 데이터베이스에 저장됩니다.

2. YOLOv8 기반 타겟 추출 및 전처리

YOLOv8 Seg 활용
입력 이미지에서 YOLOv8 Segmentation 모델이
빵 객체의 영역을 마스킹 하여 정밀하게 추출합니다.

데이터 규격화
추출된 영역을 ResNet 모델의 입력 규격에 맞게
*Resize 및 정규화*하여 테스트용 임베딩 벡터를 생성합니다.

특징
단순 전체 이미지가 아닌, YOLO가 탐지한
*핵심 객체 영역(ROI)*만을 사용함으로써 분류 정확도를 극대화합니다.

3. kNN을 이용한 메뉴 매칭

거리 비교
실시간으로 생성된 테스트 임베딩 벡터와
DB에 저장된 기준 임베딩 벡터들 간의 거리를
kNN알고리즘으로 계산합니다.

최종 식별
기준 벡터 중 가장 거리가 가까운(유사도가 높은)
프로토타입 메뉴를 찾아 해당 빵의 종류를 최종 확정합니다.


## 05.Trouble Shooting

### 빵 문제해결
<img width="869" height="509" alt="Screenshot from 2026-01-26 13-29-40" src="https://github.com/user-attachments/assets/a05218ae-aef8-46fb-8f02-a290df4ce824" />

### 넘어짐 문제해결

<img width="1078" height="509" alt="Screenshot from 2026-01-26 13-31-12" src="https://github.com/user-attachments/assets/1910262f-6f74-4641-8dd8-ed388fefac98" />

### 폭행 문제해결

![ezgif com-video-to-gif-converter](https://github.com/user-attachments/assets/3f6682d0-bd90-40e8-8dad-c178750f2f2e)


## 06.향후 개선 과제 

### 빵스캐너 개선 과제

<img width="1086" height="411" alt="Screenshot from 2026-01-26 19-11-57" src="https://github.com/user-attachments/assets/c938bece-cc26-4c6c-953f-12cc91879762" />

### CCTV 개선 과제

<img width="1086" height="411" alt="Screenshot from 2026-01-26 19-12-39" src="https://github.com/user-attachments/assets/78034b30-44e1-4b8b-9d2c-a2936bc5dea7" />




### ERD

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-38-27" src="https://github.com/user-attachments/assets/45c1b30f-5c29-4ba8-8afb-57980ddce04b" />

### 기술 스택

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-37-46" src="https://github.com/user-attachments/assets/f5be026b-7e9a-429f-b00c-f02d7033128a" />

<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-09" src="https://github.com/user-attachments/assets/f8cfcd1e-267c-4720-ae3e-74a7715ae355" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-10" src="https://github.com/user-attachments/assets/cb092f1e-41e6-42ff-9abe-49d53a44938e" />
<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-18" src="https://github.com/user-attachments/assets/023a8e7b-c4c5-46f6-8e90-f93284f5f2ba" />

<img width="2059" height="799" alt="Screenshot from 2026-01-21 17-59-43" src="https://github.com/user-attachments/assets/7c6f08ae-482a-4c76-b1c9-7d49261481d7" />


### 팀원소개 


<img width="1920" height="1080" alt="Screenshot from 2026-01-16 09-54-41" src="https://github.com/user-attachments/assets/7e9a9563-ce2c-4486-ba9f-674885a6e17a" />




