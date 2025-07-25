# 🧠 NLI 기반 문장 자기모순 및 할루시네이션 평가 개념

## 개요

이 문서는 Natural Language Inference (NLI) 모델을 활용하여 **모델이 생성한 문장 중 할루시네이션이 발생했을 가능성이 있는 문장**을 식별하는 개념 및 평가 방식에 대해 설명한다. 평가의 핵심은 **"문장 간 의미적 모순(contradiction)"** 을 NLI 모델로 판단하는 것이다.

---

## 1. 평가 목적

- **문장 단위로 생성된 결과물이 사실 기반 문장들과 논리적으로 충돌하는지 여부**를 정량화한다.
    
- 충돌(모순)이 감지된 문장은 **할루시네이션 가능성이 높다**고 판단한다.
    
- 평가 결과는 문장마다 **[0, 1] 사이의 contradiction 확률 값**으로 표현된다.
    

---

## 2. 주요 개념

### 🔹 sentences (문장 리스트)

- 모델이 생성한 응답을 문장 단위로 분할한 리스트
    
- **검사 대상 문장(hypothesis)**으로 사용됨
    
- 예시:
    
    ```python
    sentences = [
        "Nikola Tesla was a Serbian-American inventor.",
        "He hated electricity.",
    ]
    ```
    

### 🔹 sampled_passages (샘플 문단들)

- 동일한 질문에 대해 생성된 다른 모델 응답, 또는 신뢰할 수 있는 정답 문단들
    
- **기준 문단(premise)**으로 사용됨
    
- 예시:
    
    ```python
    sampled_passages = [
        "Tesla was a pioneer in electrical engineering who believed electricity would change the world.",
        "He advocated for alternating current and worked to popularize it.",
    ]
    ```
    

---

## 3. 평가 방식

1. 각 `sentence`에 대해 `sampled_passages`의 각 항목과 NLI 모델을 사용해 **문장 쌍 비교**를 수행한다.
    
2. NLI 모델은 각 문장 쌍에 대해 다음 세 가지 클래스를 예측한다:
    
    - entailment (함의)
        
    - contradiction (모순)
        
    - neutral (중립)
        
3. 최종 점수는 **contradiction / (contradiction + entailment)** 로 정규화된다.
    
    - neutral은 무시하고, contradiction 대 entailment만 고려
        
    - 즉, "모순인가 vs. 일관적인가"만 본다
        

---

## 4. 출력값

- `sent_scores: list[float]`
    
    - 각 문장에 대한 모순 확률 값
        
    - 예: `[0.05, 0.92]` → 첫 문장은 모순 거의 없음, 두 번째 문장은 강한 모순 가능성
        

---

## 5. 예시 흐름

```python
from transformers import pipeline

nli = pipeline("text-classification", model="facebook/bart-large-mnli")

sentences = ["Tesla hated electricity."]
sampled_passages = ["Tesla believed electricity would change the world."]

def contradiction_score(sentence, passage):
    output = nli(f"{passage} </s> {sentence}")
    prob = {o['label'].lower(): o['score'] for o in output}
    contradiction = prob.get("contradiction", 0.0)
    entailment = prob.get("entailment", 0.0)
    if contradiction + entailment == 0:
        return 0.0
    return contradiction / (contradiction + entailment)

# 결과: 0.92
```

---

## 6. 활용 예시

- 문장별 할루시네이션 점수 기반 필터링
    
- 모델 디버깅: 자기모순 문장 탐지
    
- 생성된 요약문, 설명문 등의 신뢰도 스코어링
    

---

## 7. 주의사항

- sampled_passages의 품질에 따라 평가 정확도가 달라질 수 있음
    
- NLI 모델의 bias 또는 generalization 한계 주의
    
- 문장이 길거나 문맥이 복잡한 경우, 문장 분리 및 전처리 중요
    
