# 웹 앱을 담을 도커 이미지를 만드는 설계도입니다.
# 빌드 명령: docker build -t mentationlab/devnote:1.0.0 .

# 파이썬 3.14가 설치된 가벼운(slim) 리눅스를 기반으로 시작
FROM python:3.14-slim

# 파이썬 실행 환경 설정
# - PYTHONDONTWRITEBYTECODE: .pyc 캐시 파일 생성 안 함 (컨테이너에선 불필요)
# - PYTHONUNBUFFERED: 로그를 버퍼 없이 즉시 출력 (docker logs로 바로 확인 가능)
# - PIP_DISABLE_PIP_VERSION_CHECK: pip 버전 확인 생략 (빌드 속도 향상)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 컨테이너 안의 작업 폴더를 /app으로 지정
WORKDIR /app

# 보안을 위해 root가 아닌 전용 사용자(app)를 만듭니다.
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app

# 의존성 목록을 먼저 복사해서 설치합니다.
# (코드가 바뀌어도 requirements.txt가 그대로면 이 단계는 캐시를 재사용 → 빌드 빨라짐)
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# 프로젝트 코드 전체를 복사 (소유자를 app 사용자로 지정)
COPY --chown=app:app . /app

# 정적 파일·업로드 파일 폴더를 미리 만들고 권한을 app 사용자에게 부여
RUN mkdir -p /app/staticfiles /app/media \
    && chown -R app:app /app

# 이후 명령은 root가 아닌 app 사용자로 실행
USER app

# 컨테이너가 8000번 포트를 사용한다고 알림 (gunicorn이 여기서 대기)
EXPOSE 8000
