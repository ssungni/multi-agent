# Photo Editor — 요구사항 정의서

Reve.com의 "Edit" 기능을 참고한 AI 기반 이미지 레이어 편집기.
이미지를 업로드하면 AI가 객체별로 레이어(Instance Segmentation)를 분리하고,
사용자는 레이어를 선택/변형하거나 채팅으로 편집을 지시할 수 있다.

---

## 1. 첫 화면 (Landing / Create)

- 좌측: 큰 캔버스 영역. 초기 상태에는 배경색만 있고 중앙에
  업로드 아이콘 + "Upload and edit" 안내 문구만 표시.
- 캔버스 우상단에 "Upload" 버튼.
- 우측 사이드바:
  - 상단에 "Create" 타이틀, 우측에 설정 아이콘 + "Chat ▾" 모드 드롭다운.
  - 날짜 표시 (예: "July 15, 2026").
  - 안내 문구: "Create by describing what you want to generate or upload
    your own photo to edit. Where do you want to start?"
  - 하단 고정 채팅 입력창 "Ask Reve":
    - placeholder 텍스트
    - 좌측 아이콘: 첨부(클립), 멘션(@), 스타일/컬러(그라디언트 원)
    - 우측: 전송 버튼(원형 화살표)

## 2. 이미지 업로드 → 레이어 분할

- 이미지를 업로드하면 캔버스에 표시되고, 상단에 브레드크럼
  (`프로젝트명 / 앨범명 / 파일명`)과 `...` 메뉴, 실행취소/다시실행,
  다운로드 아이콘이 나타난다.
- 우측 사이드바가 "Create | Edit" 두 개의 탭으로 전환되고 "Edit" 탭이 활성화.
- "Reference image" 드롭다운(예: "Literal ▾").
- 업로드된 이미지 아래에 자동으로 분리된 레이어 트리가 표시된다.
  예: `Uploaded image` → `lion`(하위에 추가 분해 가능, `>` 화살표) →
  `body`, `background` 등 계층형 리스트, 각 항목에 썸네일 표시.
- 캔버스 하단 중앙에 도구 툴바(아이콘 7종, 5번 항목 참고)가 항상 노출.

## 3. Instance Segmentation + Bounding Box 선택

- AI가 업로드 이미지를 객체 단위 레이어로 자동 분리(사람/동물/배경 등).
- 사이드바 레이어 리스트에서 레이어를 클릭하면:
  - 해당 레이어가 리스트에서 하이라이트(파란 배경) 처리.
  - 캔버스 위 해당 객체 영역에 **Bounding Box(Transform Box)** 표시:
    - 4개 모서리 핸들(리사이즈용 사각형 점)
    - 박스 테두리 라인
    - 인접/하위 레이어 이름 라벨이 박스 모서리 근처에 툴팁처럼 표시
    - 박스 하단에 "Edit" 버튼 노출 → 해당 레이어만 별도로 편집 진입.
  - 레이어 리스트 항목에 마우스를 올리면 다운로드/삭제 등 보조 아이콘 노출.

## 4. 우측 사이드바 Chat 박스

- 화면 우측 하단에 항상 고정된 채팅 입력창("Ask Reve").
- 사용자가 자연어로 요구사항을 입력하면(예: "갈귀가 초록색이 되게 변경해줘")
  현재 선택된 레이어/이미지에 대한 편집 명령으로 처리된다.
- 채팅 입력은 이미지가 없는 초기 상태(1번)에서도, 이미지/레이어를 선택한
  편집 상태(3번)에서도 동일한 위치에 유지된다.

## 5. 더 나아가기 — 하단 도구 툴바 (7종)

캔버스 하단 중앙에 고정된 툴바. 각 도구를 누르면 해당 기능의 보조 옵션이
툴바 위쪽에 별도 행으로 나타난다.

1. **Select objects** — 포인터 도구. Bounding Box를 클릭해 레이어를 선택.
2. **Spotlight** — 점선 사각형(마키) 도구. 원하는 영역을 드래그로 사각 선택.
3. **Draw** — 자유 드로잉 도구.
   - 선택 시 보조 툴바에 펜/지우개 아이콘 2종이 나타남.
   - 굵기 조절 슬라이더.
   - 색상 선택용 컬러 스와치(그라디언트 원 클릭 → 색상 피커).
4. **Add objects** — 프롬프트로 원하는 위치에 새로운 객체를 생성해 배치.
5. **Text** — 캔버스에 텍스트 레이어 추가(입력 시 "Text" placeholder 표시,
   폰트/크기 등은 추후 옵션으로 확장 가능).
6. **Add image** — 로컬 폴더의 이미지 파일을 업로드해 캔버스에 추가.
7. **Add effects** — 프리셋 효과 패널.
   - 우측 사이드바 전체를 덮는 패널로 전환, 헤더에 "Add effect" + 닫기(X).
   - 상단 탭: **All / Saved / Textures / Light / Color**.
   - **All 탭**: 상단에 "Adjust"(슬라이더 아이콘), "Create"(+ 아이콘) 카드,
     이어서 Textures / Light / Color 섹션이 각각 "See all" 링크와 함께
     가로 스크롤 행(3~6개 미리보기 + `>` 화살표로 더 보기)으로 요약 표시.
   - **Textures 탭**: 전체 프리셋을 3열 그리드로 표시.
     예: CMYK Halftone, Grain, Dither, Texture Overlay, Stippling,
     Retro Handhold, Engraving, Risograph, Engraving Pass, Halftone
     Texture, Color Tile, Geomosaic.
   - **Light 탭**: 3열 그리드. 예: Vignette, Zoom Blur, Halation, Light
     Leak, Motion Blur, Spin Blur, Faceted Glass, Frosted Glass, Glow,
     Star Highlight, Sun Rays, Tilt Shift, Chromatic Aberration, Heat
     Distortion, Lens Flare, Bokeh.
   - **Color 탭**: 3열 그리드. 예: Deep Cine 2, Neon Day, Neon Night, Neon
     Port, Sand Cine 3, Duotone, Clean Land, Vivid Land 1, Vivid Land 2,
     Vivid Port, Warm Port, Grit Mono, Low Light, Punch Day, Quiet Port,
     Soft Day, Soft Port, Story Mono.
   - 각 프리셋은 현재 이미지에 효과를 적용한 실시간 썸네일 미리보기로 표시.
   - 패널 하단에 "Cancel" / "Done" 버튼.

## 참고 스크린샷 대응표

| 화면 | 설명 |
|---|---|
| Image #1 | 첫 화면 (업로드 전) |
| Image #3 | 이미지 업로드 후 레이어 트리 (uploaded image / lion / body / background) |
| Image #4 | 레이어 선택 시 Bounding Box + Edit 버튼 + 챗 입력 예시 |
| Image #5, #6 | Draw 도구 보조 옵션 (펜/지우개, 굵기 슬라이더, 색상) |
| Image #7 | Add effect 패널 - All 탭 (요약 가로 스크롤) |
| Image #8 | Add effect 패널 - Textures 탭 (전체 그리드) |
| Image #9 | Add effect 패널 - Light 탭 (전체 그리드) |
| Image #10 | Add effect 패널 - Color 탭 (전체 그리드) |

## 범위 밖 (이번 문서에서 다루지 않음)

- 실제 Instance Segmentation 모델/API 선정 및 연동 방식
- 기술 스택(프론트/백엔드) 및 아키텍처 설계
- 위 항목들은 별도 설계 단계에서 논의.
