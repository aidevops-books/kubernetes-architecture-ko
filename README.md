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

## 라이선스

Copyright © 2026 John Bae

- **실습 코드** (매니페스트, Dockerfile, 스크립트, 설정, 예제 애플리케이션 소스): [MIT License](LICENSE). 저작권 표시를 유지하면 자유롭게 쓰고 고칠 수 있습니다.
- **설명 글** (이 README를 포함한 모든 Markdown 문서): [CC BY-NC-ND 4.0](LICENSE-docs). 출처를 밝히고, 비영리 목적으로, 내용을 바꾸지 않을 때 공유할 수 있습니다. 문서 안에 적힌 명령과 코드 조각은 실습 코드와 같이 MIT로 쓸 수 있습니다.
- **책 본문과 그림**은 이 저장소에 들어 있지 않으며 모든 권리를 보유합니다.

예제가 사용하는 Container Image, Helm Chart 등 다른 프로젝트의 소프트웨어는 각 프로젝트의 라이선스를 따릅니다.
