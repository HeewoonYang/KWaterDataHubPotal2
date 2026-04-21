# 로컬 Rocky Linux 9.x VM 시뮬레이터

폐쇄망 VM 구축 절차([docs/폐쇄망_Rocky9_서버구축_가이드.md](../../docs/폐쇄망_Rocky9_서버구축_가이드.md))를 로컬 PC 의 Docker 위에서 미리 연습하기 위한 컨테이너입니다.

> ※ 실제 Rocky 9.6 와 최대한 근접하도록 `rockylinux:9.3` 공식 이미지를 사용합니다. (9.6 태그는 공식 Docker Hub 에 아직 없어 최신 마이너를 사용)
> 패키지 관리(dnf), SELinux 컨텍스트, systemd 동작은 실제 VM 과 다릅니다 — **SSH 접속/명령 실행/파일 배치 연습 용도로만** 사용하세요.

---

## 1. 기동

```powershell
# PowerShell 또는 Git Bash
cd D:\00_수공프로젝트\dataHubPotal2\sandbox\rocky9-vm

# 이미지 빌드 + 기동 (최초 1회 5~10분 소요)
docker compose up -d --build

# 상태 확인
docker compose ps
docker compose logs -f rocky9-vm
```

기동되면 컨테이너 `datahub-rocky9-vm` 이 SSH 22번(호스트 2222) 으로 대기합니다.

## 2. 접속

### 2-1. SSH 로 접속 (권장)

Windows 10/11 은 OpenSSH 클라이언트가 기본 설치되어 있습니다.

```powershell
ssh datahub@localhost -p 2222
# 비밀번호: datahub
```

root 접속이 필요하면:

```powershell
ssh root@localhost -p 2222
# 비밀번호: rootpass
```

> 첫 접속 시 호스트 키 등록 여부 묻습니다 → `yes` 입력.
> 컨테이너를 재빌드하면 호스트 키가 바뀌어 `REMOTE HOST IDENTIFICATION HAS CHANGED!` 오류가 납니다. 이때:
> ```powershell
> ssh-keygen -R "[localhost]:2222"
> ```

### 2-2. SSH 키 등록 (비밀번호 없이 접속)

```powershell
# 로컬에 키가 없으면 생성
ssh-keygen -t ed25519 -C "datahub-local"

# 공개키를 컨테이너에 복사
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh datahub@localhost -p 2222 "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### 2-3. `docker exec` 로 바로 들어가기 (SSH 없이)

```powershell
# datahub 계정으로
docker exec -it -u datahub datahub-rocky9-vm bash

# root 로
docker exec -it datahub-rocky9-vm bash
```

### 2-4. VS Code 에서 접속

1. VS Code 확장 `Remote - SSH` 설치
2. `F1` → `Remote-SSH: Connect to Host` → `ssh datahub@localhost -p 2222`
3. 비밀번호 `datahub` 입력

---

## 3. 기본 계정 정보

| 계정 | 비밀번호 | 권한 |
|------|---------|------|
| `datahub` | `datahub` | `wheel` 그룹, `NOPASSWD sudo` |
| `root` | `rootpass` | 최고 권한 |

> 비밀번호를 바꾸려면 `sandbox/rocky9-vm/docker-compose.yml` 의 `args` 를 수정하고 재빌드:
> ```powershell
> docker compose down
> docker compose up -d --build
> ```

---

## 4. 파일 공유 (호스트 ↔ 컨테이너)

`./shared/` 디렉토리가 컨테이너의 `/home/datahub/shared` 로 마운트되어 있습니다.

```powershell
# 호스트에서 airgap 패키지 복사
mkdir D:\00_수공프로젝트\dataHubPotal2\sandbox\rocky9-vm\shared
copy datahub-airgap-*.tar.gz D:\00_수공프로젝트\dataHubPotal2\sandbox\rocky9-vm\shared\

# 컨테이너 안에서
ssh datahub@localhost -p 2222
ls -la ~/shared
```

---

## 5. 폐쇄망 가이드 연습 시 유의사항

이 컨테이너는 최소 패키지만 포함합니다. 실제 가이드대로 연습할 때:

| 가이드 섹션 | 이 컨테이너에서 | 비고 |
|------------|---------------|------|
| 3-1. 계정 생성 | **생략** | `datahub` 가 이미 생성됨 |
| 3-3. SELinux / swap / sysctl | **일부 불가** | 컨테이너는 커널 공유 — `setenforce`, `swapoff` 는 오류 |
| 3-4. 디스크 파티션 | **불가** | 호스트 볼륨 사용 |
| 4. Docker 설치 | **Docker-in-Docker 필요** | `privileged: true` + `/var/lib/docker` 볼륨 추가 필요 |
| 5. 이미지 load / compose 기동 | **불가 (권장)** | 호스트 Docker 에서 이미 compose 로 실행 중 |
| 8. nginx + TLS | **가능** | `dnf install nginx` 로 테스트 가능 |
| 9. 접속 확인 | **부분 가능** | 네트워크 격리 모사만 |

**실제 통합 테스트**는 이 컨테이너가 아닌 **별도 Rocky 9.6 VM(VirtualBox / Hyper-V / VMware)** 에서 수행하세요.

이 컨테이너는 다음 용도로 적합합니다:
- SSH 접속 연습
- `dnf install`, 파일 배치, sudo 명령어 순서 연습
- `.env`, `docker-compose.yml` 편집 연습
- 스크립트(`airgap-import.sh` 등) 문법/경로 검증

---

## 6. 정지 / 제거

```powershell
# 정지 (데이터 유지)
docker compose stop

# 완전 제거 (이미지/볼륨 포함)
docker compose down --rmi local --volumes
```

---

## 7. 트러블슈팅

| 증상 | 해결 |
|------|------|
| `Permission denied (publickey,password)` | `docker compose logs rocky9-vm` 로 sshd 기동 확인, 비밀번호 오타 재확인 |
| `REMOTE HOST IDENTIFICATION HAS CHANGED!` | `ssh-keygen -R "[localhost]:2222"` |
| 포트 2222 이미 사용 중 | `docker-compose.yml` 의 `2222:22` 를 `2223:22` 등으로 변경 후 `ssh -p 2223` |
| Windows Defender 가 파일 차단 | `./shared` 디렉토리를 Defender 예외에 추가 |
| 컨테이너 재기동 후 변경사항 사라짐 | 컨테이너 파일시스템은 휘발성 — 호스트 마운트(`./shared`)에 작업물 보관 |
