# CloudShop — 『그림으로 이해하는 Kubernetes 아키텍처』 동반 자료

자료 판본: v1.0 · 대응 도서: 제1판 (2026).

배포 파일: `Kubernetes-Architecture-Companion-v1.0.zip`. 압축을 풀고 `companion/` 폴더가 들어 있는 상위 폴더에서 아래 명령을 실행합니다. `backups/`는 백업 실습 시 생성되며 실제 DB 덤프와 실행 캐시는 배포 파일에 포함하지 않습니다.

이 디렉터리는 책 전체(01~33장)에서 사용하는 실습 프로젝트 **CloudShop**의 전체 소스입니다.
Web → Edge → API → Data(PostgreSQL + Redis)로 이어지는 하나의 서비스를 책 전체에서 점진적으로
확장합니다. 모든 매니페스트·스크립트는 kind 3-Node Cluster(`architecture-book`)에서 1~33장
전체를 실행해 검증했습니다. 검증 범위와 발견된 문제는 부록 A와 저장소의 검수 기록을 참고하세요.

## 디렉터리 구조

```text
companion/
├── kind/
│   └── kind-config.yaml        표준 3-Node Cluster 설정 (Control Plane 1 + Worker 2)
├── api/                        CloudShop API (Python 표준 라이브러리 HTTP 서버)
├── web/                        정적 프런트엔드
├── k8s/                        기본 배포 매니페스트 — 순서대로 적용
│   ├── 00-namespace.yaml       cloudshop Namespace
│   ├── 10-web.yaml             Web Deployment + Service
│   ├── 20-data.yaml            PostgreSQL(StatefulSet) + Redis
│   ├── 30-api.yaml             API Deployment + Service
│   └── 40-edge.yaml            Edge(Nginx) Deployment + Service — 외부 진입점
├── labs/                       장별 개별 실험. 실습 후 원상 복구하거나 삭제
│   ├── client.yaml             DNS·연결 확인용 상주 테스트 Pod (9장~)
│   ├── pending.yaml            Pending 상태 재현 (4장)
│   ├── report-job.yaml         Job 실습 (8장)
│   ├── hpa.yaml                HorizontalPodAutoscaler (18장 — Metrics Server 필요)
│   ├── pdb.yaml                PodDisruptionBudget (19장)
│   ├── rbac.yaml                ServiceAccount/Role/RoleBinding (22장)
│   ├── network-policy.yaml     NetworkPolicy 5종 (23장)
│   └── external-mock.yaml      지연·오류 주입용 외부 시스템 모의 서버 (26장, 32장)
├── optional/                   본문에서 선택적으로 다루는 확장 예제
│   ├── ingress.yaml
│   └── gateway.yaml
├── scripts/                    Python 유틸리티. 모두 `cloudshop` Namespace에
│   │                           `purpose: architecture-book-lab` 라벨이 있는지 확인한 뒤 동작
│   ├── common.py               kubectl 래퍼, 라벨 안전장치, psql 헬퍼
│   ├── setup_secret.py         DB 비밀번호 1회 생성 (재실행해도 기존 값 유지)
│   ├── smoke.py                Edge 경유 헬스체크 + 주문 흐름 스모크 테스트
│   ├── load.py                 초당 요청 수 기반 부하 생성기 (HPA 실습용)
│   ├── backup.py / restore_check.py   PostgreSQL 백업/복구 확인 (16장)
│   └── lab.py                  readiness-break / readiness-restore 프로브 실험 (17장)
├── tests/
│   └── test_api.py             API 유닛 테스트 (SQLite 로컬 모드)
└── backups/                    backup.py 산출물. .gitignore 처리됨
```

## 빠른 시작

```bash
# 1. Docker 엔진 실행 확인 후 전용 Cluster 생성
kind create cluster --name architecture-book --config companion/kind/kind-config.yaml
kubectl config use-context kind-architecture-book

# 2. 이미지 빌드 및 로드
docker build -t cloudshop-api:0.1.0 companion/api
docker build -t cloudshop-web:0.1.0 companion/web
kind load docker-image cloudshop-api:0.1.0 cloudshop-web:0.1.0 --name architecture-book

# 3. 배포
python companion/scripts/setup_secret.py
kubectl apply -f companion/k8s
kubectl rollout status statefulset/postgres -n cloudshop --timeout=180s
kubectl rollout status deployment/api -n cloudshop --timeout=180s
kubectl rollout status deployment/web -n cloudshop --timeout=120s
kubectl rollout status deployment/edge -n cloudshop --timeout=120s

# 4. 확인 (다른 터미널)
kubectl port-forward -n cloudshop service/edge 8080:8080
python companion/scripts/smoke.py
```

18장(HPA) 실습 전에는 Metrics Server 설치가 별도로 필요합니다 — 부록 A의 "메트릭 서버 설치"
절차를 먼저 실행하세요.

## 장별 준비물

| 장 | 필요한 추가 작업 |
|---|---|
| 1~2 | 읽기·조회만. 배포 불필요 |
| 3~7 | Namespace + Web 배포(`00-namespace.yaml`, `10-web.yaml`)만 있으면 충분 |
| 8 | Job 실습 전 전체 DB 구성(`20-data.yaml`, `30-api.yaml`) 완료 권장 |
| 9~12 | 기본 배포 + `labs/client.yaml` |
| 13~17 | 기본 배포만으로 충분 |
| 18 | 부록 A의 Metrics Server 설치 + `labs/hpa.yaml` |
| 19 | `labs/pdb.yaml` |
| 22 | `labs/rbac.yaml` |
| 23 | `labs/network-policy.yaml` |
| 26, 31 | `labs/external-mock.yaml` — 실습 후 반드시 재적용해 기본값(DELAY_SECONDS=0, FAIL=false)으로 복원 |
| 29 | 전체 스택 처음부터 재배포 |

## 정리

```bash
kind delete cluster --name architecture-book
```

## 상태

이 저장소는 현재 이 책의 소스 저장소 안에 로컬로만 존재합니다. 별도 공개 저장소(GitHub 등)
배포 여부와 위치는 아직 확정되지 않았습니다 — 확정되면 이 파일과 책의 "동반 자료" 절을 함께
갱신합니다.
