# Rocky Linux 9.6 로컬 VM 시뮬레이션 이미지
# - 폐쇄망 VM 환경을 흉내내기 위한 SSH 접속 가능한 컨테이너
# - sudo 가능한 운영 계정(datahub) 포함
FROM rockylinux:9.3

ARG USER_NAME=datahub
ARG USER_PASSWORD=datahub
ARG ROOT_PASSWORD=rootpass

RUN dnf -y --allowerasing install \
      openssh-server \
      sudo \
      passwd \
      which \
      vim-minimal \
      curl \
      wget \
      tar \
      gzip \
      unzip \
      net-tools \
      iproute \
      iputils \
      procps-ng \
      bash-completion \
      ca-certificates \
      hostname \
 && dnf clean all \
 && rm -rf /var/cache/dnf

# SSH 호스트 키 생성
RUN ssh-keygen -A

# SSH 설정: root 비밀번호 로그인 허용 (로컬 테스트용)
RUN sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config \
 && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config \
 && sed -i 's/^#\?UsePAM.*/UsePAM no/' /etc/ssh/sshd_config

# root + 운영 계정
RUN echo "root:${ROOT_PASSWORD}" | chpasswd \
 && useradd -m -s /bin/bash ${USER_NAME} \
 && echo "${USER_NAME}:${USER_PASSWORD}" | chpasswd \
 && usermod -aG wheel ${USER_NAME} \
 && echo "%wheel ALL=(ALL) NOPASSWD: ALL" > /etc/sudoers.d/wheel-nopasswd \
 && chmod 440 /etc/sudoers.d/wheel-nopasswd

# 타임존
RUN ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D", "-e"]
