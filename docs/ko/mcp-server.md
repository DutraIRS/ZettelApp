# MCP 서버

[Model Context Protocol](https://modelcontextprotocol.io/)(MCP)은 AI 어시스턴트가 다른 프로그램의 도구와 데이터를
사용할 수 있게 해 주는 개방형 표준이에요. ZettelApp에는 MCP 서버가 들어 있어서 **Claude Desktop**이나
**Claude Code** 같은 어시스턴트가 도와주는 동안 Zettelkasten을 검색하고, 노트를 읽고, 유형이 있는 링크를 따라가고,
링크 제안을 요청할 수 있어요.

## 실행 방식

서버는 `ZettelApp.exe` 옆에 설치되는 별도의 작은 프로그램인 **`zettelapp-mcp.exe`**예요. 소스에서는 같은 서버를
`python -m zettelapp.mcp_main`으로 실행해요. MCP 클라이언트가 필요할 때 이를 시작하고 표준 입출력으로 통신해요.
**네트워크 포트는 열리지 않아요.**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

`--vault`가 없으면 ZettelApp에서 마지막으로 연 볼트를 제공해요. MCP로 변경한 내용은 몇 초 안에 앱에 나타나요.

## MCP 스위치

MCP 클라이언트는 **ZettelApp이 열려 있고 상태 표시줄의 MCP 스위치가 켜져 있는** 동안에만 노트에 접근할 수 있어요.
스위치는 **ZettelApp을 시작할 때마다 꺼져 있으므로**, 어시스턴트가 노트를 읽어도 되는지 세션마다 직접 결정해요. 스위치를
끄거나 ZettelApp을 닫으면 서버는 약 1초 안에 멈춰요. 스위치가 없으면 서버는 시작을 거부하고 이유를 알려 줘요. 정확한
동작은 [MCP API 레퍼런스](mcp-reference.md)를 참고하세요.

## Claude Desktop 연결

*도구 ▸ 옵션 ▸ MCP 서버*를 열고 **Claude Desktop에 추가…**를 클릭하세요. ZettelApp이 `%APPDATA%\Claude\claude_desktop_config.json`에
자신을 추가해요(이전 파일은 백업해 둬요). 그런 다음 Claude Desktop을 다시 시작하세요. Claude Desktop을 시작하기 전에
ZettelApp 상태 표시줄의 **MCP 스위치**를 켜세요. 나중에 켰다면 Claude Desktop에서 ZettelApp을 다시 연결하거나 Claude
Desktop을 다시 시작하세요. 직접 하려면 그 페이지에 표시된 스니펫을 파일에 복사하세요. 다음과 같은 모양이에요.

```json
{
  "mcpServers": {
    "zettelapp": {
      "command": "C:\\Users\\me\\AppData\\Local\\Programs\\ZettelApp\\zettelapp-mcp.exe",
      "args": ["--vault", "C:\\Users\\me\\Documents\\ZettelApp"]
    }
  }
}
```

## Claude Code 연결

같은 옵션 페이지에 복사할 명령이 표시돼요.

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

다른 MCP 클라이언트에도 같은 명령과 인수가 필요해요. Claude Desktop과 마찬가지로 먼저 ZettelApp에서 MCP를 켜고, 나중에
켰다면 서버를 다시 연결하세요(Claude Code에서는 `/mcp`).

## 도구

| 도구 | 하는 일 |
|---|---|
| `search_notes` | 제목, 본문, 태그를 전문 검색해요(`tag:name` 필터도 동작해요). 검색어가 비어 있으면 최근에 편집한 노트를 나열해요. |
| `get_note` | 노트의 전체 텍스트, 태그, 출처 링크, 날짜, 양방향의 유형이 있는 링크, 플래시카드, 마인드맵 개요. |
| `list_tags` | 모든 태그와 각 태그를 사용하는 노트 수. |
| `get_subgraph` | 노트에서 1–4개 링크 이내의 노트와 그 사이의 유형이 있는 링크(일부 링크 유형만 선택 가능). |
| `suggest_links` | 노트와 관련이 있을 가능성이 높지만 아직 링크되지 않은 노트를 [나이브 베이즈 제안기](link-suggestions.md)의 순위로 보여 줘요. |
| `list_link_types` | *뒷받침*, *반박*, *상위 항목*처럼 볼트에 있는 링크 유형. |
| `create_note` | *(쓰기)* 노트를 만들어요. 본문의 `[[Title]]`은 기존 노트에 링크돼요. |
| `add_link` | *(쓰기)* 한 노트에서 다른 노트로 유형이 있는 링크를 추가해요. |

## 기본적으로 읽기 전용

서버는 볼트를 **읽기 전용**으로 열어요. 두 가지 쓰기 도구는 다음 두 조건이 **모두** 참일 때만 제공돼요.

1. *옵션 ▸ MCP 서버*에서 **MCP 클라이언트가 노트와 링크를 만들도록 허용**이 체크되어 있어요.
2. 서버가 `--allow-writes`로 시작되었어요. 옵션을 체크하면 옵션 페이지의 스니펫에 이 플래그가 포함돼요.

이 설정은 쓰기마다 다시 확인되므로 체크를 해제하면 즉시 적용돼요. 켜려면 MCP 클라이언트가 서버를 다시 시작해야 해요.

노트 내용은 데이터로서 어시스턴트에 전달되며, 서버는 어시스턴트에게 이를 지시로 취급하지 말라고 알려요. 입력(ID, 크기,
한도)은 검증되고, 서버는 볼트 밖의 파일을 절대 건드리지 않아요.

## 문제 해결

- **클라이언트에서 서버 시작에 실패했다고 하거나 도구 호출에서 스위치가 꺼져 있다고 해요.** ZettelApp을 열고 상태
  표시줄에서 MCP를 켠 다음 클라이언트에서 서버를 다시 연결하세요.
- **서버가 여전히 시작되지 않아요.** `zettelapp-mcp.exe` 경로가 맞는지 확인하세요. 터미널에서 직접 명령을 실행해 보세요.
  무엇이 잘못되었는지(예: "No ZettelApp vault found") 표준 오류로 알려 줘요.
- **쓰기 도구가 없어요.** 옵션을 체크하고 `--allow-writes`도 추가한 다음 클라이언트를 다시 시작하세요.
