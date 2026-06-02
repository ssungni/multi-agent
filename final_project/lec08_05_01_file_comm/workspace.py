"""워크스페이스 관리자 모듈.

Sub-agent 결과를 파일로 저장하고 읽는 기능을 제공합니다.
워크스페이스 디렉터리를 자동 생성하고, JSON 파일 I/O를 관리합니다.
"""

import json
import uuid
from pathlib import Path


class WorkspaceManager:
    """파일 기반 커뮤니케이션을 위한 워크스페이스 관리자.

    Sub-agent 결과를 JSON 파일로 저장하고, 파일 경로를 통해 접근합니다.
    이를 통해 LLM 컨텍스트 윈도우에 전체 결과를 넣지 않고도
    필요할 때만 파일을 읽어 참조할 수 있습니다.

    Attributes:
        workspace_dir: 워크스페이스 디렉터리 경로
    """

    workspace_dir: Path

    def __init__(self, workspace_dir: str | Path | None = None) -> None:
        """WorkspaceManager를 초기화합니다.

        Args:
            workspace_dir: 워크스페이스 디렉터리 경로.
                None이면 ./workspace_{uuid_short}/ 자동 생성.
        """
        if workspace_dir is None:
            short_id = uuid.uuid4().hex[:8]
            self.workspace_dir = Path(f"./workspace_{short_id}")
        else:
            self.workspace_dir = Path(workspace_dir)

        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, filename: str, data: dict | list) -> Path:
        """JSON 데이터를 파일로 저장합니다.

        Args:
            filename: 저장할 파일 이름 (예: "outline.json")
            data: 저장할 데이터 (dict 또는 list)

        Returns:
            저장된 파일의 절대 경로
        """
        filepath = self.workspace_dir / filename
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return filepath.resolve()

    def read_json(self, filepath: str | Path) -> dict | list:
        """JSON 파일을 읽어 반환합니다.

        Args:
            filepath: 읽을 파일 경로 (절대 또는 상대 경로)

        Returns:
            파일 내용 (dict 또는 list)

        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        path = Path(filepath)
        content = path.read_text(encoding="utf-8")
        return json.loads(content)

    def list_files(self) -> list[Path]:
        """워크스페이스 내 파일 목록을 반환합니다.

        Returns:
            워크스페이스 디렉터리 내의 파일 경로 리스트
        """
        return sorted(self.workspace_dir.iterdir())
