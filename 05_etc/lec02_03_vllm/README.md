# lec02_03_vllm — 폐쇄망 오픈소스 LLM 서빙

> vLLM으로 폐쇄망 환경에서 오픈소스 LLM을 OpenAI 호환 API로 서빙합니다.

폐쇄망 환경에서 Llama, Mistral, Qwen 등 오픈소스 LLM을 빠르게 서빙하기 위한 vLLM 사용 방법을 설명합니다.

## 핵심 개념

### 왜 필요한가
보안 규정상 외부 API를 사용할 수 없는 폐쇄망 환경에서도 LLM을 사용해야 합니다.

### 무엇을 배우는가
vLLM을 사용하여 Llama, Mistral 등 오픈소스 LLM을 **OpenAI 호환 API**로 서빙하고, LiteLLM Router와 연동하는 방법을 학습합니다.

### 어떻게 동작하는가
1. `vllm serve model-name --port 8000`으로 서버 실행
2. OpenAI SDK 또는 LiteLLM Router로 동일한 방식으로 호출
3. Structured Output, Tool Calling 등 고급 기능 지원

## 주요 키워드

- vLLM
- On-premise deployment
- Open-source LLM
- Model serving

## vLLM 소개

vLLM은 LLM 추론을 위한 고성능 서빙 엔진입니다. PagedAttention 기술을 통해 메모리 효율성을 극대화하고, continuous batching으로 높은 처리량을 달성합니다.

주요 기능:
- **OpenAI 호환 API 서버** 내장
- **Structured Output** (JSON Schema, Regex 등) 지원
- **Tool Calling** 지원 (`tool_choice`: `auto`, `required`, `none`, named function)
- **Multi-GPU** 지원 (Tensor Parallelism, Pipeline Parallelism)
- **LoRA 어댑터** 동적 로딩
- **YAML config** 파일을 통한 설정 관리

## 설치

```bash
pip install vllm
```

## 기본 사용법

`vllm serve` 명령어로 OpenAI 호환 API 서버를 실행합니다.

```bash
# 기본 실행
vllm serve meta-llama/Llama-3.1-8B-Instruct --port 8000

# GPU 메모리 활용률 및 최대 컨텍스트 길이 설정
vllm serve meta-llama/Llama-3.1-8B-Instruct \
    --port 8000 \
    --gpu-memory-utilization 0.9 \
    --max-model-len 4096

# 멀티 GPU (Tensor Parallelism)
vllm serve meta-llama/Llama-3.1-70B-Instruct \
    --port 8000 \
    --tensor-parallel-size 4
```

### 주요 서버 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--port` | 서버 포트 | 8000 |
| `--tensor-parallel-size` | GPU 분산 수 | 1 |
| `--gpu-memory-utilization` | GPU 메모리 활용 비율 (0.0~1.0) | 0.9 |
| `--max-model-len` | 최대 컨텍스트 길이 (토큰) | 모델 기본값 |
| `--served-model-name` | API에서 사용할 모델 이름 | `--model` 값 |
| `--api-key` | API 인증 키 | 없음 |
| `--dtype` | 모델 가중치 타입 (`float16`, `bfloat16`, `auto`) | auto |
| `--tool-call-parser` | Tool calling 파서 (모델에 따라 선택) | 없음 |

도움말 확인:

```bash
vllm serve --help=listgroup    # 모든 옵션 그룹 목록
vllm serve --help=ModelConfig   # 특정 그룹 상세 보기
vllm serve --help=max           # 키워드로 옵션 검색
```

### YAML Config 파일

CLI 인자를 YAML 파일로 관리할 수 있습니다. CLI 인자가 config 파일보다 우선합니다.

```yaml
# config.yaml
model: meta-llama/Llama-3.1-8B-Instruct
host: "0.0.0.0"
port: 8000
gpu-memory-utilization: 0.9
max-model-len: 4096
uvicorn-log-level: "info"
```

```bash
vllm serve --config config.yaml
```

## 폐쇄망 (Air-Gapped) 배포

### 로컬 모델 경로로 서빙

인터넷이 되는 환경에서 모델을 먼저 다운로드한 후, 폐쇄망으로 전송합니다.

```bash
# 1. 인터넷 환경에서 모델 다운로드
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct \
    --local-dir ./llama3-8b-instruct

# 2. 폐쇄망으로 모델 파일 전송 후, 로컬 경로로 서빙
vllm serve ./llama3-8b-instruct --port 8000
```

### Docker 배포

```bash
docker run --runtime nvidia --gpus all \
    -v /path/to/models:/models \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model /models/llama3-8b-instruct
```

## LiteLLM과 연동

```python
# router.py에서 vLLM 엔드포인트 추가
model_list = [
    {
        "model_name": "llama-3.1-8b",
        "litellm_params": {
            "model": "openai/meta-llama/Llama-3.1-8B-Instruct",
            "api_base": "http://localhost:8000/v1",
            "api_key": "dummy",  # vLLM은 API 키 불필요
        },
    },
]
```

## 참고 자료

- [vLLM 공식 문서](https://docs.vllm.ai/)
- [vLLM GitHub](https://github.com/vllm-project/vllm)
- [vLLM CLI Reference](https://docs.vllm.ai/en/latest/cli/)
- [vLLM Server Arguments](https://docs.vllm.ai/en/latest/configuration/serve_args/)
- [vLLM Docker 배포 가이드](https://docs.vllm.ai/en/stable/deployment/docker/)
- [vLLM Structured Outputs](https://docs.vllm.ai/en/latest/features/structured_outputs/)
- [vLLM Tool Calling](https://docs.vllm.ai/en/latest/features/tool_calling/)

## 강의 네비게이션

```
← lec02_02_langfuse │ 현재: lec02_03_vllm │ 다음: lec02_04_streamlit →
```

**이전 강의**: [lec02_02_langfuse](../lec02_02_langfuse/README.md) - Langfuse Observability

**이 강의**: vLLM 폐쇄망 LLM 서빙 (참고용 README - 실행 코드 없음)

**다음 강의**: [lec02_04_streamlit](../lec02_04_streamlit/README.md) - Streamlit 기반 LiteLLM 채팅 UI
