# Kubernetes Architecture — 그림으로 이해하는 Kubernetes 구조와 동작 원리 — 실습 자료

『Kubernetes Architecture — 그림으로 이해하는 Kubernetes 구조와 동작 원리』(John Bae 지음, 『아키텍처를 읽는 법』 3권)의 공식 실습 자료입니다.
책에서 `companion/...`으로 가리키는 파일이 이 저장소의 `companion/` 폴더에 같은 경로로 들어 있습니다.

- 도서 안내: <https://www.aidevops.kr/books/>

## 받는 방법

```bash
git clone https://github.com/aidevops-books/kubernetes-architecture-ko.git
cd kubernetes-architecture-ko/companion
```

## 폴더 구성

```text
companion/
├── api/
├── k8s/
├── kind/
├── labs/
├── optional/
├── scripts/
├── tests/
├── web/
├── .gitignore
└── README.md
```

실습 순서와 준비물, 각 파일의 쓰임은 [`companion/README.md`](companion/README.md)에 있습니다. 먼저 그 문서를 읽으세요.

## 사용할 때

- 학습용 환경에서만 사용하세요. 예제에 들어 있는 비밀번호와 토큰은 실습용 값이며 실제 서비스에 쓰면 안 됩니다.
- 책과 다른 버전의 도구에서는 출력이나 옵션이 조금 다를 수 있습니다.
- 오류를 발견하면 책 제목과 판본, 장 번호, 실행 환경, 재현 절차를 함께 Issue로 알려 주세요.
