// getByteTimeDomainData는 128을 무음 기준선으로 사용한다 — 이 값에서 가장 크게
// 벗어난 정도를 발화 감지(useAutoStopOnSilence, useSpeechWhileMuted)의 공통 척도로 쓴다.
export function maxAmplitudeDeviation(dataArray: Uint8Array): number {
  let maxDeviation = 0
  for (let i = 0; i < dataArray.length; i++) {
    maxDeviation = Math.max(maxDeviation, Math.abs(dataArray[i]! - 128))
  }
  return maxDeviation
}
