# 시작하기

## 설치

ZettelApp은 **Windows 10(21H2 이상), Windows 11, 그리고 최근 64비트 Linux 데스크톱**에서 실행돼요.
[최신 릴리스](https://github.com/DutraIRS/ZettelApp/releases/latest)에서 내려받으세요.

### Windows

| 다운로드 | 이럴 때 사용하세요 |
|---|---|
| [Microsoft Store](https://apps.microsoft.com/detail/9PB0HCDXF63D) | 가장 쉬운 방법입니다. 스토어에서 설치하고, 자동으로 업데이트되며, SmartScreen 경고가 나타나지 않습니다. |
| `ZettelApp-Setup.exe` | 시작 메뉴 항목, *설정 ▸ 앱*의 제거 프로그램, Anki에서 노트를 여는 `zettelapp://` 링크가 있는 일반적인 설치를 원할 때. 관리자 권한은 필요 없어요. 내 계정에만 설치돼요. |
| `ZettelApp-Portable.zip` | 소프트웨어를 설치할 수 없거나 USB 드라이브에서 실행하고 싶을 때. 아무 곳에나 압축을 풀고 `ZettelApp.exe`를 실행하세요. |

설치 프로그램은 사용할 언어를 묻고 Windows 표시 언어를 추천해요. 설치 프로그램과 앱은 11개 언어로 번역되어 있으며,
앱의 언어는 *옵션*에서 바꿀 수 있어요.

각 릴리스에는 SHA-256 체크섬(`SHA256SUMS.txt`)이 있어요. PowerShell에서 다운로드 파일을 확인하려면:

```powershell
Get-FileHash .\ZettelApp-Setup.exe -Algorithm SHA256
```

### Linux

| 다운로드 | 이럴 때 사용 |
|---|---|
| `ZettelApp-Linux-amd64.deb` | Debian, Ubuntu, Mint 등 `.deb` 기반 배포판. `sudo apt install ./ZettelApp-Linux-amd64.deb`로 설치하거나 소프트웨어 센터에서 열어요. |
| `ZettelApp-Linux-x86_64.tar.gz` | 다른 배포판, 또는 설치 없이 사용: 원하는 곳에 압축을 풀고 `ZettelApp/zettelapp`을 실행하세요. |
| [Flathub](https://flathub.org/apps/io.github.dutrairs.zettelapp) | Flatpak을 사용한다면: `flatpak install flathub io.github.dutrairs.zettelapp` 또는 소프트웨어 센터에서 ZettelApp을 검색하세요. |
| `zettelapp` (Snap) | Snap Store에서: `sudo snap install zettelapp`. |

두 패키지 모두 Python과 Qt를 포함해요. 64비트 데스크톱(X11 또는 Wayland — GNOME, KDE 등)과 표준 그래픽 라이브러리가 필요해요. 터미널에서 다운로드를 확인하려면:

```bash
sha256sum ZettelApp-Linux-amd64.deb
```

API 키는 Secret Service(GNOME Keyring 또는 KWallet)에 저장되고, 키링이 없으면 메모리에만 보관돼요. Anki 카드의 `zettelapp://` 링크는 `.deb`에서는 바로 노트를 열어요. 다른 설치 방식에서는 *옵션 ▸ 데스크톱 통합*에서 핸들러를 설정하세요.

### "Windows에서 PC를 보호했습니다"

빌드는 아직 코드 서명이 되어 있지 않아서, 설치 프로그램을 처음 실행할 때 Microsoft Defender SmartScreen이
경고할 수 있어요. 공식 릴리스 페이지에서 내려받았고 체크섬이 일치한다면 **추가 정보 ▸ 실행**을 선택하세요.
코드 서명은 [로드맵](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md)에 있어요.

## 첫 볼트

**볼트**는 노트를 담는 폴더예요. 데이터베이스 파일(`zettel.db`)과 이미지용 `assets` 폴더로 이루어져요.
처음 시작하면 ZettelApp이 **Documents\ZettelApp**에 서로 링크된 시작용 노트 11개가 있는 볼트를 만들어요.
*ZettelApp에 오신 것을 환영해요* 노트가 링크, 태그, 이미지, 마인드맵, 플래시카드와 앱의 나머지 기능을 안내해
줘요. 선택 사항인 10분짜리 모험은 같은 투어를 실제 동작으로 진행해요. *파일 ▸ 새 볼트…*나 *파일 ▸ 볼트 열기…*로
만든 새 볼트에도 같은 시작 자료가 들어가므로, 다른 곳(예: OneDrive 폴더)에서도 작업할 수 있어요.
*파일 ▸ 최근 항목 열기*에는 최근에 사용한 볼트가 나와요.

노트는 입력하는 대로 자동 저장돼요. 저장 버튼은 없어요.

## 창 둘러보기

![노트 페이지](../website/assets/screenshots/notes-light.png)

왼쪽의 **탐색 레일**로 페이지를 전환해요(Ctrl+1~Ctrl+5).

- **노트**: 노트 목록, 편집기, 사이드 패널.
  - *목록*에는 검색(`tag:name` 필터도 동작해요), 태그 필터, 정렬, 휴지통이 있어요.
  - *편집기*에는 제목, 태그, 선택 사항인 출처 링크, 그리고 **노트**(Markdown, 편집·분할·미리 보기 모드),
    **마인드맵**, **플래시카드** 탭이 있어요.
  - *사이드 패널*에는 **링크 제안**, 노트의 **링크**, **백링크**가 나와요.
- **그래프**: 노트를 2D 또는 3D 네트워크로 보여 주고, 태그나 주제 클러스터별로 색을 입혀요.
- **인사이트**: 볼트에 대한 통계와 차트.
- **복습**: 간격 반복 복습, 퀴즈, Anki.
- **질문**: 원하는 AI 공급자로 노트에 대해 질문해요(선택 사항).

**옵션**(레일 맨 아래 또는 *도구 ▸ 옵션…*, Ctrl+,)에는 테마, 편집기 글자 크기, 링크 제안, 링크 유형, AI, MCP 서버,
Anki, Zotero, 데스크톱 통합, 백업 설정이 있어요.

앱은 시스템의 **밝게/어둡게** 설정과 **강조 색상**을 따라요. *보기 ▸ 테마*에서 테마를 고정할 수 있어요.

앱을 연 채로 강조 색을 바꿔도 바로 따라가요.

*검정 (OLED)*은 OLED 화면을 위해 완전한 검정 위에 그린 어두운 테마예요. *옵션 ▸ 일반*에서 **기본 색상**(버튼 등 강조 요소), **보조 색상**(링크), **강조 색상**(선택한 텍스트와 찾기 결과), **글자 색상**을 직접 고를 수 있어요. *테마 색상 사용*을 누르면 원래대로 돌아가요.

## 업데이트

시작하고 약 4초 뒤에 ZettelApp은 최신 버전을 확인하려고 `https://dutrairs.github.io/ZettelApp/version.json`에
HTTPS 요청을 한 번 보내요. 그 밖에는 아무것도 보내지 않으며(`ZettelApp/<version>` 사용자 에이전트뿐), 요청이
실패해도 아무 알림이 없어요. 더 새로운 버전이 있으면 오른쪽 아래에 작은 알림이 버전당 최대 한 번 나타나요.
포커스를 가져가지 않아요. **다운로드**는 브라우저에서 릴리스 페이지를 열고, **✕**는 알림을 닫고,
**업데이트 확인 안 함**은 확인을 꺼요. *도구 ▸ 옵션 ▸ 일반 ▸ ZettelApp을 시작할 때 업데이트 확인*에서 다시 켤 수
있어요. ZettelApp은 스스로 아무것도 설치하지 않아요.

## 제거

Windows에서는 *Windows 설정 ▸ 앱 ▸ 설치된 앱 ▸ ZettelApp ▸ 제거*를 사용하세요. Linux에서는 패키지를 제거하거나(`sudo apt remove zettelapp`) 소프트웨어 센터에서 삭제하세요. 노트와 `~/.config/ZettelApp`의 설정은 직접 삭제하지 않는 한 남아 있어요. 확인하면 선택되지 않은
**내 ZettelApp 설정과 데이터도 삭제** 옵션이 있는 대화 상자가 나와요. 이 옵션은 설정, 저장된 API 키, 로그, 캐시,
자동 백업(`%LOCALAPPDATA%\ZettelApp`)과 **모든 노트**(볼트의 데이터베이스와 첨부 파일)를 삭제해요.
노트를 유지하려면 선택하지 마세요. 포터블 버전은 폴더를 삭제하세요.

## 다음 단계

- [노트와 링크](notes-and-links.md)에서 노트 문법을 배워 보세요.
- [링크 제안](link-suggestions.md)이 어떻게 동작하는지 읽어 보세요.
- 언제든 **F1**을 눌러 이 설명서를 열거나 [키보드 단축키](keyboard-shortcuts.md)를 보세요.
