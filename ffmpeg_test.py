import asyncio
import shutil
import sys

async def test_ffmpeg_pipe():
    print("\n[2] ffmpeg 파이프 입력/출력 테스트 중...")

    # ffmpeg 프로세스 생성 (디스코드 봇이 보통 이렇게 씀)
    proc = await asyncio.create_subprocess_exec(
        FFMPEG_BIN,
        '-hide_banner',          # 깔끔하게
        '-loglevel', 'info',     # info 레벨 로그
        '-f', 's16le',           # raw pcm 입력이라고 가정
        '-ar', '48000',          # sample rate
        '-ac', '2',              # stereo
        '-i', 'pipe:0',          # stdin에서 입력 받음
        '-f', 'null', '-',       # 출력은 그냥 버림
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # ffmpeg에 더미(0으로 채운 가짜 오디오 바이트) 조금 밀어넣고 stdin 닫기
    fake_audio = b"\x00" * 48000 * 2 * 2 // 10
    # = 0.1초 분량 정도의 무음 PCM 데이터
    proc.stdin.write(fake_audio)
    await proc.stdin.drain()
    proc.stdin.close()

    # 결과 기다리기
    stderr_data = await proc.stderr.read()
    stdout_data = await proc.stdout.read()
    returncode = await proc.wait()

    print(f"ffmpeg 종료 코드(returncode): {returncode}")
    print("\n--- ffmpeg stderr (로그) ---")
    print(stderr_data.decode(errors="replace"))
    print("--- 끝 ---")

    # returncode 0이면 성공적으로 처리된 것
    return returncode == 0

# 0. ffmpeg 바이너리 경로 찾기
FFMPEG_BIN = shutil.which("ffmpeg")

async def main():
    print("[0] ffmpeg 바이너리 위치 확인")
    if FFMPEG_BIN is None:
        print("❌ ffmpeg 를 PATH에서 못 찾았어.")
        print("Termux에서 아래 실행해서 설치했는지 확인해봐:")
        print("    pkg install ffmpeg")
        sys.exit(1)
    else:
        print(f"✅ ffmpeg 위치: {FFMPEG_BIN}")

    # 1. ffmpeg -version 체크
    print("\n[1] ffmpeg -version 출력:")
    ver_proc = await asyncio.create_subprocess_exec(
        FFMPEG_BIN, "-version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    ver_out, ver_err = await ver_proc.communicate()
    print(ver_out.decode(errors="replace"))
    if ver_err:
        print("stderr:")
        print(ver_err.decode(errors="replace"))

    # 2. 파이프 테스트
    ok = await test_ffmpeg_pipe()

    print("\n[결과 요약]")
    if ok:
        print("🎉 ffmpeg 파이프 입출력까지 정상적으로 작동하고 있어. (디스코드 음악봇이 쓸 준비 됨)")
    else:
        print("⚠ ffmpeg 실행은 됐는데 파이프 처리가 비정상일 수 있어.")
        print("   - 봇에서 사용하는 ffmpeg 인자랑 이 스크립트 인자를 비교해봐.")
        print("   - 오디오 포맷(-f s16le / -ar 48000 / -ac 2) 맞는지 확인 필요.")

if __name__ == "__main__":
    # Termux python은 기본적으로 asyncio 루프 사용 가능
    asyncio.run(main())